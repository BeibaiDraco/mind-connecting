#!/usr/bin/env python3
"""Recompute the frozen v4 formal analysis without torch or writes to the raw run.

    .venv/bin/python scripts/report_v4_formal.py
    .venv/bin/python scripts/report_v4_formal.py --check-only

The default source is the original SD-card run. Output is derived documentation;
the runner's postprocess function is deliberately never called because it writes
into the source run. All choices are scored per ordering before episode averaging.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
import os
from pathlib import Path

import numpy as np
import pandas as pd

from mb import analyze, ledger, readouts, run, v4

REPO = Path(__file__).resolve().parents[1]
RUN_ID = "20261009-005433_v4_llama31_confirm_v4_confirm"
N = 600
N_BOOT = 10_000
SEED = 0
METRICS = {"M": ("START", "START_R"), "M_NOW": ("NOW", "NOW_R"), "M_WORD": ("WORD", "WORD_R")}
ROLE_ORDER = ("C0", "K*", "STATIC", "TAG", "UNTAG", "RF", "CF")


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def source_hashes(root: Path) -> dict:
    names = ("identity.json", "manifest.json", "config.yaml", "arm_hashes.json", "run_status.json",
             "completeness.json", "v4_contrasts.json")
    paths = [root / name for name in names] + ledger.shard_paths(root)
    return {str(path.relative_to(root)): {"sha256": ledger.file_sha256(path), "bytes": path.stat().st_size}
            for path in paths}


def compare_stored(actual, stored, path: str = "root") -> list[dict]:
    """Require structural agreement and strict numeric agreement across CPU platforms."""
    changes = []
    if isinstance(actual, dict) and isinstance(stored, dict):
        require(set(actual) == set(stored), f"stored keys differ at {path}")
        for key in actual:
            changes.extend(compare_stored(actual[key], stored[key], f"{path}.{key}"))
    elif isinstance(actual, list) and isinstance(stored, list):
        require(len(actual) == len(stored), f"stored list length differs at {path}")
        for i, (a, b) in enumerate(zip(actual, stored)):
            changes.extend(compare_stored(a, b, f"{path}[{i}]"))
    elif isinstance(actual, (int, float)) and not isinstance(actual, bool) and isinstance(stored, (int, float)):
        # Tiny p-values must agree relatively: a large absolute tolerance could hide zeroing.
        tolerance = 0.0 if ".p_" in path else 1e-12
        require(math.isclose(actual, stored, rel_tol=1e-12, abs_tol=tolerance), f"stored value differs at {path}")
        if actual != stored:
            changes.append({"path": path, "absolute_difference": abs(actual - stored)})
    else:
        require(actual == stored, f"stored value differs at {path}")
    return changes


def verify_pinned_sources(root: Path, cfg: run.StageConfig, identity: dict) -> None:
    """Verify immutable source pins without requiring the GPU's filesystem layout."""
    pins = {**cfg.params["sources"], "model_assets": cfg.params["model_assets"]}
    for name, pin in pins.items():
        path = REPO / pin["path"]
        require(path.is_file() and ledger.file_sha256(path) == pin["sha256"],
                f"pinned source differs: {name}")
    require(pins["model_assets"]["sha256"] == identity["tokenizer_manifest_sha"],
            "model asset manifest differs from the frozen run identity")
    metadata = read(REPO / pins["calibration_metadata"]["path"])
    for layer, configured in cfg.calibration.items():
        entry, recorded = metadata[str(layer)], identity["calibration"][str(layer)]
        require(configured == entry["path"] == recorded["path"], "frozen calibration path identity differs")
        require(entry["file_sha256"] == recorded["file_sha256"] and entry["hash"] == recorded["hash"],
                "calibration metadata differs from the frozen run identity")
        relative = Path(configured).relative_to("/workspace/mb-data")
        local_blob = root.parent.parent / relative
        require(local_blob.is_file() and ledger.file_sha256(local_blob) == entry["file_sha256"],
                "immutable SD calibration bytes differ from the pinned GPU artifact")


