"""Torch-free v5 record-provenance gates and paired analysis.

Candidates a/b/r/d always denote the original physical A/B/Robin/spare items.
The validation stage cannot consume receiver-attribution or anchor questions.
Cross-checkpoint multiplicity is applied only by ``combine_formal``; episodes
and model-specific effect sizes are never pooled.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from mb import analyze, ledger, tasks

SELF_QIDS = ("PROV_SELF_RULE", "PROV_ROBIN_RULE", "PROV_SELF_WORD", "PROV_ROBIN_WORD")
DONOR_QIDS = ("PROV_DONOR_SELF_RULE", "PROV_DONOR_ROBIN_RULE",
              "PROV_DONOR_SELF_WORD", "PROV_DONOR_ROBIN_WORD")
BASELINE_QIDS = (*SELF_QIDS, "START", "WORD", "CAP0", "CAP1")
ACCESS_QIDS = (*DONOR_QIDS, "CAP0", "CAP1")
FORMAL_QIDS = (*SELF_QIDS, *DONOR_QIDS, "START", "WORD", "CAP0", "CAP1")
POST_NAMES = ("v5_provenance_baseline", "v5_provenance_validity", "v5_provenance_contrasts")
MODEL_PROFILES = ("qwen3_4b_instruct_2507", "llama31_8b_instruct")
MODEL_PREFIX = dict(zip(MODEL_PROFILES, ("qwen", "llama31")))
SECONDARY_NAMES = ("robin_word_conflict", "rule_source_qualification", "word_source_qualification")
N_BOOT = 10_000
SEED = 0
VERSION = "v5-provenance-v1"


def _require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def _kind(qid: str) -> str:
    return "word" if "WORD" in qid else "rule"


def _physical_logit(rec: Mapping[str, Any], candidate: str) -> float:
    option = rec["provenance"]["candidates"][_kind(rec["qid"])][candidate]
    return float(rec["label_logits"][rec["options"].index(option)])


def _ratio(rec: Mapping[str, Any], numerator: str, denominator: str) -> float:
    return _physical_logit(rec, numerator) - _physical_logit(rec, denominator)


def _correct(rec: Mapping[str, Any]) -> float:
    chosen = int(np.argmax(rec["label_logits"]))
    if rec["qid"].startswith("CAP"):
        return float(rec["label_meaning"][chosen] == "correct")
    return float(rec["options"][chosen] == rec["provenance"]["expected_truth"])


def _validate_record(rec: Mapping[str, Any]) -> None:
    _require(rec.get("status") == "ok", "only successful records may be scored")
    logits = rec.get("label_logits", [])
    _require(len(logits) == 4 and all(x is not None and math.isfinite(float(x)) for x in logits),
             "four finite logits are required")
    logprobs = rec.get("label_logprobs", [])
    _require(len(logprobs) == 4 and all(x is not None and math.isfinite(float(x)) for x in logprobs),
             "four finite label log probabilities are required")
    mass = rec.get("label_mass")
    _require(mass is not None and math.isfinite(float(mass)) and 0 <= float(mass) <= 1 + 1e-6,
             "finite valid label mass is required")
    p = rec.get("provenance", {})
    _require(p.get("version") == VERSION, "missing or unsupported provenance metadata")
    side = rec["recipient"]
    _require(side in ("A", "B") and p.get("recipient_role") == side
             and p.get("donor_role") == ("B" if side == "A" else "A"), "source roles differ")
    _require(type(p.get("donor_robin_conflict")) is bool, "conflict flag must be Boolean")
    for key in ("receiver_card_sha256", "donor_card_sha256"):
        _require(bool(re.fullmatch("[0-9a-f]{64}", str(p.get(key, "")))), "invalid private-card hash")
    _require(isinstance(rec.get("text_hash"), str) and bool(rec["text_hash"]), "missing question hash")
    for kind in ("rule", "word"):
        candidates = p.get("candidates", {}).get(kind, {})
        _require(set(candidates) == set("abrd") and len(set(candidates.values())) == 4
                 and all(isinstance(x, str) and x for x in candidates.values()), "physical candidates must be distinct")
        for source, owner in (("receiver", side), ("donor", p["donor_role"])):
            truth = p.get(f"{source}_truth", {})
            robin = "d" if owner == "B" and p["donor_robin_conflict"] else "r"
            _require(truth.get(f"{kind}_self") == candidates[owner.lower()]
                     and truth.get(f"{kind}_robin") == candidates[robin], "original-record truth differs from physical candidates")
    qid = rec["qid"]
    if qid.startswith("CAP"):
        meanings, options = list(rec.get("label_meaning", [])), list(rec.get("options", []))
        _require(len(meanings) == len(options) == 4 and len(set(options)) == 4
                 and meanings.count("correct") == 1, "CAP correct answer is not unique")
        _require(p.get("expected_truth") is None and p.get("source_role") is None,
                 "CAP must not masquerade as record recall")
        return
    candidates = p["candidates"][_kind(qid)]
    options = list(rec.get("options", []))
    _require(len(options) == 4 and set(options) == set(candidates.values()), "question options differ from physical candidates")
    labels = p.get("candidate_labels", rec.get("candidate_labels"))
    _require(labels == {key: str(options.index(value) + 1) for key, value in candidates.items()},
             "candidate labels disagree with physical option order")
    source = "donor" if qid in DONOR_QIDS else "receiver"
    field = "robin" if "ROBIN" in qid else "self"
    _require(p.get("source_role") == p[f"{source}_role" if source == "donor" else "recipient_role"],
             "question source role differs")
    _require(p.get("expected_truth") == p[f"{source}_truth"][f"{_kind(qid)}_{field}"],
             "question truth differs from its named original record")


def checked_records(records: Sequence[dict], roles: Mapping[str, str], qids: Sequence[str],
                    expected_n: int, *, baseline: bool = False) -> list[dict]:
    """Require a complete paired rectangular sample; never drop malformed trials."""
    _require(expected_n >= 2, "at least two episodes are required")
    required_roles = {"C0", "CONFLICT"} if baseline else {"C0", "KV", "CONFLICT"}
    _require(set(roles) == required_roles and len(set(roles.values())) == len(roles), "wrong or aliased arm roles")
    qids = tuple(qids)
    _require(len(set(qids)) == len(qids) and set(qids) <= set(FORMAL_QIDS), "invalid question whitelist")
    recipients = ("A", "B") if baseline else ("A",)
    keys, rotations, candidates, cards, questions = set(), defaultdict(set), {}, {}, {}
    for rec in records:
        _require(rec.get("arm") in roles.values() and rec.get("qid") in qids
                 and rec.get("recipient") in recipients, "unexpected arm, recipient or question; access-only gates reject attribution inputs")
        _validate_record(rec)
        key = ledger.trial_key(rec)
        _require(key not in keys, "duplicate successful record")
        keys.add(key)
        ep, arm, side, qid, rot = key
        _require(type(rot) is int and 0 <= rot < 4, "invalid answer ordering")
        rotations[ep].add(rot)
        p = rec["provenance"]
        _require(p["donor_robin_conflict"] == (arm == roles["CONFLICT"]), "arm and donor mutation disagree")
        canonical = json.dumps(p["candidates"], sort_keys=True)
        _require(candidates.setdefault(ep, canonical) == canonical, "physical candidates changed across paired arms")
        for source, name in (("receiver", side), ("donor", p["donor_role"])):
            variant = p["donor_robin_conflict"] if name == "B" else False
            card_key = (ep, name, variant)
            _require(cards.setdefault(card_key, p[f"{source}_card_sha256"]) == p[f"{source}_card_sha256"],
                     "original private-card hash differs across paired questions or arms")
        question_key = (ep, side, qid, rot)
        fingerprint = (rec["text_hash"], tuple(rec.get("options", [])))
        _require(questions.setdefault(question_key, fingerprint) == fingerprint, "paired question text or options differ")
    _require(len(rotations) == expected_n, "wrong episode count; no episode exclusions permitted")
    for ep, rots in rotations.items():
        _require(len(rots) == 2 and abs(max(rots) - min(rots)) == 2, "each episode needs two balanced orderings")
        expected = {(ep, arm, side, qid, rot) for arm in roles.values() for side in recipients
                    for qid in qids for rot in rots}
        _require(expected <= keys, "incomplete paired sample or missing ordering")
    _require(len(keys) == expected_n * len(roles) * len(recipients) * len(qids) * 2,
             "unexpected successful trial keys")
    return list(records)


def _episode_scores(records: Sequence[dict]) -> pd.DataFrame:
    rows = []
    for rec in records:
        row = {k: rec[k] for k in ("episode_id", "arm", "recipient", "qid")}
        row.update(accuracy=_correct(rec), label_mass=float(rec["label_mass"]))
        if not rec["qid"].startswith("CAP"):
            pair = ("d", "r") if "ROBIN" in rec["qid"] else ("b", "a")
            row["score"] = _ratio(rec, *pair)
            chosen = rec["options"][int(np.argmax(rec["label_logits"]))]
            row["fixed_candidate_choice"] = float(chosen == rec["provenance"]["candidates"][_kind(rec["qid"])][pair[0]])
            # Only ordinary KV and C0 use this fixed spare-foil access yardstick.
            if rec["qid"] in ("PROV_DONOR_SELF_RULE", "PROV_DONOR_SELF_WORD"):
                row["spare_foil_access"] = _ratio(rec, "b", "d")
        rows.append(row)
    return pd.DataFrame(rows).groupby(["episode_id", "arm", "recipient", "qid"], sort=True).mean().reset_index()


def _vector(scores: pd.DataFrame, arm: str, qid: str, column: str = "score", side: str = "A") -> pd.Series:
    values = scores[(scores.arm == arm) & (scores.qid == qid) & (scores.recipient == side)]
    return values.set_index("episode_id")[column].sort_index()


def _difference(scores: pd.DataFrame, arm1: str, arm2: str, qid: str, column: str = "score") -> np.ndarray:
    a, b = (_vector(scores, arm, qid, column) for arm in (arm1, arm2))
    _require(a.index.equals(b.index), "paired episode identities differ")
    out = (a - b).to_numpy(dtype=float)
    _require(bool(np.isfinite(out).all()), "non-finite paired score")
    return out


def _bound(values: Sequence[float], n_boot: int) -> dict:
    values = np.asarray(values, dtype=float)
    lower = analyze.one_sided_lower_bound(values, n_boot=n_boot, seed=SEED)
    return {"n": len(values), "mean": float(values.mean()), "lb95_one_sided": lower, "pass": lower > 0}


def _quality(scores: pd.DataFrame, arm: str, side: str = "A") -> dict:
    group = scores[(scores.arm == arm) & (scores.recipient == side)]
    cap = group[group.qid.isin(("CAP0", "CAP1"))].groupby("episode_id").accuracy.mean()
    mass = group.groupby("episode_id").label_mass.mean()
    return {"CAP_ACC": float(cap.mean()), "label_mass": float(mass.mean()), "n": len(cap)}


def baseline_gate(records: Sequence[dict], roles: Mapping[str, str], expected_n: int = 60) -> dict:
    rows = checked_records(records, roles, BASELINE_QIDS, expected_n, baseline=True)
    scores = _episode_scores(rows)
    groups = {}
    for role, arm in roles.items():
        groups[role] = {}
        for side in ("A", "B"):
            quality = _quality(scores, arm, side)
            accuracy = {q: float(_vector(scores, arm, q, "accuracy", side).mean())
                        for q in (*SELF_QIDS, "START", "WORD")}
            passed = all(v >= .90 - 1e-12 for v in accuracy.values())
            passed &= quality["CAP_ACC"] >= .90 - 1e-12 and quality["label_mass"] >= .90 - 1e-12
            groups[role][side] = {**quality, "accuracy": accuracy, "pass": bool(passed)}
    return {"gate": "pass" if all(g["pass"] for a in groups.values() for g in a.values()) else "fail",
            "groups": groups}


def validity_summary(records: Sequence[dict], roles: Mapping[str, str], expected_n: int = 80,
                     n_boot: int = N_BOOT) -> dict:
    rows = checked_records(records, roles, ACCESS_QIDS, expected_n)
    scores = _episode_scores(rows)
    quality = {role: _quality(scores, arm) for role, arm in roles.items()}
    base = quality["C0"]
    for role, row in quality.items():
        row["cap_drop"] = base["CAP_ACC"] - row["CAP_ACC"]
        row["mass_drop"] = base["label_mass"] - row["label_mass"]
        row["pass"] = (row["cap_drop"] <= .05 + 1e-12 and row["label_mass"] >= .90 - 1e-12
                       and row["mass_drop"] <= .05 + 1e-12)
    own, robin = {}, {}
    for kind in ("RULE", "WORD"):
        own[kind.lower()] = _bound(_difference(scores, roles["KV"], roles["C0"],
                                    f"PROV_DONOR_SELF_{kind}", "spare_foil_access"), n_boot)
        robin[kind.lower()] = _bound(_difference(scores, roles["CONFLICT"], roles["KV"],
                                      f"PROV_DONOR_ROBIN_{kind}"), n_boot)
    access = {role: {qid: {"accuracy": float(_vector(scores, arm, qid, "accuracy").mean()),
                           "fixed_pair_score": float(_vector(scores, arm, qid).mean())}
                     for qid in DONOR_QIDS} for role, arm in roles.items()}
    passed = (base["CAP_ACC"] >= .90 - 1e-12 and all(row["pass"] for row in quality.values())
              and own["rule"]["pass"] and robin["rule"]["pass"])
    return {"gate": "pass" if passed else "fail", "quality": quality, "donor_own_access": own,
            "donor_robin_specificity": robin, "access": access,
            "access_definition": {"donor_own": "z(b)-z(d), ordinary KV minus C0 only",
                                  "donor_robin": "z(d)-z(r), conflict KV minus ordinary KV"},
            "word_bounds_gate": False}


def _test(values: Sequence[float], name: str, n_boot: int) -> dict:
    result = asdict(analyze.paired_t(values))
    lo, hi = analyze.bootstrap_ci(values, n_boot=n_boot, seed=SEED)
    return {"name": name, "available": True, **result, "ci95_lo": lo, "ci95_hi": hi,
            "p_for_adjustment": result["p_two_sided"]}


def formal_summary(records: Sequence[dict], roles: Mapping[str, str], model_profile: str,
                   expected_n: int = 600, n_boot: int = N_BOOT) -> dict:
    _require(model_profile in MODEL_PROFILES, "unknown checkpoint")
    rows = checked_records(records, roles, FORMAL_QIDS, expected_n)
    scores = _episode_scores(rows)
    primary = _test(_difference(scores, roles["CONFLICT"], roles["KV"], "PROV_ROBIN_RULE"),
                    "robin_rule_conflict", n_boot)
    secondary = [_test(_difference(scores, roles["CONFLICT"], roles["KV"], "PROV_ROBIN_WORD"),
                       SECONDARY_NAMES[0], n_boot)]
    for name, original, qualified in ((SECONDARY_NAMES[1], "START", "PROV_SELF_RULE"),
                                      (SECONDARY_NAMES[2], "WORD", "PROV_SELF_WORD")):
        values = (_difference(scores, roles["KV"], roles["C0"], original)
                  - _difference(scores, roles["KV"], roles["C0"], qualified))
        secondary.append(_test(values, name, n_boot))
    descriptions = {}
    for role, arm in roles.items():
        questions = {}
        for qid in FORMAL_QIDS:
            raw = [r for r in rows if r["arm"] == arm and r["qid"] == qid]
            counts = Counter(r["options"][int(np.argmax(r["label_logits"]))] for r in raw)
            values = _vector(scores, arm, qid, "accuracy").to_numpy()
            lo, hi = analyze.bootstrap_ci(1 - values, n_boot=n_boot, seed=SEED)
            question = {"n_episodes": expected_n, "n_choices": len(raw), "accuracy": float(values.mean()),
                        "error_rate": float(1 - values.mean()), "error_ci95": [lo, hi],
                        "physical_choice_counts": dict(sorted(counts.items())),
                        "label_mass": float(_vector(scores, arm, qid, "label_mass").mean())}
            if not qid.startswith("CAP"):
                question["fixed_pair_score"] = float(_vector(scores, arm, qid).mean())
                physical_counts = Counter(next(key for key, value in r["provenance"]["candidates"][_kind(qid)].items()
                                               if value == r["options"][int(np.argmax(r["label_logits"]))]) for r in raw)
                question["candidate_choice_counts"] = {key: physical_counts[key] for key in "abrd"}
            questions[qid] = question
        descriptions[role] = {"arm": arm, "quality": _quality(scores, arm), "questions": questions}
    paired_errors = {}
    for qid in ("PROV_ROBIN_RULE", "PROV_ROBIN_WORD"):
        errors = -_difference(scores, roles["CONFLICT"], roles["KV"], qid, "accuracy")
        replacement = _difference(scores, roles["CONFLICT"], roles["KV"], qid, "fixed_candidate_choice")
        paired_errors[qid] = {"n_episodes": expected_n, "contrast": "conflict KV minus ordinary KV",
                              "error_rate_difference": float(errors.mean()),
                              "error_difference_ci95": list(analyze.bootstrap_ci(errors, n_boot=n_boot, seed=SEED)),
                              "replacement_d_choice_difference": float(replacement.mean()),
                              "replacement_d_difference_ci95": list(analyze.bootstrap_ci(replacement, n_boot=n_boot, seed=SEED)),
                              "inferential_status": "descriptive; no added hypothesis test"}
    return {"version": VERSION, "gate": "pass", "gate_meaning": "complete analysis, not an effect-significance gate",
            "model_profile": model_profile, "n_episodes": expected_n,
            "n_readouts": len(rows), "primary": [primary], "secondary": secondary,
            "descriptive": descriptions, "paired_error_differences": paired_errors,
            "unit": "episode; two orderings averaged within episode",
            "bootstrap_draws": n_boot, "bootstrap_seed": SEED,
            "interpretation": "A logit shift alone is a preference shift, not increased error choices; no self-selectivity inference.",
            "multiplicity_pending": "combine_formal: two primary and six secondary tests across checkpoints"}


def combine_formal(summaries: Mapping[str, dict | None]) -> dict:
    """Keep unavailable checkpoints in both families without imputing outcomes."""
    _require(set(summaries) == set(MODEL_PROFILES), "both checkpoints must be supplied, with None for unavailable")
    families = {"primary": [], "secondary": []}
    for profile in MODEL_PROFILES:
        summary = summaries[profile]
        if summary is not None:
            _require(summary.get("version") == VERSION and summary.get("model_profile") == profile
                     and summary.get("n_episodes") == 600 and summary.get("n_readouts") == 43_200,
                     "cross-model inference requires the full fixed N=600 per checkpoint")
            _require(summary.get("bootstrap_draws") == N_BOOT and summary.get("bootstrap_seed") == SEED,
                     "wrong formal bootstrap contract")
            _require(summary.get("consumable", True), "cannot combine an incomplete run")
        for family, names in (("primary", ("robin_rule_conflict",)), ("secondary", SECONDARY_NAMES)):
            if summary is not None:
                _require(tuple(r["name"] for r in summary[family]) == tuple(names), "fixed analysis family differs")
            for i, name in enumerate(names):
                if summary is None:
                    row = {"name": name, "available": False, "n": 0, "mean": None, "sd": None,
                           "se": None, "t": None, "p_two_sided": None, "ci95_lo": None, "ci95_hi": None,
                           "p_for_adjustment": 1.0, "reason": "checkpoint comparison unavailable"}
                else:
                    row = dict(summary[family][i])
                    _require(row.get("available") is True and row.get("n") == 600,
                             "a model summary cannot silently omit paired episodes")
                    _require(math.isfinite(row["p_for_adjustment"]) and 0 <= row["p_for_adjustment"] <= 1,
                             "invalid family p-value")
                    _require(row["p_for_adjustment"] == row["p_two_sided"], "family p-value differs from paired test")
                families[family].append({"model_profile": profile, **row})
    for rows in families.values():
        for row, adjusted in zip(rows, analyze.holm([r["p_for_adjustment"] for r in rows])):
            row["p_holm"] = adjusted
    return {"version": VERSION, "families": ledger.sanitize(families), "pooled_episodes": False,
            "primary_family_size": 2, "secondary_family_size": 6}


def _validate_config(cfg: Any, step: str) -> dict[str, str]:
    from mb.conditions import ArmConfig

    stage = {POST_NAMES[0]: ("base", 60, BASELINE_QIDS), POST_NAMES[1]: ("validity", 80, ACCESS_QIDS),
             POST_NAMES[2]: ("confirm", 600, FORMAL_QIDS)}[step]
    suffix, n, qids = stage
    _require(cfg.model_profile in MODEL_PROFILES, "explicit approved checkpoint profile required")
    prefix = f"v5_{MODEL_PREFIX[cfg.model_profile]}_provenance_"
    _require(cfg.stage == cfg.split == prefix + suffix, "stage and split must be the fixed model-specific v5 stage")
    _require(cfg.n_episodes == n and cfg.seed == SEED and tuple(cfg.qids) == tuple(qids),
             "wrong fixed sample, seed or ordered question set")
    _require(cfg.materials == "v1" and not cfg.all_rotations_first, "v5 uses v1 materials and two balanced orderings")
    _require(cfg.episodes_per_batch == 2 and cfg.max_rows == 16 and cfg.calibration is None
             and cfg.calibration_layers == [], "fixed batching and no residual calibration are required")
    roles = (cfg.params or {}).get("roles", {})
    _require((cfg.params or {}).get("provenance_contract") == VERSION
             and (cfg.params or {}).get("protocol") == "v5", "wrong provenance contract")
    asset_pin = (cfg.params or {}).get("model_assets", {})
    _require(isinstance(asset_pin.get("path"), str)
             and bool(re.fullmatch("[0-9a-f]{64}", str(asset_pin.get("sha256", "")))), "missing model asset pin")
    baseline = suffix == "base"
    _require(set(roles) == ({"C0", "CONFLICT"} if baseline else {"C0", "KV", "CONFLICT"}), "wrong stage role map")
    arms = cfg.arm_configs()
    _require(len(arms) == len(roles) and set(roles.values()) == {arm.name for arm in arms}, "configured arms differ from roles")
    layer = 21 if cfg.model_profile == "llama31_8b_instruct" else 24
    common = dict(layer=layer, recipients=("A", "B") if baseline else ("A",), model_profile=cfg.model_profile)
    for arm in arms:
        role = next(k for k, v in roles.items() if v == arm.name)
        if baseline or role == "C0":
            expected = ArmConfig("C0", donor_robin_conflict=role == "CONFLICT", **common)
        else:
            expected = ArmConfig("ONE", interface="kv", kv_scope="P", gain=1,
                                 donor_robin_conflict=role == "CONFLICT", **common)
        _require(asdict(arm) == asdict(expected), "arm differs from the canonical fixed provenance intervention")
    return roles


def _checked_records(run_dir: Path, cfg: Any, status: Mapping[str, Any]) -> tuple[list[dict], dict]:
    from mb import provenance_tasks
    from mb.model_profiles import resolve_profile
    from mb.run import source_hash

    identity = json.loads((run_dir / "identity.json").read_text())
    manifest = json.loads((run_dir / "manifest.json").read_text())
    arm_hash = json.loads((run_dir / "arm_hashes.json").read_text())
    _require(identity["stage_config"] == json.loads(json.dumps(cfg.resolved())), "config differs from stored identity")
    _require(identity.get("source_hash") == source_hash(), "frozen source identity differs")
    profile = resolve_profile(cfg.model_profile)
    _require(identity.get("model_profile") == profile.identity() and identity.get("model_revision") == profile.revision,
             "checkpoint identity differs")
    _require(identity.get("tokenizer_manifest_sha") == cfg.params["model_assets"]["sha256"], "model asset identity differs")
    arms = cfg.arm_configs()
    template = identity.get("template_hash")
    _require(isinstance(template, str) and bool(template), "missing template identity")
    _require(arm_hash == {a.name: a.config_hash("none", "none", template) for a in arms},
             "registered arm hashes differ")
    report = ledger.load_records(run_dir)
    eps = tasks.make_episodes(cfg.n_episodes, cfg.split, cfg.seed)
    expected = ledger.expected_trials([ledger.ArmSpec(a.name, a.recipients) for a in arms],
                                      [(e.episode_id, e.rotations) for e in eps], cfg.qids, set())
    expected_set = set(expected)
    _require(not ledger.conflicting_hashes(report.records, arm_hash), "raw record arm hash differs")
    _require(all(ledger.trial_key(r) in expected_set for r in report.records), "unexpected raw trial key")
    records = [r for r in report.records if r.get("status") == "ok"]
    _require(all(r.get("config_hash") == arm_hash[r["arm"]] for r in records), "missing successful record hash")
    keys = [ledger.trial_key(r) for r in records]
    _require(len(keys) == len(set(keys)), "duplicate successful raw records")
    episodes = {ep.episode_id: ep for ep in eps}
    arm_specs = {arm.name: arm for arm in arms}
    for rec in records:
        _validate_record(rec)
        content, options, meanings, cap_id = provenance_tasks.question_body(
            episodes[rec["episode_id"]], rec["recipient"], rec["qid"], rec["rotation_id"])
        _require(list(rec["options"]) == list(options) and list(rec["label_meaning"]) == list(meanings)
                 and rec.get("cap_item_id") == cap_id
                 and rec["text_hash"] == hashlib.sha256(content.encode()).hexdigest()[:16],
                 "raw question differs from its deterministic text, options or answer ordering")
        question = SimpleNamespace(qid=rec["qid"], options=tuple(rec["options"]))
        metadata = provenance_tasks.record_metadata(episodes[rec["episode_id"]], rec["recipient"], question,
                                                     arm_specs[rec["arm"]].donor_robin_conflict, cfg.materials)
        _require(rec["provenance"] == metadata, "raw provenance metadata differs from deterministic original episode")
    completeness = ledger.completeness(report.records, expected, arm_hash)
    smoke = bool(manifest.get("smoke", True) or identity.get("limit") is not None)
    consumable = not smoke and completeness["status"] == status.get("status") == "complete"
    return records, {"consumable": consumable, "smoke": smoke, "completeness": completeness,
                     "truncated_tails": report.truncated_tails, "identity_sha256": ledger.file_sha256(run_dir / "identity.json")}


def postprocess(run_dir: Path, cfg: Any, status: Mapping[str, Any]) -> dict:
    """Runner entry point. Only this wrapper writes its derived stage JSON."""
    from mb.run import validate_stage_sources

    steps = [s for s in cfg.post if s in POST_NAMES]
    _require(len(steps) == 1 and status.get("post_step", steps[0]) == steps[0], "exactly one matching post step is required")
    step = steps[0]
    roles = _validate_config(cfg, step)
    validate_stage_sources(cfg)
    run_dir = Path(run_dir)
    records, out = _checked_records(run_dir, cfg, status)
    out.update(step=step, split=cfg.split, n_episodes=cfg.n_episodes, model_profile=cfg.model_profile)
    if out["consumable"]:
        if step == POST_NAMES[0]:
            out.update(baseline_gate(records, roles, cfg.n_episodes))
        elif step == POST_NAMES[1]:
            out.update(validity_summary(records, roles, cfg.n_episodes))
        else:
            out.update(formal_summary(records, roles, cfg.model_profile, cfg.n_episodes))
    else:
        out.update(gate="unavailable", reason="incomplete or smoke run; no scientific decision")
    out = ledger.sanitize(out)
    (run_dir / f"{step}.json").write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    return out
