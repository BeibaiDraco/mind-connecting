"""Explicit, read-only admission of the named post-validation Llama continuations.

Historical failures are never rewritten. Old collection identities are checked
against their original Git tree; new runs use the current frozen source identity.
The only exceptions are three specific observed capability drops, not new gates.
"""
from __future__ import annotations

import ast
import dataclasses
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Any, Mapping

from mb import chat, ledger, provenance_tasks, run, tasks, v4, v5_provenance as prov, v5_static as static
from mb.conditions import ArmConfig
from mb.model_profiles import LLAMA31

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

ROOT = Path(__file__).resolve().parents[2]
VERSION = "v5-continuation"
HISTORICAL_COMMIT = "ff2387d90035a110c37e4aeeb69e083543b16500"
HISTORICAL_FREEZE = "docs/protocol/FREEZE_protocol_v5_algorithm.json"
REMOTE_RESULTS = Path("/workspace/mb-data/results")
RUNS = {
    "base": "20261010-000737_v5_llama31_provenance_base_v5_llama31_provenance_base",
    "provenance_validity": "20261010-002651_v5_llama31_provenance_validity_v5_llama31_provenance_validity",
    "cal": "20261010-154140_calibrate_v5_static_cal",
    "match": "20261010-154353_v5_llama_static_match_v5_static_match",
    "static_validity": "20261010-164716_v5_llama_static_validity_v5_static_validity",
}
STUDY_RUNS = {"provenance": ("base", "provenance_validity"), "static": ("cal", "match", "static_validity")}
SELECTED = {"layer": 16, "gain": 0.5, "arm": "STATIC/L16/raw/g0.5/FULL"}
EXCEPTIONS = {"provenance": {"KV": .05625}, "static": {"K1": .0625, "CF": .059375}}


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def read(path: Path) -> Any:
    return json.loads(path.read_text())


def canonical(value: Any) -> Any:
    return json.loads(json.dumps(ledger.sanitize(value), allow_nan=False))


def local_path(value: str | Path, results_root: Path | None = None) -> Path:
    """Only the original results prefix is remapped; stored source bytes stay intact."""
    path = Path(value)
    if path.is_relative_to(REMOTE_RESULTS) and results_root is not None:
        return (results_root / path.relative_to(REMOTE_RESULTS)).resolve()
    return (path if path.is_absolute() else ROOT / path).resolve()


def check_pin(pin: Mapping[str, str], results_root: Path | None = None) -> Path:
    require(set(pin) == {"path", "sha256"}, "source pin must contain exactly path and sha256")
    path = local_path(pin["path"], results_root)
    require(path.is_file() and ledger.file_sha256(path) == pin["sha256"], f"source changed or missing: {path.name}")
    return path


def git_blob(name: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{HISTORICAL_COMMIT}:{name}"], cwd=ROOT,
                                   stderr=subprocess.DEVNULL)


def historical_code() -> dict:
    """Verify the actual old tree and its freeze, without importing old code."""
    frozen_bytes = git_blob(HISTORICAL_FREEZE)
    require((ROOT / HISTORICAL_FREEZE).read_bytes() == frozen_bytes, "original algorithm freeze changed")
    doc = json.loads(frozen_bytes)
    require(doc.get("protocol") == "v5" and doc.get("kind") == "algorithm", "invalid historical freeze")
    names = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", HISTORICAL_COMMIT,
                                     "src/mb"], cwd=ROOT, text=True).splitlines()
    source = hashlib.sha256()
    for name in sorted(n for n in names if n.endswith(".py")):
        source.update(Path(name).name.encode())
        source.update(git_blob(name))
    for name, sha in doc["files"].items():
        try:
            contents = git_blob(name)
        except subprocess.CalledProcessError:
            require(name.startswith("materials/tokenizer"), "untracked non-asset in historical freeze")
            contents = (ROOT / name).read_bytes()
        require(hashlib.sha256(contents).hexdigest() == sha, f"historical frozen input changed: {name}")
    # Every old collection module remains byte-identical. Only the independently
    # reviewed STATIC record checker changes; its numerical functions stay fixed.
    for name in names:
        if not name.endswith(".py"):
            continue
        old = git_blob(name)
        if name != "src/mb/v5_static.py":
            require((ROOT / name).read_bytes() == old, f"collection/native migration changed: {name}")
        else:
            def nodes(text: str) -> dict:
                return {getattr(n, "name", f"statement_{i}"): ast.dump(n, include_attributes=False)
                        for i, n in enumerate(ast.parse(text).body)
                        if getattr(n, "name", None) != "_checked_records"}
            require(nodes(old.decode()) == nodes((ROOT / name).read_text()),
                    "STATIC changes exceed the reviewed record-checker repair")
    return {"commit": HISTORICAL_COMMIT, "source_hash": source.hexdigest()[:16],
            "freeze_sha256": hashlib.sha256(frozen_bytes).hexdigest(), "frozen_files": len(doc["files"]),
            "collection_code_unchanged": True, "native_and_smoke_required_on_new_source": True}