def recompute(root: Path) -> tuple[dict, list[dict], pd.DataFrame, run.StageConfig]:
    require(root.name == RUN_ID, "this report is pinned to the original v4 formal run")
    cfg = run.StageConfig.load(root / "config.yaml")
    identity, status = read(root / "identity.json"), read(root / "run_status.json")
    require(cfg.n_episodes == N and cfg.seed == SEED and cfg.model_profile == "llama31_8b_instruct",
            "wrong formal sample, seed, or model")
    require(identity["source_hash"] == run.source_hash(), "frozen analysis/runtime source hash differs")
    require(ledger.file_sha256(root / "config.yaml") == ledger.file_sha256(REPO / "configs/v4/v4_confirm.yaml"),
            "formal input differs from the frozen local configuration")
    require(json.loads(json.dumps(cfg.resolved())) == identity["stage_config"],
            "resolved configuration differs from the frozen run identity")
    verify_pinned_sources(root, cfg, identity)
    records, checked = v4._checked_records(root, cfg, status)
    all_records = ledger.load_records(root)
    require(checked["consumable"] and not checked["truncated_tails"] and not checked["invalid_records"],
            "formal inputs are not complete, finite, and consumable")
    require(len(all_records.records) == len(records) == checked["completeness"]["n_expected"] == 84000,
            "unexpected failed, excluded, duplicate, or missing raw records")
    require({r["recipient"] for r in records} == {"A"}, "unexpected formal recipient")
    require(len({r["episode_id"] for r in records}) == N, "not all 600 episodes are present")
    scores = readouts.score_records(records, readouts.ScoreOptions(rotations=None))
    require(len(scores) == N * 7 and bool((scores.n_rotations == 2).all()), "wrong arm or ordering count")
    require(np.isfinite(scores[[*METRICS, "ACC_RULE", "ACC_WORD", "CAP_ACC", "LABEL_MASS"]]).all().all(),
            "a required episode-level metric is missing or non-finite")
    roles = cfg.params["roles"]
    families = v4.analyze_families(scores, roles, n_boot=N_BOOT)
    require(all(row["available"] and row["n"] == N for rows in families.values() for row in rows),
            "a prespecified contrast excluded episodes")
    access = v4.access_table(records, N)
    by_arm = {row["arm"]: row for row in access}
    target, static = by_arm[roles["K1"]], by_arm[roles["STATIC"]]
    formal_matched = bool(target["acc_increment"] > 0 and static["acc_increment"] > 0
                         and abs(target["acc_increment"] - static["acc_increment"]) <= 0.25 * target["acc_increment"] + 1e-12)
    reconstructed = {**checked, "step": "v4_contrasts", "split": cfg.split, "n_episodes": N,
                     "families": families, "descriptive": v4.descriptive(records),
                     "content_Kstar": v4.content_check(records, roles["K*"], roles["CF"], N, n_boot=N_BOOT),
                     "access_table": access, "formal_matched": formal_matched,
                     "independent_route_validated": bool(cfg.params.get("route_validated", False))}
    return ledger.sanitize(reconstructed), records, scores, cfg


