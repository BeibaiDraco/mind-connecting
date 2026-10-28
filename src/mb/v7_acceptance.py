"""V7 engineering-only checkpoint checks, timing and BF16 calibration.

No ownership readouts are collected here. The small runner exercise collects CAP0
only and never scores choices. Pilot collection is a separate, conditional step.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import math
import time
from pathlib import Path
from typing import Any

import yaml

from mb import chat, ledger, run, tasks, v7_run
from mb.model_profiles import QWEN

APPROVED_SHA = "39c607bb5a51cdc480c6dee6780fb74970b1a2a2678b231029510888770768c0"
BATCHES = (1, 4, 8, 12)
METRICS = tuple(f"{kind}_{stat}" for kind in ("key", "value", "logit") for stat in ("max_abs", "rms"))
RECIPE = {
    "version": "v7-bf16-batch-envelope-v1", "episodes": 12, "split": "v7_dev", "seed": 0,
    "batches": list(BATCHES), "reference": "native one episode per batch, identical saved P inputs",
    "baseline": "maximum observed native batch-composition error per metric over all rows and layers",
    "comparison": "fp32 R(-L) of native BF16 keys versus actual BF16 offset prefill at the same batch size",
    "limits": "each comparison error must be <= its measured baseline envelope; no multiplier or fixed floor",
    "metrics": list(METRICS), "decision": "all metrics finite and within envelope; otherwise stop before pilot",
    "timing": "8 teacher-forced neutral tokens per arm/batch; first 2 warmup ticks excluded from selection",
    "selection": "minimum translated/logged total measured seconds per episode-token; ties prefer smaller batch",
    "runner_exercise": "12 dev episodes, all 14 base arms, CAP0 only, no choice scoring",
}


def envelope(rows: list[dict[str, float]]) -> dict[str, float]:
    if not rows or any(not math.isfinite(row[k]) or row[k] < 0 for row in rows for k in METRICS):
        raise ValueError("baseline errors must be finite, nonnegative and nonempty")
    return {k: max(row[k] for row in rows) for k in METRICS}


def within_envelope(rows: list[dict[str, float]], limits: dict[str, float]) -> bool:
    return bool(rows) and all(math.isfinite(limits[k]) and limits[k] >= 0
                             and math.isfinite(row[k]) and 0 <= row[k] <= limits[k]
                             for row in rows for k in METRICS)


def choose_batch(rows: list[dict[str, Any]]) -> int:
    if len(rows) != len(BATCHES) or {row["batch"] for row in rows} != set(BATCHES):
        raise ValueError("all declared batch candidates must be measured")
    if any(not row["passed"] or not math.isfinite(row["seconds_per_episode_token"])
           or row["seconds_per_episode_token"] <= 0 for row in rows):
        raise ValueError("failed or invalid engineering timing; no batch selected")
    return min(rows, key=lambda row: (row["seconds_per_episode_token"], row["batch"]))["batch"]


def write_once(path: Path, value: Any) -> None:
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def timed_engine_class(path: Path):
    import torch
    from mb.runtime import Engine

    class TimedEngine(Engine):
        tag = "unspecified"

        def _kv_geometry_begin(self, state, kv):
            torch.cuda.synchronize()
            start = time.perf_counter()
            super()._kv_geometry_begin(state, kv)
            torch.cuda.synchronize()
            self.geometry_seconds = time.perf_counter() - start

        def step(self, state, tokens, injection, kv=None):
            torch.cuda.synchronize()
            start = time.perf_counter()
            self.geometry_seconds = 0.0
            output = super().step(state, tokens, injection, kv)
            torch.cuda.synchronize()
            self.last_step_seconds = time.perf_counter() - start
            with path.open("a") as stream:
                stream.write(json.dumps({"tag": self.tag, "phase": state.phase, "tick": state.tick,
                    "rows": state.rows, "columns": state.attn.shape[1], "wall_seconds": self.last_step_seconds,
                    "geometry_seconds": self.geometry_seconds, "kv": kv is not None}) + "\n")
            return output

    return TimedEngine


def capture(state) -> list[dict]:
    from mb.runtime import cache_layers

    result = []
    for row, length in enumerate(state.attn.sum(-1).tolist()):
        result.append({"key": [k[row, :, -length:].float().cpu() for k, _ in cache_layers(state.cache)],
                       "value": [v[row, :, -length:].float().cpu() for _, v in cache_layers(state.cache)],
                       "logit": [state.logits[row].float().cpu()]})
    return result


def errors(expected: dict, actual: dict) -> dict[str, float]:
    result = {}
    for kind in ("key", "value", "logit"):
        differences = [(a - b).float() for a, b in zip(expected[kind], actual[kind], strict=True)]
        result[kind + "_max_abs"] = max(float(d.abs().max()) for d in differences)
        result[kind + "_rms"] = max(float(d.square().mean().sqrt()) for d in differences)
    return result


def offset_prefill(engine, prefixes: list[list[int]]):
    import torch
    from transformers import DynamicCache

    width = max(map(len, prefixes))
    ids = torch.full((len(prefixes), width), engine.pad_id, device=engine.device, dtype=torch.long)
    attn = torch.zeros_like(ids)
    for row, tokens in enumerate(prefixes):
        ids[row, -len(tokens):] = torch.tensor(tokens, device=engine.device)
        attn[row, -len(tokens):] = 1
    positions = (attn.cumsum(-1) - 1).clamp(min=0) - attn.sum(-1)[:, None]
    cache = DynamicCache(config=engine.model.config)
    engine.hook.mode = "prefill"
    try:
        output = engine.model.model(input_ids=ids, attention_mask=attn, position_ids=positions,
                                    past_key_values=cache, use_cache=True)
    finally:
        engine.hook.mode = "tick"
    from types import SimpleNamespace
    return SimpleNamespace(cache=cache, attn=attn, logits=engine._lm_logits(output.last_hidden_state[:, -1]))


def bf16_check(engine, prefixes: list[list[int]], root: Path) -> bool:
    import torch
    from mb.kv_geometry import rephase_keys

    references = []
    for start in range(0, len(prefixes), 2):
        state = engine.prefill(prefixes[start:start + 2])
        references.extend(capture(state))
        del state
    torch.save(references, root / "native_reference.pt")
    baseline = []
    for batch in BATCHES:
        for start in range(0, len(prefixes), 2 * batch):
            state = engine.prefill(prefixes[start:start + 2 * batch])
            for index, actual in enumerate(capture(state)):
                baseline.append({"batch": batch, "row": start + index,
                                 **errors(references[start + index], actual)})
            del state
    limits = envelope(baseline)
    # This file is committed to disk before any offset-prefill errors are computed.
    write_once(root / "bf16_baseline.json", {"recipe": RECIPE, "limits": limits, "rows": baseline})
    freq, pairing, _ = engine._rotary_spec()
    freq = freq.cpu()
    compared = []
    for batch in BATCHES:
        for start in range(0, len(prefixes), 2 * batch):
            sequences = prefixes[start:start + 2 * batch]
            native = engine.prefill(sequences)
            expected_rows = capture(native)
            del native
            shifted = offset_prefill(engine, sequences)
            actual_rows = capture(shifted)
            del shifted
            for index, (expected, actual) in enumerate(zip(expected_rows, actual_rows)):
                length = len(sequences[index])
                expected["key"] = [rephase_keys(key[None, :, None], torch.tensor([-length]),
                    torch.ones((1, length), dtype=torch.bool), freq, pairing)[0, :, 0] for key in expected["key"]]
                compared.append({"batch": batch, "row": start + index, **errors(expected, actual)})
    passed = within_envelope(compared, limits)
    write_once(root / "bf16_comparison.json", {"passed": passed, "limits": limits,
                "observed": envelope(compared), "rows": compared})
    return passed


def benchmark(engine, prefixes: list[list[int]], spans: list[list[tuple]], root: Path) -> int:
    import torch
    from mb.conditions import ArmConfig
    from mb.runtime import make_plan

    rows, selected = [], []
    token = chat.encode(engine.tok, "Continue")[0]
    for batch in BATCHES:
        for mode in ("legacy", "logged", "translated"):
            arm = ArmConfig("ONE", interface="kv", kv_scope="P", gain=2.,
                            kv_log_spans=mode != "legacy", kv_position="before_own" if mode == "translated" else "native")
            elapsed, denominator = 0.0, 0
            for start in range(0, len(prefixes), 2 * batch):
                engine.tag = f"benchmark/{mode}/batch{batch}"
                state = engine.prefill(prefixes[start:start + 2 * batch], attention_spans=spans[start:start + 2 * batch])
                plan = make_plan(arm, ["A", "B"] * (state.rows // 2), [None] * state.rows,
                                 None, engine.device, d=engine.d)
                for tick in range(8):
                    logits, _, _ = engine.step(state, torch.full((state.rows,), token, device=engine.device), None, plan.kv)
                    if not bool(torch.isfinite(logits).all()):
                        raise RuntimeError("nonfinite engineering logits")
                    if mode != "legacy":
                        mass = engine.last_kv_span_mass[0::2]
                        banks = engine.last_kv_bank_mass[0::2]
                        if not bool(torch.isfinite(mass).all() and torch.isfinite(banks).all()):
                            raise RuntimeError("nonfinite active diagnostic mass")
                        torch.testing.assert_close(banks.sum(-1), torch.ones_like(banks[..., 0]))
                    if tick >= 2:
                        elapsed += engine.last_step_seconds
                        denominator += state.rows // 2
                del state
            row = {"mode": mode, "batch": batch, "seconds_per_episode_token": elapsed / denominator,
                   "measured_seconds": elapsed, "passed": True}
            rows.append(row)
            if mode == "translated":
                selected.append(row)
            print(json.dumps({"event": "timing", **row}), flush=True)
    batch = choose_batch(selected)
    write_once(root / "timing_selection.json", {"measurements": rows, "selected_episodes_per_batch": batch,
                "selected_max_rows": 2 * batch, "recipe": RECIPE["selection"]})
    return batch


def engineering_run(root: Path, engine_cls, model, tok, batch: int) -> dict:
    class EngineeringRunner(v7_run.V7Runner):
        def _pending_questions(self, *args):
            return [item for item in super()._pending_questions(*args) if item[2].qid == "CAP0"]

        def run_arm_chunk(self, engine, arm, *args, **kwargs):
            engine.tag = f"engineering/{arm.arm_id}"
            return super().run_arm_chunk(engine, arm, *args, **kwargs)

    cfg = v7_run.V7Config("v7_dev", "base", 12, tag="engineering", episodes_per_batch=batch, max_rows=2 * batch)
    config_path = root / "engineering.yaml"
    config_path.write_text(yaml.safe_dump(cfg.resolved()))
    prep = v7_run.prepare_run(cfg, config_path, tok=tok)
    with (prep.run_dir / "notes.jsonl").open("xb") as stream:
        stream.write((root / "notes.jsonl").read_bytes())
    collector = EngineeringRunner(cfg, prep.run_dir, None, prep.identity, {}, {}, lambda msg: print(msg, flush=True),
                                  model=model, tok=tok, engine_cls=engine_cls)
    try:
        collector.register_arms(cfg.arm_configs())
        # Acceptance failures are preserved and stop progression; no silent acceptance retry.
        collector.run_arms(cfg.arm_configs(), passes=1)
    finally:
        collector.close()
    records = ledger.load_records(prep.run_dir).records
    expected = [key for key in v7_run.expected_trials(cfg) if key[3] == "CAP0"]
    comp = ledger.completeness(records, expected, collector.arm_hash)
    passed = comp["status"] == "complete" and len(records) == len(expected) and all(
        record["status"] == "ok" and record["qid"] == "CAP0" for record in records)
    result = {"passed": passed, "run_dir": str(prep.run_dir), "engineering_qids": ["CAP0"],
              "outcomes_scored": False, "completeness": comp, "scientific_consumable": False}
    write_once(root / "engineering_collection.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--approved-protocol-sha256", required=True)
    args = parser.parse_args(argv)
    cfg = v7_run.V7Config("v7_dev", "base", 12)
    v7_run.validate_launch(cfg, args.output / "engineering.yaml", args.approved_protocol_sha256, None)
    if args.approved_protocol_sha256 != APPROVED_SHA:
        raise ValueError("acceptance receipt differs from the bounded PI approval")
    args.output.mkdir(parents=True, exist_ok=False)
    write_once(args.output / "recipe.json", {**RECIPE, "source_hash": run.source_hash(),
               "protocol_sha256": APPROVED_SHA, "git": run.git_state()})
    phase, started, passed = "model_load", time.perf_counter(), False
    durations = {}
    try:
        import torch
        from mb.runtime import load_model

        if not torch.cuda.is_available():
            raise RuntimeError("V7 acceptance requires the authorized GPU")
        torch.set_num_threads(8)
        tok = chat.load_tokenizer(profile=QWEN.key)
        model = load_model(dtype=torch.bfloat16, profile=QWEN.key, tokenizer=tok)
        durations[phase] = time.perf_counter() - started
        engine_cls = timed_engine_class(args.output / "steps.jsonl")
        engine = engine_cls(model, tok, 18, None)
        try:
            phase, started = "save_inputs", time.perf_counter()
            adapter = v7_run.V7Runner.__new__(v7_run.V7Runner)
            adapter.cfg, adapter.tok, adapter.run_dir, adapter.notes = cfg, tok, args.output, {}
            _, episodes = adapter._stage_episodes(None)
            adapter.active_arm = next(a for a in cfg.arm_configs() if a.arm_id == "orig_w2")
            adapter._input_cache, adapter._prefix_cache, adapter._bank_cache = {}, {}, {}
            engine.tag = "input_notes"
            adapter.ensure_notes(engine, [(ep, role) for ep in episodes for role in tasks.ROLES])
            parts = [adapter._prefix_parts(ep, role) for ep in episodes for role in tasks.ROLES]
            prefixes, spans = [p[0] for p in parts], [p[1] for p in parts]
            write_once(args.output / "saved_inputs.json", {"episodes": [ep.episode_id for ep in episodes],
                        "prefix_ids": prefixes, "attention_spans": spans})
            durations[phase] = time.perf_counter() - started
            phase, started = "bf16", time.perf_counter()
            with torch.inference_mode():
                passed = bf16_check(engine, prefixes, args.output)
            durations[phase] = time.perf_counter() - started
            if not passed:
                raise RuntimeError("BF16 comparison exceeds the measured native batch envelope")
            phase, started = "timing", time.perf_counter()
            with torch.inference_mode():
                batch = benchmark(engine, prefixes, spans, args.output)
            durations[phase] = time.perf_counter() - started
        finally:
            engine.close()
        phase, started = "engineering_collection", time.perf_counter()
        result = engineering_run(args.output, engine_cls, model, tok, batch)
        durations[phase] = time.perf_counter() - started
        if not result["passed"]:
            raise RuntimeError("engineering collection incomplete or failed")
        pilot = v7_run.V7Config("v7_pilot", "base", 80, tag="approved", episodes_per_batch=batch, max_rows=2 * batch)
        (args.output / "pilot.yaml").write_text(yaml.safe_dump(pilot.resolved()))
        write_once(args.output / "acceptance.json", {"passed": True, "durations_seconds": durations,
                   "source_hash": run.source_hash(), "protocol_sha256": APPROVED_SHA,
                   "selected_batch": batch, "pilot_config_sha256": ledger.file_sha256(args.output / "pilot.yaml")})
        print(json.dumps({"event": "acceptance", "passed": True, "selected_batch": batch}), flush=True)
        return 0
    except Exception as exc:
        durations[phase] = time.perf_counter() - started
        write_once(args.output / "acceptance.json", {"passed": False, "failed_phase": phase,
                    "reason": str(exc), "durations_seconds": durations, "source_hash": run.source_hash(),
                    "protocol_sha256": APPROVED_SHA, "pilot_dispatched": False})
        print(json.dumps({"event": "acceptance", "passed": False, "phase": phase, "reason": str(exc)}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