@lru_cache(maxsize=2)
def native_hashes(provenance: bool) -> tuple[str, str]:
    tok = chat.load_tokenizer(profile=LLAMA31)
    return (run.template_hash(tok, "v1", LLAMA31.key, provenance=provenance),
            run.prefix_hash(tok, "v1", LLAMA31.key))


def identity_contract(path: Path, cfg: run.StageConfig, source_hash: str) -> dict:
    identity, manifest = read(path / "identity.json"), read(path / "manifest.json")
    require(canonical(run.StageConfig.load(path / "config.yaml").resolved()) == canonical(cfg.resolved()), "stored config differs")
    require(identity.get("limit") is None and manifest.get("smoke") is False, "smoke source is unavailable")
    require(read(path / "run_status.json").get("status") == "complete", "source is incomplete")
    template, prefix = native_hashes(cfg.provenance)
    expected = run.build_identity(cfg, None, template, {int(k): v for k, v in identity["calibration"].items()}, prefix=prefix)
    expected["source_hash"] = source_hash
    require(identity == expected, "run identity differs from exact source/assets/native contract")
    for key in ("model_profile", "tokenizer_manifest_sha", "template_hash", "prefix_hash"):
        require(manifest.get(key) == identity[key], "manifest and identity differ")
    require(manifest.get("stage") == cfg.stage, "manifest stage differs")
    return identity


def complete_records(path: Path, cfg: run.StageConfig) -> list[dict]:
    """Audit every raw trial, including deterministic question and donor metadata."""
    identity = read(path / "identity.json")
    report = ledger.load_records(path)
    require(not report.truncated_tails, "truncated raw shard")
    hashes = {a.name: a.config_hash(identity["calibration"][str(a.layer)]["hash"] if a.needs_calibration
                                  else "none", "none", identity["template_hash"]) for a in cfg.arm_configs()}
    require(read(path / "arm_hashes.json") == hashes, "registered arm hashes differ")
    keys = run.stage_expected(cfg, None)
    expected_set = set(keys)
    require(all(ledger.trial_key(r) in expected_set for r in report.records), "unexpected raw trial")
    require(not ledger.conflicting_hashes(report.records, hashes), "raw arm hash differs")
    comp = ledger.completeness(report.records, keys, hashes)
    require(comp["status"] == "complete", "raw ledger incomplete")
    records = [r for r in report.records if r.get("status") == "ok"]
    require(len(records) == len(keys) and len({ledger.trial_key(r) for r in records}) == len(keys),
            "duplicate successful or missing raw record")
    for r in records:
        require(r.get("config_hash") == hashes[r["arm"]], "missing record hash")
        for field in ("label_logits", "label_logprobs"):
            require(isinstance(r.get(field), list) and len(r[field]) == 4
                    and all(static.finite(x) for x in r[field]), "four finite logits/logprobs required")
        require(static.finite(r.get("label_mass")) and 0 <= r["label_mass"] <= 1 + 1e-6,
                "invalid label mass")
    if not cfg.provenance:
        rows, status = static._checked_records(path, cfg, {"status": "complete"})
        require(status["consumable"] and not status["truncated_tails"], "STATIC raw audit failed")
        return rows
    episodes = {e.episode_id: e for e in tasks.make_episodes(cfg.n_episodes, cfg.split, cfg.seed)}
    arms = {a.name: a for a in cfg.arm_configs()}
    for r in records:
        prov._validate_record(r)
        ep, a = episodes[r["episode_id"]], arms[r["arm"]]
        text, options, meanings, cap = provenance_tasks.question_body(ep, r["recipient"], r["qid"], r["rotation_id"])
        require(r["options"] == list(options) and r["label_meaning"] == list(meanings)
                and r.get("cap_item_id") == cap and r["text_hash"] == hashlib.sha256(text.encode()).hexdigest()[:16],
                "raw provenance question differs")
        expected = provenance_tasks.record_metadata(ep, r["recipient"], SimpleNamespace(qid=r["qid"], options=options),
                                                   a.donor_robin_conflict, "v1")
        require(r["provenance"] == expected, "raw provenance metadata differs")
        for field, value in {"split": cfg.split, "materials": "v1", "condition": a.condition,
                             "interface": a.interface, "kv_scope": a.kv_scope, "layer": a.layer,
                             "gain": a.gain, "template_hash": identity["template_hash"],
                             "model_revision": identity["model_revision"], "readout_mode": a.readout_mode,
                             "message_form": a.form, "calibration_hash": "none", "mask_hash": "none"}.items():
            require(r.get(field) == value, f"record metadata differs: {field}")
    return records