def descriptive_tables(records: list[dict], scores: pd.DataFrame, roles: dict) -> tuple[dict, dict]:
    indexed = defaultdict(list)
    for rec in records:
        indexed[(rec["arm"], rec["qid"])].append(rec)
    arms, components = {}, {}
    for role in ROLE_ORDER:
        arm = roles[role]
        group = scores[scores.arm == arm]
        choices = {}
        for qid in v4.FORMAL_QIDS:
            recs = indexed[(arm, qid)]
            require(len(recs) == N * 2, "descriptive choice denominator differs")
            counts = Counter(readouts.argmax_meaning(rec) for rec in recs)
            by_episode = defaultdict(list)
            for rec in recs:
                by_episode[rec["episode_id"]].append(float(readouts.argmax_meaning(rec) == "partner"))
            require(len(by_episode) == N and all(len(values) == 2 for values in by_episode.values()),
                    "descriptive choices do not contain two orderings per episode")
            values = np.array([np.mean(by_episode[key]) for key in sorted(by_episode)], dtype=float)
            # These intervals describe behavior; they are not additional confirmatory tests.
            lo, hi = analyze.bootstrap_ci(values, n_boot=N_BOOT, seed=SEED)
            choices[qid] = {"n_episodes": N, "n_choices": N * 2, "counts": dict(sorted(counts.items())),
                            "rates": {key: value / (N * 2) for key, value in sorted(counts.items())},
                            "partner_rate": float(values.mean()), "partner_ci95": [lo, hi]}
        arms[role] = {"arm": arm, "n_episodes": len(group), "choices": choices,
                      "metric_means": {metric: float(group[metric].mean()) for metric in METRICS},
                      "ACC_RULE": float(group.ACC_RULE.mean()), "ACC_WORD": float(group.ACC_WORD.mean()),
                      "CAP_ACC": float(group.CAP_ACC.mean()), "LABEL_MASS_all_questions": float(group.LABEL_MASS.mean())}
        components[role] = {}
        for metric, (self_qid, robin_qid) in METRICS.items():
            self_value = float(np.mean([readouts.log_ratio(r, "partner", "own") for r in indexed[(arm, self_qid)]]))
            robin_value = float(np.mean([readouts.log_ratio(r, "partner", "robin") for r in indexed[(arm, robin_qid)]]))
            value = arms[role]["metric_means"][metric]
            require(math.isclose(value, self_value - robin_value, abs_tol=1e-12), "metric decomposition differs")
            components[role][metric] = {"self_partner_minus_own": self_value,
                                        "robin_partner_minus_robin": robin_value, "difference": value}
    base = components["C0"]
    for role in components:
        for metric in METRICS:
            comp = components[role][metric]
            comp.update(delta_self_vs_C0=comp["self_partner_minus_own"] - base[metric]["self_partner_minus_own"],
                        delta_robin_vs_C0=comp["robin_partner_minus_robin"] - base[metric]["robin_partner_minus_robin"],
                        delta_metric_vs_C0=comp["difference"] - base[metric]["difference"])
    return arms, components


def build_summary(root: Path) -> dict:
    before = source_hashes(root)
    recomputed, records, scores, cfg = recompute(root)
    differences = compare_stored(recomputed, read(root / "v4_contrasts.json"))
    arms, components = descriptive_tables(records, scores, cfg.params["roles"])
    prior = {}
    for step, source in cfg.params["sources"].items():
        path = REPO / source["path"]
        require(ledger.file_sha256(path) == source["sha256"], "pinned pilot artifact differs")
        prior[step] = read(path)
    by_arm = {row["arm"]: row for row in recomputed["access_table"]}
    formal_quality = {role: {**by_arm[arm], "engineering_eligible_descriptive_recheck":
                            v4.engineering_eligible(by_arm[arm], N)}
                      for role, arm in cfg.params["roles"].items() if arm}
    k1, static = formal_quality["K1"], formal_quality["STATIC"]
    require(source_hashes(root) == before, "raw input bytes changed during this read-only report")
    files = ["docs/protocol/PROTOCOL_V4.md", "docs/protocol/FREEZE_protocol_v4.txt",
             "src/mb/readouts.py", "src/mb/analyze.py", "src/mb/v4.py", "src/mb/ledger.py",
             "scripts/report_v4_formal.py"]
    return {"run_id": root.name, "n_episodes": N, "n_unique_arms": 7, "n_readouts": len(records),
            "n_orderings_per_episode": 2, "n_choices_per_arm_question": N * 2,
            "analysis": {"primary_family_size": 5, "secondary_family_size": 4, "paired_test": "two-sided t",
                         "familywise_alpha": 0.05, "adjustment": "Holm separately in each family",
                         "bootstrap_draws": N_BOOT, "bootstrap_seed": SEED, "bootstrap_unit": "episode",
                         "bootstrap_interval": "pointwise 95% percentile; not multiplicity adjusted",
                         "metric_unit": "natural-log probability ratio (logit differences, nats)",
                         "episode_exclusions": 0, "unavailable_primary_comparisons": 0},
            "stored_output_comparison": {"agrees": True, "exact_equality": not differences,
                                          "roundoff_differences": differences, "relative_tolerance": 1e-12,
                                          "absolute_tolerance_non_p_values": 1e-12},
            "recomputed_frozen_output": recomputed, "arms": arms, "components": components,
            "formal_quality": formal_quality,
            "route_limits": {"pilot_matched": prior["match"]["matched"],
                             "independent_core_gate": prior["validity"]["core_gate"],
                             "independent_route_validated": prior["validity"]["route_validated"],
                             "independent_matched": prior["validity"]["matched"],
                             "formal_matched": recomputed["formal_matched"],
                             "formal_access_gap": abs(k1["acc_increment"] - static["acc_increment"]),
                             "formal_relative_access_gap": abs(k1["acc_increment"] - static["acc_increment"]) / k1["acc_increment"],
                             "matched_route_claim_supported": False,
                             "STATIC_test_estimable": True},
            "prior_stage_outputs": {key: prior[key] for key in ("baseline", "strength", "match", "validity")},
            "provenance": {"raw_inputs": before, "source_files": {p: ledger.file_sha256(REPO / p) for p in files},
                           "model_profile": read(root / "identity.json")["model_profile"],
                           "model_revision": read(root / "identity.json")["model_revision"],
                           "raw_inputs_unchanged_after_analysis": True}}


