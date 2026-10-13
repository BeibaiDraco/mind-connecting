"""Torch-free analysis of the proposed continuous v6 experiment.

Inputs are resolved records: exactly one final status per planned key, after the
runner has preserved and reconciled any retry history. This module checks ledger
and scoring consistency, not source-file hashes or the task world's derivation.
The runner must separately verify those against its immutable material manifest.
No admission/selector is implemented: its neutral input contract is not frozen.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from scipy import stats

MODELS = ("qwen3_4b_instruct_2507", "llama31_8b_instruct")
POLICIES = ("LIVE", "A_TO_B", "B_TO_A", "OFF", "FRESH")
PULSE_ARMS = ("L", "Fcut", "Rcut", "Replay")
GOAL_ARMS = ("L", "Fcut", "Replay")
GOAL_QIDS = ("action", "transfer_action", "original_goal", "latest_goal",
             "partner_beacon", "partner_goal")
KEY_FIELDS = ("model_profile", "episode_id", "kind", "policy", "checkpoint",
              "arm", "version", "round_id", "side", "qid")
PRIMARY = tuple(f"pulse{cp}_{name}" for cp in (2, 5)
                for name in ("forward", "return", "replay", "chain_quality")) + (
                    "goal_cross", "goal_return", "live_minus_fresh")
SECONDARY = ("goal_cross_latest_error", "goal_return_latest_error")
Key = tuple[Any, ...]
Record = Mapping[str, Any]


def _integer(value: Any, choices: Iterable[int], name: str) -> int:
    if type(value) is not int or value not in choices:
        raise ValueError(f"{name} must be one of {tuple(choices)}")
    return value


def _choice(value: Any) -> int | None:
    return None if value is None else _integer(value, range(4), "semantic choice")


def signed_choice(choice: int | None, old: int, new: int) -> float:
    """Fixed physical candidates; invalid and unrelated responses score zero."""
    _choice(choice)
    _integer(old, range(4), "old candidate")
    _integer(new, range(4), "new candidate")
    if old == new:
        raise ValueError("old and new candidates must differ")
    return float(choice == new) - float(choice == old)


def quality_score(choice: int | None, old: int, new: int) -> float:
    signed_choice(choice, old, new)
    return 1.0 if choice == new else 0.0 if choice in (None, old) else -0.5


def record_key(record: Record) -> Key:
    try:
        return tuple(record[field] for field in KEY_FIELDS)
    except KeyError as exc:
        raise ValueError(f"missing key field: {exc.args[0]}") from exc


def _key(model: str, episode: str, kind: str, cp: int, arm: str,
         version: int, round_id: int, side: int, qid: str = "action") -> Key:
    policy = arm if kind in ("natural", "text") else "LIVE"
    return (model, episode, kind, policy, cp, arm, version, round_id, side, qid)


def expected_keys(episode_id: str, model_profile: str, *, text: bool = False) -> set[Key]:
    """328 records per base episode; 24 additional records for declared text cases."""
    result = {_key(model_profile, episode_id, "natural", 0, policy, 1, r, side, qid)
              for policy in POLICIES for r in range(1, 7) for side in (0, 1)
              for qid in ("action", "partner_beacon")}
    result.update(_key(model_profile, episode_id, "pulse", cp, arm, version, r, side)
                  for cp in (2, 5) for arm in PULSE_ARMS for version in (0, 1)
                  for r in (cp, cp + 1) for side in (0, 1))
    result.update(_key(model_profile, episode_id, "goal", cp, arm, version, cp, side, qid)
                  for cp in (3, 6) for arm in GOAL_ARMS for version in (0, 1)
                  for side in (0, 1) for qid in GOAL_QIDS)
    if text:
        result.update(_key(model_profile, episode_id, "text", 0, "TEXT", 1, r, side, qid)
                      for r in range(1, 7) for side in (0, 1)
                      for qid in ("action", "partner_beacon"))
    return result


def _episode_lists(value: Mapping[str, Sequence[str]]) -> dict[str, tuple[str, ...]]:
    if not isinstance(value, Mapping) or set(value) - set(MODELS):
        raise ValueError("expected episode lists use only the two planned model profiles")
    result = {}
    for model in MODELS:
        items = value.get(model, ())
        if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
            raise ValueError("episode IDs must be an explicit sequence")
        if any(not isinstance(item, str) or not item for item in items):
            raise ValueError("episode IDs must be nonempty strings")
        if len(set(items)) != len(items):
            raise ValueError("duplicate expected episode ID")
        result[model] = tuple(items)
    return result


def _finite_tree(value: Any) -> None:
    if isinstance(value, (float, np.floating)) and not math.isfinite(value):
        raise ValueError("nonfinite record field")
    if isinstance(value, Mapping):
        for child in value.values():
            _finite_tree(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _finite_tree(child)


def _fixed(table: dict, key: tuple, value: Any, label: str) -> None:
    if key in table and table[key] != value:
        raise ValueError(f"contradictory {label}")
    table[key] = value


def _native_choice_metadata(row: Record) -> None:
    fields = {"top_token", "token_ids", "candidate_map", "legal_logits", "legal_mass", "top_probability"}
    if not fields.intersection(row):
        return
    if not fields <= row.keys():
        raise ValueError("incomplete native choice metadata")
    ids, candidates, logits = row["token_ids"], row["candidate_map"], row["legal_logits"]
    if not all(isinstance(x, (list, tuple)) and len(x) == 4 for x in (ids, candidates, logits)):
        raise ValueError("native choices require four IDs, candidates and logits")
    if any(type(token) is not int or token < 0 for token in ids) or len(set(ids)) != 4:
        raise ValueError("native choice IDs must be four distinct nonnegative integers")
    if any(type(c) is not int for c in candidates) or sorted(candidates) != list(range(4)):
        raise ValueError("native candidate map must be a four-choice permutation")
    if type(row["top_token"]) is not int or row["top_token"] < 0:
        raise ValueError("native top token must be a nonnegative integer")
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in logits):
        raise ValueError("native legal logits must be finite numbers")
    for name in ("legal_mass", "top_probability"):
        value = row[name]
        upper = 1.000001 if name == "legal_mass" else 1.0
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= upper:
            raise ValueError("native probabilities outside producer's numerical tolerance")
    semantic = candidates[ids.index(row["top_token"])] if row["top_token"] in ids else None
    if row["status"] == "ok" and row["choice"] != semantic:
        raise ValueError("semantic choice disagrees with actual native top token")
    # Native BF16 greedy choice need not equal an argmax after FP32 score recomputation.


@dataclass(frozen=True)
class ValidatedLedger:
    records: dict[Key, Record]
    expected: frozenset[Key]
    episodes: dict[str, tuple[str, ...]]
    early_focal: dict[tuple[str, str], int]

    @property
    def complete(self) -> bool:
        return self.expected == self.records.keys() and all(
            row["status"] == "ok" for row in self.records.values())


def _validated_ledger(records: Iterable[Record], expected_episodes: Mapping[str, Sequence[str]],
                      *, text_episodes: Mapping[str, Sequence[str]] | None = None) -> ValidatedLedger:
    """Reject malformed/duplicate/contradictory rows; retain missingness explicitly."""
    episodes = _episode_lists(expected_episodes)
    texts = _episode_lists(text_episodes or {})
    if any(set(texts[m]) - set(episodes[m]) for m in MODELS):
        raise ValueError("text episodes must be a predeclared subset of base episodes")
    expected = frozenset(key for m in MODELS for ep in episodes[m]
                         for key in expected_keys(ep, m, text=ep in texts[m]))
    indexed: dict[Key, Record] = {}
    focals: dict[tuple[str, str], int] = {}
    candidates: dict[tuple, tuple[int, int]] = {}
    truths: dict[tuple, int] = {}
    for row in records:
        if not isinstance(row, Mapping):
            raise ValueError("record must be a mapping")
        _finite_tree(row)
        key = record_key(row)
        for name in ("checkpoint", "version", "round_id", "side"):
            if type(row[name]) is not int:
                raise ValueError(f"{name} must be an integer, not a boolean or float")
        for name in ("model_profile", "episode_id", "kind", "policy", "arm", "qid"):
            if not isinstance(row[name], str):
                raise ValueError(f"{name} must be a string")
        if key not in expected:
            raise ValueError(f"unexpected record key: {key}")
        if key in indexed:
            raise ValueError(f"duplicate resolved record key: {key}")
        if not {"choice", "correct", "correct_choice", "status"} <= row.keys():
            raise ValueError("record lacks choice/correct/correct_choice/status")
        choice = _choice(row["choice"])
        correct_choice = _integer(row["correct_choice"], range(4), "correct_choice")
        if row["status"] == "ok":
            if type(row["correct"]) is not bool or row["correct"] != (choice == correct_choice):
                raise ValueError("correct disagrees with actual semantic choice and truth")
        elif row["status"] == "technical_failure":
            if choice is not None or row["correct"] is not None and row["correct"] is not False:
                raise ValueError("technical failure cannot carry a scored response")
        else:
            raise ValueError("unknown record status")
        _native_choice_metadata(row)
        model, ep, kind, _, cp, _, version, r, side, qid = key
        if kind in ("pulse", "goal"):
            focal = _integer(row.get("focal_side"), (0, 1), "focal_side")
            _fixed(focals, (model, ep), focal if cp in (2, 3) else 1 - focal,
                   "early/late physical focal roles")
            is_target = kind == "goal" and qid == "transfer_action" or (
                kind == "pulse" and (r, side) in ((cp, 1 - focal), (cp + 1, focal)))
            if is_target:
                old = _integer(row.get("old_candidate"), range(4), "old candidate")
                new = _integer(row.get("new_candidate"), range(4), "new candidate")
                signed_choice(choice, old, new)
                candidate_key = (model, ep, kind, cp, r, side if kind == "pulse" else None, qid)
                _fixed(candidates, candidate_key, (old, new), "fixed physical candidates")
                if kind == "pulse" and r == cp or kind == "goal" and side == focal:
                    if correct_choice != (old, new)[version]:
                        raise ValueError("fixed-world correct choice disagrees with candidate/version")
                if kind == "goal" and side != focal and correct_choice in (old, new):
                    raise ValueError("partner's own goal must differ from both focal candidate goals")
            if kind == "goal":
                # Physical facts and authorized assignments do not vary with the path intervention.
                stable = qid in ("original_goal", "partner_beacon") or (
                    qid in ("action", "transfer_action", "latest_goal") and side != focal) or (
                    qid == "partner_goal" and side == focal)
                invariant_version = None if stable else version
                _fixed(truths, (model, ep, cp, side, qid, invariant_version), correct_choice,
                       "goal-probe truth across arms/versions")
                if qid == "original_goal":
                    _fixed(truths, (model, ep, side, "original_goal"), correct_choice,
                           "original assignment across checkpoints")
        indexed[key] = dict(row)
    for model, ep in focals:
        for cp in (3, 6):
            focal = focals[(model, ep)] if cp == 3 else 1 - focals[(model, ep)]
            for version in (0, 1):
                own = truths.get((model, ep, cp, focal, "latest_goal", version))
                peer = truths.get((model, ep, cp, 1 - focal, "partner_goal", version))
                other = truths.get((model, ep, cp, 1 - focal, "latest_goal", None))
                mirrored = truths.get((model, ep, cp, focal, "partner_goal", None))
                if own is not None and peer is not None and own != peer or (
                        other is not None and mirrored is not None and other != mirrored):
                    raise ValueError("contradictory own/partner latest assignment truth")
                if own is not None and other is not None and own == other:
                    raise ValueError("goal-probe authorized goals must differ")
            old = truths.get((model, ep, cp, focal, "latest_goal", 0))
            new = truths.get((model, ep, cp, focal, "latest_goal", 1))
            if old is not None and new is not None and old == new:
                raise ValueError("goal probe must change focal assignment")
    return ValidatedLedger(indexed, expected, episodes, focals)


def _completeness(ledger: ValidatedLedger) -> dict:
    missing = ledger.expected - ledger.records.keys()
    failed = sum(row["status"] == "technical_failure" for row in ledger.records.values())
    complete = bool(ledger.expected) and ledger.complete
    return {"expected_records": len(ledger.expected), "observed_records": len(ledger.records),
            "ok_records": len(ledger.records) - failed, "missing_records": len(missing),
            "technical_failures": failed, "complete": complete, "consumable": complete,
            "ledger_complete": complete}


def validate_records(records: Iterable[Record], expected_episodes: Mapping[str, Sequence[str]],
                     *, text_episodes: Mapping[str, Sequence[str]] | None = None) -> dict:
    """JSON-safe audit; callers must check ``complete``, not merely absence of errors.

    ``consumable`` here certifies this declared ledger only. Smoke/source/material
    identity and prospective sample-size checks belong to the calling runner.
    """
    return _completeness(_validated_ledger(records, expected_episodes, text_episodes=text_episodes))


def _combine(values: Sequence[float | None], weights: Sequence[float]) -> float | None:
    if any(value is None for value in values):
        return None
    # Sequential sums of ten +0.1 then ten -0.1 can create a spurious constant
    # nonzero contrast, which a zero-variance t test would otherwise reject.
    return float(math.fsum(value * weight for value, weight in zip(values, weights)))


def episode_scores(ledger: ValidatedLedger, model_profile: str) -> dict:
    """One score per declared base episode, never one sample per side/round."""
    if model_profile not in MODELS:
        raise ValueError("unknown model profile")
    primary = {name: [] for name in PRIMARY}
    secondary = {name: [] for name in SECONDARY}
    components = {f"pulse{cp}_{name}": [] for cp in (2, 5)
                  for name in ("Q_J", "Q_I") + tuple(f"{arm}_Delta_{side}" for arm in PULSE_ARMS
                                                    for side in ("J", "I"))}
    for ep in ledger.episodes[model_profile]:
        def get(kind: str, cp: int, arm: str, version: int, r: int, side: int,
                qid: str = "action", score: str = "signed") -> float | None:
            row = ledger.records.get(_key(model_profile, ep, kind, cp, arm, version, r, side, qid))
            if row is None or row["status"] != "ok":
                return None
            if score == "correct":
                return float(row["correct"])
            if score == "error":
                return float(not row["correct"])
            function = quality_score if score == "quality" else signed_choice
            return function(row["choice"], row["old_candidate"], row["new_candidate"])

        def delta(kind: str, cp: int, arm: str, r: int, side: int,
                  qid: str = "action", score: str = "signed") -> float | None:
            weights = (1.0, -1.0) if score == "error" else (0.5, -0.5)
            return _combine([get(kind, cp, arm, v, r, side, qid, score) for v in (1, 0)], weights)

        early = ledger.early_focal.get((model_profile, ep))
        for cp in (2, 5):
            i = early if cp == 2 else None if early is None else 1 - early
            if i is None:
                for name in PRIMARY[:8]:
                    if name.startswith(f"pulse{cp}_"):
                        primary[name].append(None)
                for name in components:
                    if name.startswith(f"pulse{cp}_"):
                        components[name].append(None)
                continue
            j = 1 - i
            for name, control, r, side in (("forward", "Fcut", cp, j),
                                           ("return", "Rcut", cp + 1, i),
                                           ("replay", "Replay", cp + 1, i)):
                primary[f"pulse{cp}_{name}"].append(_combine([
                    delta("pulse", cp, "L", r, side), delta("pulse", cp, control, r, side)], (1, -1)))
            qs = [get("pulse", cp, "L", 1, r, side, score="quality")
                  for r, side in ((cp, j), (cp + 1, i))]
            primary[f"pulse{cp}_chain_quality"].append(None if None in qs else min(qs))
            for side_name, value in zip(("J", "I"), qs):
                components[f"pulse{cp}_Q_{side_name}"].append(value)
            for arm in PULSE_ARMS:
                components[f"pulse{cp}_{arm}_Delta_J"].append(delta("pulse", cp, arm, cp, j))
                components[f"pulse{cp}_{arm}_Delta_I"].append(delta("pulse", cp, arm, cp + 1, i))
        for name, control, target in (("goal_cross", "Fcut", "J"),
                                      ("goal_return", "Replay", "I")):
            effects, errors = [], []
            for cp in (3, 6):
                i = early if cp == 3 else None if early is None else 1 - early
                side = None if i is None else i if target == "I" else 1 - i
                if side is None:
                    effects.append(None)
                    errors.append(None)
                    continue
                effects.append(_combine([delta("goal", cp, arm, cp, side, "transfer_action")
                                         for arm in ("L", control)], (1, -1)))
                errors.append(_combine([delta("goal", cp, arm, cp, side, "latest_goal", "error")
                                        for arm in ("L", control)], (1, -1)))
            primary[name].append(_combine(effects, (.5, .5)))
            secondary[f"{name}_latest_error"].append(_combine(errors, (.5, .5)))
        natural = [get("natural", 0, policy, 1, r, side, score="correct")
                   for policy in ("LIVE", "FRESH") for r in range(2, 7) for side in (0, 1)]
        primary["live_minus_fresh"].append(_combine(natural, (.1,) * 10 + (-.1,) * 10))
    return {"episode_ids": list(ledger.episodes[model_profile]), "primary": primary,
            "secondary": secondary, "components": dict(components)}


def test_scores(values: Sequence[float | None], *, n_boot: int = 10_000, seed: int = 0) -> dict:
    """Two-sided one-sample t test and paired episode percentile interval.

    A missing required component makes the entire contrast unavailable, p=1.
    A constant zero contrast has p=1; a constant nonzero contrast has limiting
    t-test p=0. The zero-variance case is explicitly reported, never NaN-imputed.
    """
    if type(n_boot) is not int or n_boot < 1 or type(seed) is not int or seed < 0:
        raise ValueError("positive bootstrap count and nonnegative integer seed required")
    if any(value is not None and (isinstance(value, bool) or not math.isfinite(value)) for value in values):
        raise ValueError("contrast scores must be finite real numbers or missing")
    available = len(values) >= 2 and None not in values
    result = {"available": available, "n_expected": len(values),
              "n_complete": sum(value is not None for value in values), "n": None,
              "mean": None, "sd": None, "se": None, "t": None, "ci95": None,
              "p_two_sided": 1.0, "zero_variance": None}
    if not available:
        result["reason"] = "missing_required_episode" if None in values else "fewer_than_two_episodes"
        return result
    x = np.asarray(values, dtype=np.float64)
    mean, sd = float(x.mean()), float(x.std(ddof=1))
    se = sd / math.sqrt(len(x))
    t = mean / se if se else None
    p = float(2 * stats.t.sf(abs(t), len(x) - 1)) if se else float(mean == 0)
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for start in range(0, n_boot, 512):
        count = min(512, n_boot - start)
        boots[start:start + count] = x[rng.integers(0, len(x), size=(count, len(x)))].mean(axis=1)
    result.update(n=len(x), mean=mean, sd=sd, se=se, t=t,
                  ci95=np.quantile(boots, [.025, .975]).tolist(), p_two_sided=p,
                  zero_variance=sd == 0)
    return result


def holm_fixed(pvalues: Sequence[float], family_size: int) -> list[float]:
    """Keep unavailable tests as p=1 in the full, fixed-size family."""
    if len(pvalues) != family_size or any(
            isinstance(p, bool) or not math.isfinite(p) or not 0 <= p <= 1 for p in pvalues):
        raise ValueError("Holm requires the complete fixed family of finite p-values")
    out, running = [1.0] * family_size, 0.0
    for rank, index in enumerate(sorted(range(family_size), key=lambda k: (pvalues[k], k))):
        running = max(running, min(1.0, (family_size - rank) * pvalues[index]))
        out[index] = running
    return out


NEUTRAL_METRICS = frozenset({"task_accuracy", "assignment_accuracy", "cap_accuracy",
                            "access_accuracy", "label_mass"})
NEUTRAL_METRICS = NEUTRAL_METRICS | {f"reference_{name}" for name in NEUTRAL_METRICS}


def neutral_gate_readiness(stage: str, inputs: Mapping[str, Any] | None = None) -> dict:
    """Check neutral-vector boundaries, but never pretend an unresolved gate passed.

    Optional inputs have exactly ``episode_ids`` and ``scores``. Every score is a
    whitelisted metric mapping string physical-side IDs ``"0"``/``"1"`` to paired
    [0,1] episode vectors in the declared order. There is deliberately no override
    that enables a selector before the material/schedule/precision contract exists.
    """
    if stage not in ("baseline", "calibration", "validity"):
        raise ValueError("unknown neutral admission stage")
    n, metrics = None, []
    if inputs is not None:
        if not isinstance(inputs, Mapping) or set(inputs) != {"episode_ids", "scores"}:
            raise ValueError("neutral inputs require only episode_ids and scores")
        ids = _episode_lists({MODELS[0]: inputs["episode_ids"]})[MODELS[0]]
        if not ids:
            raise ValueError("neutral inputs require a nonempty explicit episode list")
        scores = inputs["scores"]
        if not isinstance(scores, Mapping) or not scores or set(scores) - NEUTRAL_METRICS:
            raise ValueError("nonneutral or unknown metric: selectors cannot read goal/attribution outcomes")
        for metric, sides in scores.items():
            if not isinstance(sides, Mapping) or set(sides) != {"0", "1"}:
                raise ValueError("neutral scores require both named physical sides")
            for values in sides.values():
                if not isinstance(values, (list, tuple)) or len(values) != len(ids) or any(
                        isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or not 0 <= value <= 1 for value in values):
                    raise ValueError("neutral vectors must be complete, paired, finite and in [0,1]")
        n, metrics = len(ids), sorted(scores)
    unresolved = ["neutral material manifest and disjoint split",
                  "full-six-round neutral collection/readout schedule",
                  "ratified physical-side/subscale scoring and admission contract"]
    if stage == "calibration":
        unresolved.append("exact gain-pass predicate and calibration precision rule")
    return {"stage": stage, "ready": False, "consumable": False,
            "gate": None, "selected_gain": None, "reason": "neutral_contract_unratified",
            "input_validated": inputs is not None, "n_episodes": n, "metrics": metrics,
            "unresolved": unresolved}


def _descriptive(ledger: ValidatedLedger) -> list[dict]:
    groups: dict[tuple, list[Key]] = defaultdict(list)
    for key in sorted(ledger.expected):
        groups[key[:1] + key[2:]].append(key)
    output = []
    for group, keys in sorted(groups.items()):
        rows = [ledger.records[k] for k in keys if k in ledger.records and ledger.records[k]["status"] == "ok"]
        counts = Counter("invalid" if row["choice"] is None else str(row["choice"]) for row in rows)
        complete = len(rows) == len(keys)
        output.append({**dict(zip(("model_profile",) + KEY_FIELDS[2:], group)),
                       "n_expected": len(keys), "n_ok": len(rows), "complete": complete,
                       "choice_counts": {label: counts[label] for label in ("0", "1", "2", "3", "invalid")},
                       "correct_count": sum(row["correct"] for row in rows),
                       "accuracy": sum(row["correct"] for row in rows) / len(keys) if complete else None,
                       "invalid_rate": counts["invalid"] / len(keys) if complete else None})
    return output


def analyze(records: Iterable[Record], expected_episodes: Mapping[str, Sequence[str]], *,
            text_episodes: Mapping[str, Sequence[str]] | None = None,
            n_boot: int = 10_000, seed: int = 0) -> dict:
    """Analyze both model slots, retaining all 22 + 4 tests even when unavailable."""
    ledger = _validated_ledger(records, expected_episodes, text_episodes=text_episodes)
    synthetic = any(row.get("scientific_data") is False or
                    str(row.get("backend_kind", "")).startswith("synthetic")
                    for row in ledger.records.values())
    scores = {model: episode_scores(ledger, model) for model in MODELS}
    families = {}
    for family, names, size in (("primary", PRIMARY, 22), ("secondary", SECONDARY, 4)):
        items = [{"model_profile": model, "endpoint": name,
                  **test_scores(scores[model][family][name], n_boot=n_boot, seed=seed)}
                 for model in MODELS for name in names]
        for item, p in zip(items, holm_fixed([item["p_two_sided"] for item in items], size)):
            item.update(p_holm=p, reject_two_sided_05=bool(item["available"] and p <= .05))
        families[family] = items
    return {"analysis_version": "v6-continuous-draft-1", "statistical_unit": "base_episode",
            "synthetic_input": synthetic, "scientific_source_verified": False,
            "source_verification_note": "This scorer does not attest material/source identity or model execution.",
            "consumable": not synthetic and ledger.complete and all(len(ledger.episodes[m]) >= 2 for m in MODELS),
            "completeness": _completeness(ledger),
            "inference": {"bootstrap_draws": n_boot, "bootstrap_seed": seed,
                          "primary_family_size": 22, "secondary_family_size": 4,
                          "intervals": "pointwise 95% episode-percentile, not simultaneous",
                          "missingness": "no complete-case confirmatory analysis"},
            **families, "episode_scores": scores, "descriptive": _descriptive(ledger),
            "sustained_response": {model: all(item["available"] and item["mean"] > 0
                                               and item["p_holm"] <= .05
                                               for item in families["primary"]
                                               if item["model_profile"] == model
                                               and item["endpoint"].startswith("pulse")) for model in MODELS}}