def named_exceptions(study: str, summary: dict) -> dict:
    """Permit only the observed named CAP failures; all other gates remain binding."""
    require(study in EXCEPTIONS and summary.get("gate") == "fail", "expected historical failed validity")
    if study == "provenance":
        rows = summary["quality"]
        require(rows["C0"]["CAP_ACC"] >= .90 and summary["donor_own_access"]["rule"]["pass"]
                and summary["donor_robin_specificity"]["rule"]["pass"], "provenance access/baseline failed")
        require(set(rows) == {"C0", "KV", "CONFLICT"}, "wrong provenance quality roles")
    else:
        require(summary["baseline"]["pass"] and summary["matched"] and summary["K1_access"]["pass"]
                and summary["content_K1"]["rule"]["pass"], "STATIC baseline/access/content/match failed")
        rr = static.roles(SELECTED, True)
        table = {row["arm"]: row for row in summary["access_table"]}
        require(set(table) == set(rr.values()), "wrong STATIC quality arms")
        rows = {key: table[arm] for key, arm in rr.items()}
    exceptions = EXCEPTIONS[study]
    failures = set()
    for role, row in rows.items():
        require(row.get("n") == 80, "incomplete quality sample")
        for key in ("cap_drop", "mass_drop", "label_mass"):
            require(static.finite(row.get(key)), "nonfinite quality summary")
        require(row["label_mass"] >= .90 - 1e-12 and row["mass_drop"] <= .05 + 1e-12,
                "format failure cannot be excepted")
        if row["cap_drop"] > .05 + 1e-12:
            failures.add(role)
            require(role in exceptions and abs(row["cap_drop"] - exceptions[role]) <= 1e-12,
                    "unapproved capability exception")
    require(failures == set(exceptions), "named observed failures differ")
    return {"original_gate": "fail", "original_cap_drop_ceiling": .05,
            "observed_cap_exceptions": exceptions, "all_other_required_checks_pass": True,
            "retrospective_validation_pass": False, "new_general_cap_threshold": None}


def _stored_sources(cfg: run.StageConfig, root: Path, allowed: set[str]) -> None:
    for pin in cfg.params.get("sources", {}).values():
        path = Path(pin["path"])
        require(path.is_relative_to(REMOTE_RESULTS) and path.relative_to(REMOTE_RESULTS).parts[0] in allowed,
                "foreign historical dependency")
        check_pin(pin, root)
    check_pin(cfg.params["model_assets"], root)


def inventory(root: Path, keys: tuple[str, ...]) -> dict:
    result = {}
    for key in keys:
        directory = root / RUNS[key]
        for p in sorted(directory.rglob("*")):
            if not p.is_file() or any(part.startswith("._") for part in p.parts):
                continue
            require(not p.is_symlink(), "historical run contains a symlink")
            rel = p.relative_to(root)
            result[str(rel)] = ledger.file_sha256(p)
    return result