def f(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def pct(value: float) -> str:
    return f"{100 * value:.3f}%"


def table(headers: list[str], rows: list[list]) -> list[str]:
    return ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |",
            *["| " + " | ".join(map(str, row)) + " |" for row in rows], ""]


def report(summary: dict) -> str:
    frozen, arms, comp = (summary[key] for key in ("recomputed_frozen_output", "arms", "components"))
    quality, limits = summary["formal_quality"], summary["route_limits"]
    choice = lambda role, qid: arms[role]["choices"][qid]["partner_rate"]
    p0 = frozen["families"]["primary"][0]
    rf_word = frozen["families"]["secondary"][3]
    max_roundoff = max((row["absolute_difference"] for row in
                       summary["stored_output_comparison"]["roundoff_differences"]), default=0.0)
    lines = ["# V4 formal results: Llama 3.1 8B Instruct", "",
             "## Main finding and scope", "",
             f"The internal-memory link increased attribution of the donor's assigned rule to the receiver relative to no link "
             f"(K*−C0 M = {f(p0['mean'])} nats, 95% episode-bootstrap CI [{f(p0['ci95_lo'])}, {f(p0['ci95_hi'])}]). "
             f"The receiver selected the donor's rule as its original assignment in {pct(choice('K*','START'))} "
             f"of orderings, versus {pct(choice('C0','START'))} under C0. These are distinct behavioral and logit results.", "",
             "The tagged-text and link-cut controls separate several effects, but this run does **not** establish "
             "the matched-access route claim: STATIC was available and estimable but unmatched, and the independent "
             "route-validity check failed. The code-word effect after cutting the link is also a boundary: its "
             "prespecified Robin-subtracted logit effect is negative, despite a small positive donor-choice rate. "
             "Each hypothesis is reported separately; this is not an all-or-nothing replication verdict.", "",
             "## Data, frozen design, and reproduction", "",
             f"- Original run: `{summary['run_id']}`; all 600 paired episodes, seven unique arms, 84,000/84,000 readouts.",
             "- K*=K1 at KV-P w=1; STATIC layer 21, raw direction, gain 0.7. Strength and STATIC gain were selected "
             "using independent access/CAP/format data; all settings were frozen before formal attribution analysis.",
             "- Two counterbalanced label orderings are averaged within each episode before inference. No episode "
             "was excluded, no missing value was imputed, and no parameter was reselected after formal outcomes.",
             "- The interrupted run resumed in the same directory. The two immutable shards contain 9,960 and "
             "74,040 successful readouts; the technical closeout verified preservation of original data and shared FULL/RF snapshots.",
             "- Raw recomputation agrees with stored `v4_contrasts.json` in structure and numerical values within "
             f"1e-12 relative/absolute tolerance (p-values use relative tolerance only). Differences are floating-point "
             f"roundoff only, with maximum absolute difference {max_roundoff:.3g}. Raw inputs were hash-checked before/after analysis.", "",
             "Reproduce from the mounted SD card (CPU only; no torch or model):", "",
             "```bash", ".venv/bin/python scripts/report_v4_formal.py", "```", "",
             "Use `--check-only` to validate/recompute without writing derived files. `summary.json` records raw-input "
             "and source hashes, exact effects, all descriptive counts, and the frozen pilot evidence. "
             "[Protocol](../../protocol/PROTOCOL_V4.md) sections 4–5 specify the analysis.", "",
             "## Metrics and inferential units", "",
             "For each ordering, L_self = z(partner) − z(own) on the self question, and L_Robin = z(partner) − "
             "z(Robin) on its Robin counterpart. M = L_self − L_Robin for START; M_NOW and M_WORD apply the "
             "same subtraction to NOW and WORD. Logit differences equal natural-log probability ratios (nats); "
             "they are neither percentages nor normalized four-choice probabilities. Positive arm differences "
             "indicate a relative preference shift after Robin subtraction, not by themselves a behavioral takeover rate.", "",
             "The primary family contains five two-sided paired t-tests; the secondary family contains four, with "
             "separate Holm familywise correction at 0.05. Every contrast has N=600 paired episodes. CIs use "
             "10,000 episode-bootstrap draws, seed 0; they are pointwise 95% percentile intervals, not simultaneous "
             "Holm-adjusted intervals. Expected positive signs did not change the two-sided tests.", ""]
    for family, title in (("primary", "Primary family (five tests)"), ("secondary", "Secondary family (four tests)")):
        lines += [f"## {title}", ""]
        rows = []
        for r in frozen["families"][family]:
            label = f"{r['role1']} − {r['role2']}"
            if r["role2"] == "STATIC":
                label += " †"
            rows.append([label, r["metric"], r["n"], f(r["mean"]), f"[{f(r['ci95_lo'])}, {f(r['ci95_hi'])}]",
                         f(r["t"], 3), f"{r['p_two_sided']:.3g}", f"{r['p_holm']:.3g}"])
        lines += table(["Contrast", "Metric", "Paired N", "Mean (nats)", "95% CI", "t (df=599)", "p, two-sided", "p, Holm"], rows)
    lines += ["† K1−STATIC remains an available prespecified statistical test in the five-test family. Its "
              "positive difference cannot be interpreted as an effect at matched access. No comparison was removed "
              "from multiplicity bookkeeping. The negative RF−C0 M_WORD contrast is significant in the opposite "
              "direction to a positive residual code-word effect.", "",
              "## Actual claiming choices (descriptive)", "",
              "Each self-question cell is the donor/partner argmax count divided by **1,200 choices = 600 episodes × "
              "two orderings**. The inferential N remains 600. Values are scored separately for each ordering; they "
              "are not argmaxes of probabilities pooled across orderings. Zero means no such choice was observed "
              "in this sample, not a universal absence of the behavior.", ""]
    rows = []
    for role in ROLE_ORDER:
        values = []
        for qid in ("START", "NOW", "WORD"):
            ch = arms[role]["choices"][qid]
            values.append(f"{ch['counts'].get('partner',0)}/1200 ({pct(ch['partner_rate'])})")
        rows.append([role, *values])
    lines += table(["Arm", "Assigned rule (START)", "Current rule (NOW)", "Code word (WORD)"], rows)
    lines += ["CF choices refer to the replacement donor's content. All arm/question choice categories, including "
              "own, Robin and unused/distractor choices, are retained in `summary.json`. Behavioral intervals in "
              "the plot resample the 600 episode means; they do not use a binomial N=1,200.", "",
              f"**Tagged versus untagged text.** Removing the source header increased current-rule adoption from "
              f"{pct(choice('TAG','NOW'))} to {pct(choice('UNTAG','NOW'))}. Both text conditions nevertheless had "
              f"{pct(choice('TAG','START'))} assigned-rule donor choices. Thus the current-rule effect is not evidence "
              "that the receiver reassigned its original rule. This additional checkpoint supports the header "
              "effect on current-rule adoption; it does not reproduce an untagged-text behavioral increase in "
              "assigned-rule claiming in this sample.", "",
              f"**Content access versus assigned-rule claiming.** Tagged text gave {pct(quality['TAG']['partner_rate'])} "
              f"correct donor-rule access, exceeding K*'s {pct(quality['K*']['partner_rate'])}, while assigned-rule "
              f"claiming was {pct(choice('TAG','START'))} versus {pct(choice('K*','START'))}. This is a descriptive "
              "dissociation between access and self-attribution; it is not a strength-matched isolation of route.", "",
              "## Robin-subtracted components (all arms; descriptive)", "",
              "Absolute means below are first averaged across the two orderings and then across 600 episodes. "
              "The last three columns show arm−C0 changes; ΔM = Δself − ΔRobin. All entries are nats.", ""]
    rows = []
    for role in ROLE_ORDER:
        for metric in METRICS:
            c = comp[role][metric]
            rows.append([role, metric, *[f(c[k]) for k in ("self_partner_minus_own", "robin_partner_minus_robin",
                         "difference", "delta_self_vs_C0", "delta_robin_vs_C0", "delta_metric_vs_C0")]])
    lines += table(["Arm", "Metric", "Self", "Robin", "M", "Δself", "ΔRobin", "ΔM"], rows)
    c = comp["RF"]["M_WORD"]
    lines += [f"**Why RF code-word choices and M_WORD differ.** RF selected the donor word in "
              f"{arms['RF']['choices']['WORD']['counts'].get('partner',0)}/1200 orderings ({pct(choice('RF','WORD'))}), "
              f"versus {arms['C0']['choices']['WORD']['counts'].get('partner',0)}/1200 under C0. Yet the raw self-question "
              f"logit component changed by {f(c['delta_self_vs_C0'])}, while the Robin-question component changed "
              f"by {f(c['delta_robin_vs_C0'])}; subtraction gives RF−C0 M_WORD = {f(rf_word['mean'])} "
              f"(95% CI [{f(rf_word['ci95_lo'])}, {f(rf_word['ci95_hi'])}], Holm p={rf_word['p_holm']:.3g}). "
              "Argmax events and the episode-mean logit contrast measure different features. This result cannot "
              "be reported as a positive Robin-subtracted residual code-word effect, or as an absence of all "
              "donor-word influence. By contrast, the RF current-rule "
              "secondary contrast is positive; cutting the link changes assigned, current-rule and code-word readouts differently.", "",
              "## Access, capability, and format (all arms)", "",
              "ACC_RULE is z(partner)−z(unused); ACC_WORD is z(partner)−z(distractor). Their gains below are paired "
              "arm−C0 mean differences. CAP is mean correctness over two items and both orderings within episode "
              "(2,400 descriptive choices per arm). Label mass is probability on the four valid answer tokens, "
              "not probability renormalized over them. The engineering screen uses the four access/CAP questions; "
              "the all-question label mass is also shown.", ""]
    rows = []
    for role in ROLE_ORDER:
        q = quality[role]
        rows.append([role, f(q["acc_increment"]), f(q["acc_word_increment"]), pct(q["partner_rate"]),
                     pct(arms[role]["choices"]["ACC_WORD"]["partner_rate"]), pct(arms[role]["CAP_ACC"]),
                     f(100*q["cap_drop"], 4), pct(q["label_mass"]), pct(arms[role]["LABEL_MASS_all_questions"]),
                     q["engineering_eligible_descriptive_recheck"]])
    lines += table(["Arm", "Rule gain", "Word gain", "Rule access", "Word access", "CAP", "CAP drop (pp)",
                    "Mass: access/CAP", "Mass: all", "Formal screen"], rows)
    lines += [f"K*'s formal CAP drop is exactly {100*quality['K*']['cap_drop']:.6f} percentage points, at the "
              f"prespecified ≤5-point boundary. CF's drop is {100*quality['CF']['cap_drop']:.6f} points, "
              f"{100*(quality['CF']['cap_drop']-.05):.6f} points above it (two extra incorrect CAP choices out of 2,400 "
              "relative to the 5-point boundary). The formal CF engineering screen therefore fails slightly. "
              "This is a reported quality limitation, not a reason to discard episodes, change parameters, or "
              "rerun selection. Formal rechecks do not retroactively alter the passing independent core gate.", "",
              "## Content counterfactual and matching limits", "",
              "For each episode, the physical original donor candidate r0 and replacement candidate r1 stay "
              "fixed while computing Q=z(r1)−z(r0). C_content = Q_CF−Q_K*. Recipient question hashes must match "
              "between the paired arms. This tests sensitivity to which content the donor carries rather than "
              "a change in the meaning label assigned to an option.", ""]
    rows = []
    for kind, c in frozen["content_Kstar"].items():
        rows.append([kind, c["n"], c["n_missing"], f(c["mean"]), f(c["lb95_one_sided"]), c["pass"]])
    lines += table(["Content", "Paired N", "Missing", "Mean (nats)", "One-sided 95% lower bound", "Lower bound >0"], rows)
    lines += ["These are the prespecified formal content checks, using 10,000 episode-bootstrap draws and seed 0. "
              "They are not extra members of either two-sided contrast family. Because K*=K1, no additional "
              "distinct CF-w1 arm was needed. The small formal CF CAP exceedance above limits the manipulation-quality interpretation.", "",
              f"The independent 80-episode **core validity gate passed**, but matching and independent route "
              f"validation were false. STATIC was already unmatched in its 40-episode matching pilot. In the formal "
              f"sample, K1's rule-access gain is {f(quality['K1']['acc_increment'])} nats and STATIC's is "
              f"{f(quality['STATIC']['acc_increment'])}; the absolute gap is {f(limits['formal_access_gap'])}, "
              f"or {pct(limits['formal_relative_access_gap'])} of the K1 gain, exceeding the 25% matching tolerance. "
              "The K1−STATIC effect remains a valid observed contrast between the selected interventions, but "
              "does not identify a route effect at equal access.", "",
              "## Interpretation and limitations", "",
              "- Supported here: increased assigned-rule claiming with the internal-memory link; a positive "
              "kept-versus-cut assigned-rule contrast; and a source-header effect on current-rule adoption.",
              "- Scope limits: unequal-access STATIC and text comparisons do not isolate route at matched "
              "strength. The RF code-word secondary metric shifts negatively, whereas RF current-rule adoption "
              "remains above C0. Untagged text does not produce assigned-rule donor choices in these data.",
              "- Capability/format checks are manipulation-quality diagnostics, not a guarantee of otherwise "
              "unchanged behavior. K* lies on the formal CAP boundary and CF narrowly exceeds it.",
              "- These effects describe one additional pinned checkpoint, one task/material set, and forced-choice "
              "readouts. They do not establish consciousness, subjective experience, a general law of LLMs, or "
              "a complete mechanism. No new self-report, third-person, or two-way/live-loop replication was performed.",
              "- Qwen and Llama episodes are not pooled. Raw logit magnitudes across models are not a calibrated "
              "common scale; cross-model claims should concern specific patterns and boundaries rather than "
              "equating effect magnitudes.", "",
              "## Figure", "",
              "![Behavioral choices and frozen contrasts](formal_overview.png)", "",
              "A: donor choices on the three self questions for the six non-CF conditions; descriptive pointwise "
              "95% episode-bootstrap intervals (600 episodes, two orderings each). A zero-width interval at zero "
              "is the empirical bootstrap boundary, not proof of a population rate of zero. CF is included in all "
              "tables and content checks. B: all nine prespecified logit contrasts with pointwise 95% episode-bootstrap "
              "intervals; Holm p-values are reported separately above. † denotes the unmatched STATIC comparison. "
              "[Vector PDF](formal_overview.pdf).", ""]
    return "\n".join(lines)


