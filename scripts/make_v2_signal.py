"""Write the protocol-v2 signal-pilot configs from the strength / matching pilot outputs (PROTOCOL_V2 §3).

    python scripts/make_v2_signal.py sig1 --static-r RUN --cal CAL_L24
    python scripts/make_v2_signal.py sig2 --kv RUN --static-k RUN --cal CAL_L24
    python scripts/make_v2_signal.py sigE --kv RUN --cal-bal CAL_L24_BALANCED

RUN arguments are local copies of the pilot run directories; CAL arguments are the calibration
file paths as seen on the GPU machine. Each config gets a ``signal`` post step whose studies
list the comparisons of PROTOCOL_V2 §2 (the first comparison of each study decides go/no-go).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
QIDS = ["NOW", "NOW_R", "START", "START_R", "WORD", "WORD_R", "ACC_RULE", "ACC_WORD", "CAP0", "CAP1", "U_CLOSED"]
N_SIGNAL = 80
R02, R03, T03 = "ONE/L24/raw/g0.2/FULL", "ONE/L24/raw/g0.3/FULL", "TWO/L24/raw/g0.3/FULL"


def _load(path: Path) -> dict:
    doc = json.loads(path.read_text())
    if not doc.get("consumable"):
        raise SystemExit(f"{path} is not consumable (smoke or incomplete)")
    return doc


def static_match(run_dir: Path, target: str) -> dict:
    m = _load(run_dir / "static_match.json")["matches"].get(target)
    if not m:
        raise SystemExit(f"no STATIC match for {target} in {run_dir.name}")
    return m


def kv_selection(run_dir: Path) -> dict:
    doc = _load(run_dir / "strength_selection.json")
    if doc.get("strength_gate") != "pass":
        raise SystemExit(f"{run_dir.name}: the KV strength gate was not met")
    return doc["selection"]


def kv_arm(sel: dict, condition: str, **extra) -> dict:
    return {"condition": condition, "interface": "kv", "kv_scope": sel["kv_scope"], "gain": float(sel["gain"]),
            **extra}


def kv_name(sel: dict, condition: str) -> str:
    return f"{condition}/KV-{sel['kv_scope']}/w{float(sel['gain']):g}/FULL"


def config(stage: str, split: str, arms: list[dict], cal: dict, studies: dict, post: list[str], **extra) -> dict:
    return {"stage": stage, "tag": "signal", "split": split, "n_episodes": N_SIGNAL, "seed": 0, "arms": arms,
            "qids": QIDS, "episodes_per_batch": 40, "max_rows": 256, "calibration": cal, "post": post,
            "params": {"studies": studies, "min_effect": 0.3}, **extra}


def sig1(args) -> tuple[dict, str]:
    m = static_match(args.static_r, R02)
    static = {"condition": "STATIC", "layer": 24, "gain": m["gain"]}
    arms = [{"condition": "C0", "layer": 24}, {"condition": "ONE", "layer": 24, "gain": 0.2},
            {"condition": "ONE", "layer": 24, "gain": 0.3}, {"condition": "TWO", "layer": 24, "gain": 0.3}, static,
            {"condition": "LANG_TAG"}, {"condition": "LANG_UNTAG"}, {"condition": "LANG_SELF"},
            {"condition": "LANG_STRANGER"}]
    studies = {"B_R": [[T03, R03, "M_NOW", "+"]],
               "A_R": [[R02, m["static_arm"], "M", "0"]],
               "C": [["LANG_UNTAG/FULL", "LANG_TAG/FULL", "M_NOW", "+"], ["LANG_SELF/FULL", "LANG_UNTAG/FULL", "M_NOW", "+"],
                     ["LANG_STRANGER/FULL", "LANG_TAG/FULL", "M_NOW", "0"]]}
    note = f"STATIC matched to {R02}: {m}"
    return config("v2_sig1", "v2_sig1", arms, {24: args.cal}, studies, ["signal"]), note


def live_loop_setting(run_dir: Path) -> dict:
    """PROTOCOL_V2 §1 amendment: study B needs a scope with a mutual loop (C or ALL); take the
    strongest eligible point among those groups (it may not meet the strength standard)."""
    groups = _load(run_dir / "strength_selection.json")["groups"]
    tops = [g for key, g in groups.items() if g and key.split("|")[2] in ("C", "ALL")]
    if not tops:
        raise SystemExit("no eligible live-loop KV setting")
    return max(tops, key=lambda g: (g["acc_increment"], -g["gain"]))


def sig2(args) -> tuple[dict, str]:
    sel = kv_selection(args.kv)
    live = live_loop_setting(args.kv)
    m = static_match(args.static_k, kv_name(sel, "ONE"))
    one, cf = kv_name(sel, "ONE"), kv_name(sel, "CF")
    b_one, b_two = kv_name(live, "ONE"), kv_name(live, "TWO")
    arms = [{"condition": "C0", "layer": 24}, kv_arm(sel, "ONE"), kv_arm(sel, "CF"),
            {"condition": "STATIC", "layer": 24, "gain": m["gain"]}, kv_arm(live, "ONE"), kv_arm(live, "TWO"),
            {"condition": "LANG_UNTAG"}]
    studies = {"D": [[one, "C0/FULL", "M", "0"], [one, "C0/FULL", "M_NOW", "0"]],
               "B_K": [[b_two, b_one, "M_NOW", "+"]],
               "A_K": [[one, m["static_arm"], "M", "0"]]}
    note = (f"K* {sel['arm']} (ACC {sel['acc_increment']:.2f}, hits {sel['partner_rate']:.2f}); live-loop setting for B "
            f"{live['arm']} (ACC {live['acc_increment']:.2f}, hits {live['partner_rate']:.2f}); STATIC match {m}; CF {cf}")
    return config("v2_sig2", "v2_sig2", arms, {24: args.cal}, studies, ["signal", "pilot_c"]), note


def sig_e(args) -> tuple[dict, str]:
    arms = [{"condition": "C0", "layer": 24}, {"condition": "ONE", "layer": 24, "gain": 0.3}, {"condition": "LANG_UNTAG"}]
    studies = {}
    note = "no KV arm (strength gate not met): E uses R-ONE(0.3)"
    try:
        sel = kv_selection(args.kv)
        arms.insert(1, kv_arm(sel, "ONE"))
        studies["E"] = [[kv_name(sel, "ONE"), "C0/FULL", "M", "0"], [R03, "C0/FULL", "M", "0"]]
        note = f"KV selection {sel['arm']} carried over"
    except SystemExit:
        studies["E"] = [[R03, "C0/FULL", "M", "0"]]
    return config("v2_sigE", "v2_sigE", arms, {24: args.cal_bal}, studies, ["signal"], materials=args.materials), note


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["sig1", "sig2", "sigE"])
    ap.add_argument("--static-r", type=Path)
    ap.add_argument("--static-k", type=Path)
    ap.add_argument("--kv", type=Path)
    ap.add_argument("--cal")
    ap.add_argument("--cal-bal")
    ap.add_argument("--materials", default="balanced2")
    args = ap.parse_args()
    cfg, note = {"sig1": sig1, "sig2": sig2, "sigE": sig_e}[args.which](args)
    out = ROOT / "configs" / "v2" / f"{args.which}.yaml"
    out.write_text(f"# Protocol v2 {args.which} signal pilot. GENERATED by scripts/make_v2_signal.py.\n# {note}\n"
                   + yaml.safe_dump(cfg, sort_keys=False, default_flow_style=None, width=140))
    print(f"wrote {out}: {len(cfg['arms'])} arms; {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