def historical_pins(root: Path, key: str, output: str | None = None) -> dict:
    directory = root / RUNS[key]
    paths = [directory / n for n in ("identity.json", "manifest.json", "run_status.json")]
    if output is None:
        paths.append(directory / "calibration_metadata.json")
    else:
        paths += [directory / n for n in ("arm_hashes.json", output, "notes.jsonl")]
        paths += ledger.shard_paths(directory)
    return {p.name if p.parent == directory else "records_" + p.name:
            {"path": str(REMOTE_RESULTS / p.relative_to(root)), "sha256": ledger.file_sha256(p)} for p in paths}


def audit_history(results_root: Path, study: str) -> dict:
    require(study in STUDY_RUNS, "unknown continuation study")
    root = Path(results_root).resolve()
    code = historical_code()
    LLAMA31.validate_manifest()
    contexts = {}
    for key in STUDY_RUNS[study]:
        path = root / RUNS[key]
        identity = read(path / "identity.json")
        cfg = run.StageConfig(**identity["stage_config"])
        identity_contract(path, cfg, code["source_hash"])
        require(read(path / "manifest.json").get("git") == {"commit": HISTORICAL_COMMIT, "dirty": False},
                "historical run was not collected by exact clean frozen tree")
        _stored_sources(cfg, root, {RUNS[k] for k in STUDY_RUNS[study]})
        contexts[key] = (path, cfg, identity)
    if study == "provenance":
        outputs = {}
        for key, step in (("base", prov.POST_NAMES[0]), ("provenance_validity", prov.POST_NAMES[1])):
            path, cfg, identity = contexts[key]
            rr = prov._validate_config(cfg, step)
            require(cfg.post == [step] and cfg.tag == cfg.stage, "wrong historical post/tag")
            require(identity["calibration"] == {}, "provenance must not use calibration")
            records = complete_records(path, cfg)
            out = prov.baseline_gate(records, rr) if key == "base" else prov.validity_summary(records, rr)
            saved = read(path / f"{step}.json")
            require(saved.get("consumable") is True and all(saved.get(k) == canonical(v) for k, v in out.items()),
                    "historical provenance output differs from raw reproduction")
            outputs[key] = out
        require(outputs["base"]["gate"] == "pass", "historical baseline failed")
        basepath, basecfg, _ = contexts["base"]
        require(basecfg.params["sources"] == {}, "baseline must not consume another run")
        sources = contexts["provenance_validity"][1].params["sources"]
        needed = {"identity.json", "manifest.json", "arm_hashes.json", "run_status.json",
                  "records/attempt-000.jsonl", "v5_provenance_baseline.json"}
        require({str(Path(p["path"]).relative_to(REMOTE_RESULTS / RUNS["base"])) for p in sources.values()} == needed,
                "validity did not consume the exact baseline")
        summary = outputs["provenance_validity"]
        details = {"baseline": outputs["base"], "validity": summary}
    else:
        cp, cc, ci = contexts["cal"]
        static._base_contract(cc, "cal", "cal")
        require(not cc.arms and cc.calibration is None and cc.calibration_layers == list(static.LAYERS)
                and not cc.params["sources"] and ci["calibration"] == {}, "wrong passive calibration")
        meta = read(cp / "calibration_metadata.json")
        require(set(meta) == {"16", "21", "27"}, "incomplete three-layer calibration")
        available = []
        for layer in static.LAYERS:
            entry = meta[str(layer)]
            for field in ("model_profile", "model_revision", "tokenizer_manifest_sha", "prefix_hash", "template_hash"):
                require(entry[field] == ci[field], "foreign calibration metadata")
            require(entry["run_dir"] == str(REMOTE_RESULTS / RUNS["cal"])
                    and entry["path"] == str(REMOTE_RESULTS / RUNS["cal"] / f"calibration_L{layer}.pt")
                    and entry["split"] == cc.split and entry["n_episodes"] == 60
                    and entry["smoke"] is False and entry["hidden_size"] == LLAMA31.hidden_size,
                    "calibration metadata differs")
            check_pin({"path": entry["path"], "sha256": entry["file_sha256"]}, root)
            if not any(str(k).startswith("raw:") for k in entry["static_unusable"]):
                available.append(layer)
        require(available == list(static.LAYERS), "historical available layers changed")
        expected_sources = {"cal_" + k: v for k, v in historical_pins(root, "cal").items()}
        expected_sources["calibration_metadata"] = expected_sources["cal_calibration_metadata.json"]
        for layer in static.LAYERS:
            expected_sources[f"calibration_L{layer}"] = {"path": meta[str(layer)]["path"],
                                                        "sha256": meta[str(layer)]["file_sha256"]}
        outputs = {}
        for key, phase in (("match", "match"), ("static_validity", "validity")):
            path, cfg, identity = contexts[key]
            static._base_contract(cfg, phase, phase)
            if phase == "validity":
                expected_sources = {**expected_sources, **{"history_0_" + k: v for k, v in
                    historical_pins(root, "match", "v5_static_match.json").items()}}
            require(cfg.params["sources"] == expected_sources, "historical STATIC source chain differs")
            require(cfg.params["calibration_run"] == str(REMOTE_RESULTS / RUNS["cal"]), "foreign calibration run")
            specs = ([static.arm("C0"), static.arm("ONE"), *[static.arm("STATIC", l, g) for l in available for g in static.GAINS]]
                     if phase == "match" else [static.arm("C0"), static.arm("ONE"), static.arm("STATIC", 16, .5), static.arm("CF")])
            static._expected_arms(specs, cfg)
            used = {str(a["layer"]) for a in specs if a["condition"] == "STATIC"}
            require({str(k): v for k, v in cfg.calibration.items()} == {l: meta[l]["path"] for l in used}, "wrong calibration map")
            require(identity["calibration"] == {l: {"path": meta[l]["path"], "hash": meta[l]["hash"],
                    "smoke": False, "file_sha256": meta[l]["file_sha256"]} for l in used}, "calibration identity differs")
            for field in ("prefix_hash", "template_hash"):
                require(identity[field] == ci[field], "historical template changed")
            history = [] if phase == "match" else [{"run_dir": str(REMOTE_RESULTS / RUNS["match"]),
                                                    "output_source": "history_0_v5_static_match.json"}]
            require(cfg.params["history"] == history, "unapproved refinement or history")
            if phase == "validity":
                require(cfg.params["selected"] == SELECTED and cfg.params["roles"] == static.roles(SELECTED, True), "selected setting changed")
            records = complete_records(path, cfg)
            output = (static.select(v4.access_table(records, 40), available) if phase == "match"
                      else static.validity(records, SELECTED))
            if phase == "match":
                saved = read(path / "v5_static_match.json")
                require(saved.get("consumable") is True and all(saved.get(k) == canonical(v) for k, v in output.items()),
                        "coarse selection differs from original raw grid")
                require(output["gate"] == "matched" and {k: output["selection"][k] for k in SELECTED} == SELECTED,
                        "named STATIC was not the original selected setting")
            else:
                require(not (path / "v5_static_validity.json").exists(), "historical checker failure must remain unmodified")
            outputs[phase] = output
        summary = outputs["validity"]
        details = {"selection": outputs["match"], "validity": summary,
                   "historical_checker_failed": True, "recomputed_by_corrected_checker": True}
    admission = named_exceptions(study, summary)
    return canonical({"protocol": VERSION, "study": study, "historical_code": code,
                      "runs": {k: RUNS[k] for k in STUDY_RUNS[study]}, "inventory": inventory(root, STUDY_RUNS[study]),
                      "admission": admission, "diagnostics": details, "paid_execution_authorized": False})