def plot(summary: dict, destination: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig, axes = plt.subplots(2, 1, figsize=(9, 9), gridspec_kw={"height_ratios": [1, 1.3]})
    fig.subplots_adjust(left=.33, right=.97, bottom=.08, top=.94, hspace=.43)
    ax = axes[0]
    roles = ROLE_ORDER[:-1]
    labels = {"C0": "No link (C0)", "K*": "KV-P kept (K*=K1)", "STATIC": "STATIC g=0.7 (unmatched)",
              "TAG": "Tagged text", "UNTAG": "Untagged text", "RF": "KV-P cut (RF)"}
    for offset, qid, label, color, marker in zip((-.2, 0, .2), ("START", "NOW", "WORD"),
            ("Assigned rule", "Current rule", "Code word"), ("#245882", "#b56828", "#2c8179"), ("o", "s", "^")):
        means = np.array([summary["arms"][r]["choices"][qid]["partner_rate"] for r in roles]) * 100
        intervals = np.array([summary["arms"][r]["choices"][qid]["partner_ci95"] for r in roles]) * 100
        ax.errorbar(means, np.arange(len(roles)) + offset, xerr=np.vstack((means-intervals[:,0], intervals[:,1]-means)),
                    fmt=marker, color=color, markersize=5, capsize=2, lw=1, label=label)
    ax.set(yticks=range(len(roles)), yticklabels=[labels[r] for r in roles], xlim=(-3, 103),
           xticks=[0, 25, 50, 75, 100], xlabel="Donor choices on the self question (%)")
    ax.invert_yaxis()
    ax.set_title("A  Behavior: 600 episodes, two orderings each", loc="left", fontweight="bold", fontsize=11)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    ax.grid(axis="x", color=".9", linewidth=.6)
    ax = axes[1]
    rows = summary["recomputed_frozen_output"]["families"]["primary"] + summary["recomputed_frozen_output"]["families"]["secondary"]
    labels = []
    for i, row in enumerate(rows):
        color = "#245882" if i < 5 else "#b56828" if row["mean"] < 0 else "#2c8179"
        ax.errorbar(row["mean"], i, xerr=[[row["mean"]-row["ci95_lo"]], [row["ci95_hi"]-row["mean"]]],
                    fmt="o", color=color, markersize=5, capsize=3, lw=1.2)
        metric = {"M": "Assigned", "M_NOW": "Current", "M_WORD": "Word"}[row["metric"]]
        labels.append(f"{metric}: {row['role1']} − {row['role2']}" + (" †" if row["role2"] == "STATIC" else ""))
    ax.set(yticks=range(len(rows)), yticklabels=labels, xlabel="Paired Robin-subtracted logit difference (nats)")
    ax.invert_yaxis()
    ax.axvline(0, color=".4", lw=.8)
    ax.axhline(4.5, color=".8", lw=.8, linestyle="--")
    ax.grid(axis="x", color=".92", linewidth=.6)
    ax.set_title("B  Five primary and four secondary contrasts", loc="left", fontweight="bold", fontsize=11)
    fig.text(.33, .015, "Intervals: 10,000 episode bootstrap draws, seed 0.  † Unmatched STATIC; no matched-route inference.",
             fontsize=8.5)
    fig.savefig(destination / "formal_overview.png", dpi=180, metadata={"Software": "report_v4_formal.py"})
    fig.savefig(destination / "formal_overview.pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    data_root = Path(os.environ.get("MB_DATA_ROOT", "/Volumes/VERBATIM SD/mind-connecting-data"))
    parser.add_argument("--run-dir", type=Path, default=data_root / "results" / RUN_ID)
    parser.add_argument("--out-dir", type=Path, default=REPO / "docs/results/v4")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    require(args.run_dir.is_dir(), "raw run unavailable; mount the SD card or supply --run-dir")
    require(not args.out_dir.resolve().is_relative_to(args.run_dir.resolve()), "derived output must not be inside the raw run")
    summary = build_summary(args.run_dir)
    if not args.check_only:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        (args.out_dir / "summary.json").write_text(json.dumps(ledger.sanitize(summary), indent=2, allow_nan=False) + "\n")
        (args.out_dir / "report.md").write_text(report(summary))
        plot(summary, args.out_dir)
    print(json.dumps({"run_id": RUN_ID, "n_episodes": N, "n_readouts": summary["n_readouts"],
                      "stored_output_comparison": summary["stored_output_comparison"],
                      "derived_files_written": not args.check_only}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
