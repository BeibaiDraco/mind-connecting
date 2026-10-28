"""V7 engineering-only production relocation checks and timing.

No ownership readouts are collected here. The small runner exercise collects CAP0
only and never scores choices. Pilot collection is a separate, conditional step.
"""
from __future__ import annotations

import argparse
import gc
import json
import math
import time
from pathlib import Path
from typing import Any

import yaml

from mb import chat, ledger, run, tasks, v7_run
from mb import v7_relocation as relocation
from mb.model_profiles import QWEN

APPROVED_SHA = "608350de020b9392672142916484afc953e846344fe733f00e0b3c3f27479e09"
BATCHES = (1, 4, 8, 12)
SAVED_HASHES = {
    "saved_inputs.json": "a1526e1d9516d6427a5ed037aa14e62e77ce127c9ad4afa8c176427aa045d566",
    "notes.jsonl": "b65956e6562cceda1cc4f4034e7faad0a980e8bc3482cbeaeab22effe9ac681d",
    "bf16_baseline.json": "b79e6700a00f916f3fd7b609d282f76c24caf3bbba5026a2cdf9ef16e3686172",
    "bf16_comparison.json": "1ca40d9bdd4a2c8d9d8abdb23a6740b7d618eb9239f1c367a0f53553e8ccfd71",
}
RECIPE = {
    "version": "v7-production-relocation-v2", "episodes": 12, "split": "v7_dev", "seed": 0,
    "batches": list(BATCHES), "saved_files": SAVED_HASHES,
    "comparison": "production KV-P w2 all layers, before_own on native B versus native read on real offset B",
    "reference": "clone the same native A state; replace only donor state with a real [-L_B, 0) prefill",
    "gate": "all A-row logits and own/donor span masses, all layers/heads, eight teacher-forced ticks, FP32",
    "logit_atol": relocation.LOGIT_ATOL, "logit_rtol": relocation.LOGIT_RTOL,
    "mass_atol": relocation.MASS_ATOL, "mass_rtol": 0.0, "bf16_is_gate": False,
    "bf16": "same production comparison plus native joint-read padding variability; descriptive only",
    "timing": "8 teacher-forced neutral tokens per arm/batch; first 2 warmup ticks excluded",
    "selection": "after CAP0 passes, minimum translated/logged seconds per episode-token; ties prefer smaller batch",
    "runner_exercise": "12 saved dev episodes, all 14 base arms, CAP0 only at fixed maximum candidate batch 12",
}


def validated_saved_inputs(root: Path) -> tuple[dict, dict[str, str]]:
    for name, sha in SAVED_HASHES.items():
        if ledger.file_sha256(root / name) != sha:
            raise ValueError(f"saved input/evidence hash mismatch: {name}")
    data = relocation.read_saved_inputs(root / "saved_inputs.json", SAVED_HASHES["saved_inputs.json"])
    return data, dict(SAVED_HASHES)


def validate_material_compatibility(tok, data: dict, notes_path: Path) -> None:
    adapter = v7_run.V7Runner.__new__(v7_run.V7Runner)
    adapter.cfg = v7_run.V7Config("v7_dev", "base", 12)
    adapter.tok = tok
    adapter.notes = {row["key"]: row["ids"] for row in v7_run._check_notes(notes_path)}
    _, episodes = adapter._stage_episodes(None)
    adapter.active_arm = next(a for a in adapter.cfg.arm_configs() if a.arm_id == "orig_w2")
    adapter._input_cache, adapter._prefix_cache, adapter._bank_cache = {}, {}, {}
    parts = [adapter._prefix_parts(ep, role) for ep in episodes for role in tasks.ROLES]
    reconstructed = {"episodes": [ep.episode_id for ep in episodes],
                     "prefix_ids": [x[0] for x in parts], "attention_spans": [x[1] for x in parts]}
    if json.loads(json.dumps(reconstructed)) != data:
        raise ValueError("current materials or span declarations differ from saved engineering inputs")


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