def config_from_evidence(study: str, evidence: dict, evidence_pin: dict) -> run.StageConfig:
    require(evidence.get("study") == study and evidence.get("protocol") == VERSION, "wrong evidence artifact")
    common = {"layer": 21, "recipients": ["A"]}
    if study == "provenance":
        arms = [{"condition": "C0", **common}, {"condition": "ONE", "interface": "kv", "kv_scope": "P", "gain": 1., **common},
                {"condition": "ONE", "interface": "kv", "kv_scope": "P", "gain": 1., "donor_robin_conflict": True, **common}]
        stage = "v5_llama31_provenance_confirm"
        roles = {role: ArmConfig(**a).name for role, a in zip(("C0", "KV", "CONFLICT"), arms)}
        qids, calibration = prov.FORMAL_QIDS, None
    else:
        arms = [static.arm("C0"), static.arm("ONE"), static.arm("STATIC", 16, .5)]
        stage, roles = "v5_llama_static_confirm", static.roles(SELECTED)
        qids = static.FORMAL_QIDS
        calibration = {"16": str(REMOTE_RESULTS / RUNS["cal"] / "calibration_L16.pt")}
    sources = {f"historical_{i:04d}": {"path": str(REMOTE_RESULTS / rel), "sha256": sha}
               for i, (rel, sha) in enumerate(sorted(evidence["inventory"].items()))}
    sources["continuation_evidence"] = evidence_pin
    if study == "static":
        meta_rel = str(Path(RUNS["cal"]) / "calibration_metadata.json")
        sources["calibration_metadata"] = {"path": str(REMOTE_RESULTS / meta_rel), "sha256": evidence["inventory"][meta_rel]}
    params = {"protocol": "v5", "continuation": {"version": VERSION, "study": study,
              "admission": evidence["admission"], "historical_commit": HISTORICAL_COMMIT},
              "model_assets": static.pin(LLAMA31.manifest_path), "sources": sources, "roles": roles,
              "smoke_only": False}
    if study == "provenance":
        params["provenance_contract"] = prov.VERSION
    else:
        params.update(phase="confirm", selected=SELECTED)
    return run.StageConfig(stage=stage, split=stage, tag=f"v5_continuation_{study}", n_episodes=600,
                           seed=0, arms=arms, qids=list(qids), episodes_per_batch=2, max_rows=16,
                           calibration=calibration, post=[], model_profile=LLAMA31.key, params=params)


