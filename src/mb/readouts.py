"""Pure scoring of readout records (protocol v0.5 §8).

A *record* is one question x recipient x arm x rotation, as written by the runtime:
it carries the four raw label logits, the label meanings and physical options for that
recipient, and a status. All log-ratios are logit differences in float64
(log P(a) - log P(b) = z_a - z_b), so they do not depend on how probabilities are
normalized. Metrics are computed per rotation first and averaged afterwards; missing
or non-finite inputs propagate as NaN, never as zero.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

Record = Mapping[str, object]

# (self question, partner meaning, correct meaning) and its Robin twin.
TWIN_METRICS: dict[str, tuple[tuple[str, str, str], tuple[str, str, str]]] = {
    "M": (("START", "partner", "own"), ("START_R", "partner", "robin")),
    "M_BEH": (("BEH", "partner", "own"), ("BEH_R", "partner", "robin")),
    "M_NOW": (("NOW", "partner", "own"), ("NOW_R", "partner", "robin")),
    "M_WORD": (("WORD", "partner", "own"), ("WORD_R", "partner", "robin")),
}
# Single-question log-ratios: (qid, numerator meaning, denominator meaning).
SINGLE_METRICS: dict[str, tuple[str, str, str]] = {
    "L_START": ("START", "partner", "own"),
    "L_START_R": ("START_R", "partner", "robin"),
    "L_START_N": ("START_N", "partner", "own"),
    "ACC_RULE": ("ACC_RULE", "partner", "unused"),
    "ACC_WORD": ("ACC_WORD", "partner", "distractor"),
}
ARGMAX_QIDS = ("BEH", "NOW", "START", "WORD", "U_CLOSED")
KEY_COLUMNS = ("episode_id", "recipient", "arm")


def _ok(rec: Record) -> bool:
    if rec.get("status", "ok") != "ok":
        return False
    logits = rec.get("label_logits")
    return logits is not None and len(logits) == 4 and all(math.isfinite(float(z)) for z in logits)


def logit_for(rec: Record, meaning: str) -> float:
    """Raw logit of the label whose meaning (for this recipient) is ``meaning``."""
    if not _ok(rec):
        return math.nan
    meanings = list(rec["label_meaning"])
    if meanings.count(meaning) != 1:
        raise ValueError(f"{rec.get('qid')}: meaning {meaning!r} not unique in {meanings}")
    return float(rec["label_logits"][meanings.index(meaning)])


def logit_for_option(rec: Record, option: str) -> float:
    """Raw logit of the label showing the physical option ``option`` (e.g. a rule key or word)."""
    if not _ok(rec):
        return math.nan
    options = list(rec["options"])
    if options.count(option) != 1:
        raise ValueError(f"{rec.get('qid')}: option {option!r} not unique in {options}")
    return float(rec["label_logits"][options.index(option)])


def log_ratio(rec: Record, a: str, b: str) -> float:
    return logit_for(rec, a) - logit_for(rec, b)


def label_probs(rec: Record) -> np.ndarray:
    """Softmax over the four labels (descriptive only; never used for M)."""
    if not _ok(rec):
        return np.full(4, np.nan)
    z = np.asarray(rec["label_logits"], dtype=np.float64)
    z = z - z.max()
    p = np.exp(z)
    return p / p.sum()


def argmax_meaning(rec: Record) -> str | None:
    if not _ok(rec):
        return None
    return list(rec["label_meaning"])[int(np.argmax(np.asarray(rec["label_logits"], dtype=np.float64)))]


# ---------------------------------------------------------------------------
# Per-rotation metrics and aggregation
# ---------------------------------------------------------------------------


def _index(records: Iterable[Record]) -> dict[tuple, dict[tuple[str, int | None], Record]]:
    grouped: dict[tuple, dict[tuple[str, int | None], Record]] = {}
    arm_hash: dict[str, object] = {}
    for rec in records:
        # Results whose configuration hashes differ must never be merged under one arm name.
        h = rec.get("config_hash")
        if h is not None and arm_hash.setdefault(str(rec["arm"]), h) != h:
            raise ValueError(f"arm {rec['arm']!r} mixes config hashes {arm_hash[str(rec['arm'])]} and {h}")
        key = tuple(rec[c] for c in KEY_COLUMNS)
        slot = (str(rec["qid"]), rec.get("rotation_id"))
        bucket = grouped.setdefault(key, {})
        if slot in bucket:
            raise ValueError(f"duplicate record for {key} {slot}")
        bucket[slot] = rec
    return grouped


def rotation_metrics(bucket: Mapping[tuple[str, int | None], Record], rotation: int) -> dict[str, float]:
    """All log-ratio metrics for one rotation; NaN where an input is missing or invalid."""
    def get(qid: str) -> Record | None:
        return bucket.get((qid, rotation))

    out: dict[str, float] = {}
    for name, (qid, a, b) in SINGLE_METRICS.items():
        rec = get(qid)
        out[name] = log_ratio(rec, a, b) if rec is not None else math.nan
    for name, ((q_self, a1, b1), (q_twin, a2, b2)) in TWIN_METRICS.items():
        r_self, r_twin = get(q_self), get(q_twin)
        if r_self is None or r_twin is None:
            out[name] = math.nan
        else:
            out[name] = log_ratio(r_self, a1, b1) - log_ratio(r_twin, a2, b2)
    out["M_START_N"] = out["L_START_N"] - out["L_START"]
    caps = [get(q) for q in ("CAP0", "CAP1")]
    cap_scores = [1.0 if argmax_meaning(r) == "correct" else 0.0 for r in caps if r is not None and _ok(r)]
    out["CAP_ACC"] = float(np.mean(cap_scores)) if len(cap_scores) == 2 else math.nan
    masses = [float(r["label_mass"]) for r in bucket.values()
              if r.get("rotation_id") == rotation and _ok(r) and r.get("label_mass") is not None]
    out["LABEL_MASS"] = float(np.mean(masses)) if masses else math.nan
    return out


METRIC_NAMES: tuple[str, ...] = tuple(rotation_metrics({}, 0))


@dataclass(frozen=True)
class ScoreOptions:
    rotations: Sequence[int] | None = None  # None: use every rotation present in the bucket
    require_all_rotations: bool = True


def score_records(records: Iterable[Record], options: ScoreOptions = ScoreOptions()) -> pd.DataFrame:
    """One row per (episode, recipient, arm): rotation-averaged metrics plus argmax profile."""
    rows = []
    for key, bucket in _index(records).items():
        present = sorted({rot for (_, rot) in bucket if rot is not None})
        wanted = list(options.rotations) if options.rotations is not None else present
        per_rot = [rotation_metrics(bucket, r) for r in wanted if r in present]
        row: dict[str, object] = dict(zip(KEY_COLUMNS, key))
        row["n_rotations"] = len(per_rot)
        complete = len(per_rot) == len(wanted) and len(wanted) > 0
        for name in METRIC_NAMES:
            values = np.array([m[name] for m in per_rot], dtype=np.float64)
            if options.require_all_rotations and not complete:
                row[name] = math.nan
            elif values.size == 0 or np.isnan(values).any():
                row[name] = math.nan
            else:
                row[name] = float(values.mean())
        for qid in ARGMAX_QIDS:
            probs = [label_probs(bucket[(qid, r)]) for r in wanted if (qid, r) in bucket]
            meanings = [list(bucket[(qid, r)]["label_meaning"]) for r in wanted if (qid, r) in bucket]
            row[f"argmax_{qid}"] = _pooled_argmax(probs, meanings)
        sample = next(iter(bucket.values()))
        for col in ("condition", "readout_mode", "layer", "gain", "message_form", "tau",
                    "k", "energy_mode", "config_hash", "split", "interface", "kv_scope", "kv_w_live", "materials"):
            if col in sample:
                row[col] = sample[col]
        rows.append(row)
    return pd.DataFrame(rows)


def _pooled_argmax(probs: list[np.ndarray], meanings: list[list[str]]) -> str | None:
    """Argmax of meaning-aligned label probabilities averaged over rotations."""
    if not probs or any(np.isnan(p).any() for p in probs):
        return None
    totals: dict[str, float] = {}
    for p, m in zip(probs, meanings):
        for prob, meaning in zip(p, m):
            totals[meaning] = totals.get(meaning, 0.0) + float(prob)
    return max(totals, key=totals.get)


# ---------------------------------------------------------------------------
# Content counterfactual (G2) with fixed physical candidates
# ---------------------------------------------------------------------------


WORD_QIDS = frozenset({"WORD", "WORD_R", "ACC_WORD"})


def content_cf_score(original: Iterable[Record], counterfactual: Iterable[Record], qid: str,
                     r0: str | None = None, r1: str | None = None) -> pd.DataFrame:
    """Per episode: C_content = mean_rot Q[cf] - mean_rot Q[orig], Q = z(r1) - z(r0).

    r0/r1 are physical options (rule keys or words), so the sign cannot flip when the
    donor's assignment changes. They differ per episode; by default they are read from the
    counterfactual records (``cf_r0_rule``/``cf_r1_rule``, or ``_word`` for word questions),
    and fixed values can be passed instead. The recipient's question text must be identical.
    """
    kind = "word" if qid in WORD_QIDS else "rule"
    counterfactual = [rec for rec in counterfactual if rec["qid"] == qid]
    cands: dict[str, tuple[str, str]] = {}
    for rec in counterfactual:
        pair = (r0, r1) if r0 is not None and r1 is not None else (rec.get(f"cf_r0_{kind}"), rec.get(f"cf_r1_{kind}"))
        if pair[0] is None or pair[1] is None:
            raise ValueError(f"{rec['episode_id']}: counterfactual record lacks cf_r0_{kind}/cf_r1_{kind}")
        if cands.setdefault(str(rec["episode_id"]), pair) != pair:
            raise ValueError(f"{rec['episode_id']}: inconsistent CF candidates across records")

    def per_episode(recs: Iterable[Record]) -> dict[str, dict[int, tuple[float, str]]]:
        out: dict[str, dict[int, tuple[float, str]]] = {}
        for rec in recs:
            if rec["qid"] != qid:
                continue
            ep_id = str(rec["episode_id"])
            if ep_id in cands:
                c0, c1 = cands[ep_id]
                q = logit_for_option(rec, c1) - logit_for_option(rec, c0)
            else:
                q = math.nan  # no counterfactual data for this episode: reported as missing
            out.setdefault(ep_id, {})[int(rec["rotation_id"])] = (q, str(rec.get("text_hash")))
        return out

    orig, cf = per_episode(original), per_episode(counterfactual)
    rows = []
    for ep_id in sorted(set(orig) | set(cf)):
        a, b = orig.get(ep_id, {}), cf.get(ep_id, {})
        rots = sorted(set(a) & set(b))
        for r in rots:
            if a[r][1] != b[r][1]:
                raise ValueError(f"{ep_id} rotation {r}: recipient question text differs under CF")
        complete = rots and set(a) == set(b)
        qa = np.array([a[r][0] for r in rots])
        qb = np.array([b[r][0] for r in rots])
        value = float(qb.mean() - qa.mean()) if complete and not (np.isnan(qa).any() or np.isnan(qb).any()) else math.nan
        rows.append({"episode_id": ep_id, "qid": qid, "C_content": value, "n_rotations": len(rots)})
    return pd.DataFrame(rows)