def benchmark(engine, prefixes: list[list[int]], spans: list[list[tuple]], root: Path) -> list[dict]:
    import torch
    from mb.conditions import ArmConfig
    from mb.runtime import make_plan

    rows = []
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
            print(json.dumps({"event": "timing", **row}), flush=True)
    write_once(root / "timing_measurements.json", {"measurements": rows, "batch_selection_pending": True})
    return rows


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
    parser.add_argument("--saved-input-dir", type=Path, required=True)
    parser.add_argument("--approved-protocol-sha256", required=True)
    args = parser.parse_args(argv)
    cfg = v7_run.V7Config("v7_dev", "base", 12)
    v7_run.validate_launch(cfg, args.output / "engineering.yaml", args.approved_protocol_sha256, None)
    if args.approved_protocol_sha256 != APPROVED_SHA:
        raise ValueError("acceptance receipt differs from the bounded PI approval")
    data, hashes = validated_saved_inputs(args.saved_input_dir)
    args.output.mkdir(parents=True, exist_ok=False)
    for name in hashes:
        with (args.output / name).open("xb") as stream:
            stream.write((args.saved_input_dir / name).read_bytes())
    write_once(args.output / "recipe.json", {**RECIPE, "source_hash": run.source_hash(),
               "protocol_sha256": APPROVED_SHA, "git": run.git_state()})
    phase, started, durations = "fp32_model_load", time.perf_counter(), {}
    model = engine = None
    try:
        import torch
        from mb.runtime import load_model

        if not torch.cuda.is_available():
            raise RuntimeError("V7 acceptance requires the authorized GPU")
        torch.set_num_threads(8)
        tok = chat.load_tokenizer(profile=QWEN.key)
        if hashes:
            validate_material_compatibility(tok, data, args.output / "notes.jsonl")
        prefixes, spans = data["prefix_ids"], data["attention_spans"]
        token = chat.encode(tok, "Continue")[0]
        engine_cls = timed_engine_class(args.output / "steps.jsonl")
        model = load_model(dtype=torch.float32, profile=QWEN.key, tokenizer=tok)
        engine = engine_cls(model, tok, 18, None)
        durations[phase] = time.perf_counter() - started
        phase, started = "fp32_relocation", time.perf_counter()
        with torch.inference_mode():
            gate = relocation.run_comparison(engine, prefixes, spans, args.output,
                                             precision="fp32", token=token, batches=BATCHES)
        durations[phase] = time.perf_counter() - started
        if not gate["passed"]:
            raise RuntimeError("FP32 production relocation equivalence failed")
        engine.close()
        engine = model = None
        gc.collect()
        torch.cuda.empty_cache()
        phase, started = "bf16_model_load", time.perf_counter()
        model = load_model(dtype=torch.bfloat16, profile=QWEN.key, tokenizer=tok)
        engine = engine_cls(model, tok, 18, None)
        durations[phase] = time.perf_counter() - started
        phase, started = "bf16_descriptive", time.perf_counter()
        with torch.inference_mode():
            relocation.run_comparison(engine, prefixes, spans, args.output,
                                      precision="bf16", token=token, batches=BATCHES)
        durations[phase] = time.perf_counter() - started
        phase, started = "timing", time.perf_counter()
        with torch.inference_mode():
            measurements = benchmark(engine, prefixes, spans, args.output)
        durations[phase] = time.perf_counter() - started
        engine.close()
        engine = None
        phase, started = "engineering_collection", time.perf_counter()
        result = engineering_run(args.output, engine_cls, model, tok, max(BATCHES))
        durations[phase] = time.perf_counter() - started
        if not result["passed"]:
            raise RuntimeError("engineering collection incomplete or failed")
        phase, started = "batch_selection", time.perf_counter()
        batch = choose_batch([row for row in measurements if row["mode"] == "translated"])
        write_once(args.output / "timing_selection.json", {"measurements": measurements,
            "selected_episodes_per_batch": batch, "selected_max_rows": 2 * batch,
            "cap0_passed_before_selection": True, "cap0_batch": max(BATCHES), "recipe": RECIPE["selection"]})
        pilot = v7_run.V7Config("v7_pilot", "base", 80, tag="approved", episodes_per_batch=batch, max_rows=2 * batch)
        (args.output / "pilot.yaml").write_text(yaml.safe_dump(pilot.resolved()))
        durations[phase] = time.perf_counter() - started
        write_once(args.output / "acceptance.json", {"passed": True, "durations_seconds": durations,
            "source_hash": run.source_hash(), "protocol_sha256": APPROVED_SHA,
            "fp32_relocation_passed": True, "bf16_is_gate": False, "saved_file_hashes": hashes,
            "selected_batch": batch, "pilot_config_sha256": ledger.file_sha256(args.output / "pilot.yaml")})
        print(json.dumps({"event": "acceptance", "passed": True, "selected_batch": batch}), flush=True)
        return 0
    except Exception as exc:
        durations[phase] = time.perf_counter() - started
        write_once(args.output / "acceptance.json", {"passed": False, "failed_phase": phase,
            "reason": str(exc), "durations_seconds": durations, "source_hash": run.source_hash(),
            "protocol_sha256": APPROVED_SHA, "pilot_dispatched": False, "bf16_is_gate": False})
        print(json.dumps({"event": "acceptance", "passed": False, "phase": phase, "reason": str(exc)}), flush=True)
        return 1
    finally:
        if engine is not None:
            engine.close()


if __name__ == "__main__":
    raise SystemExit(main())