def verify_config_contract(cfg: run.StageConfig, *, results_root: Path | None = None) -> dict:
    continuation = (cfg.params or {}).get("continuation", {})
    require(continuation.get("version") == VERSION and continuation.get("study") in STUDY_RUNS, "not an explicit continuation")
    study = continuation["study"]
    evidence_pin = cfg.params["sources"]["continuation_evidence"]
    evidence = read(check_pin(evidence_pin, results_root))
    root = Path(results_root) if results_root is not None else REMOTE_RESULTS
    require(evidence == audit_history(root, study), "evidence does not reproduce from historical raw sources")
    expected = config_from_evidence(study, evidence, evidence_pin)
    require(cfg.resolved() == expected.resolved(), "formal config differs from the named fixed continuation")
    for value in cfg.params["sources"].values():
        check_pin(value, results_root)
    check_pin(cfg.params["model_assets"], results_root)
    return evidence


def prepare(study: str, results_root: Path, artifact_path: Path) -> tuple[dict, run.StageConfig]:
    evidence = audit_history(results_root, study)
    text = json.dumps(evidence, indent=2, sort_keys=True, allow_nan=False) + "\n"
    pin = {"path": str(artifact_path.relative_to(ROOT)) if artifact_path.is_relative_to(ROOT) else str(artifact_path),
           "sha256": hashlib.sha256(text.encode()).hexdigest()}
    return evidence, config_from_evidence(study, evidence, pin)


def analyze_run(run_dir: Path, *, results_root: Path | None = None) -> dict:
    """Pure formal analysis; completion depends on the ledger, never its effects."""
    path = Path(run_dir)
    cfg = run.StageConfig(**read(path / "identity.json")["stage_config"])
    evidence = verify_config_contract(cfg, results_root=results_root)
    identity_contract(path, cfg, run.source_hash())
    records = complete_records(path, cfg)
    study = evidence["study"]
    if study == "provenance":
        summary = prov.formal_summary(records, cfg.params["roles"], LLAMA31.key)
        # Original Qwen inference remains separate. Its slots in this amendment
        # stay unavailable; no old effects enter preparation or continuation.
        summary["amended_families"] = prov.combine_formal({prov.MODEL_PROFILES[0]: None, LLAMA31.key: summary})
    else:
        summary = static.formal_summary(records, SELECTED)
    return canonical({"protocol": VERSION, "study": study, "consumable": True, "gate": "pass",
                      "gate_meaning": "complete ledger and analysis, not effect or matching success",
                      "original_admission": evidence["admission"], "summary": summary,
                      "original_qwen_inference_unchanged": True})
