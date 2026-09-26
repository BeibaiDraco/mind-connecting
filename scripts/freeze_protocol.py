"""Freeze a protocol version: SHA256 manifest of the protocol, code and formal configs (AGENTS.md §4).

    python scripts/freeze_protocol.py --write    # after committing the formal configs
    python scripts/freeze_protocol.py --verify   # before every formal stage (run_formal.sh)

``--write`` creates docs/protocol/FREEZE_protocol_v1.txt (refuses to overwrite) with the commit it
was made at; commit that file and tag it ``protocol-v1``. ``--verify`` recomputes every hash and
exits non-zero on any difference, so the formal stages only ever run the frozen files.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "docs" / "protocol" / "FREEZE_protocol_v1.txt"
FORMAL_CONFIGS = ("main", "main_diag", "ext_layers", "ext_masks")
VERSION = "v1"
# Later versions (--version v2 / v3): protocol text, generator and driver scripts; configs in configs/<version>/.
LATER = {
    "v2": {"docs": ("PROTOCOL_V2.md",), "glob": "v2_*.yaml",
           "scripts": ("make_v2_main.py", "make_v2_signal.py", "run_formal_v2.sh", "freeze_protocol.py")},
    "v3": {"docs": ("PROTOCOL_V3.md",), "glob": "v3_confirm*.yaml",
           "scripts": ("make_v3_confirm.py", "run_chain.sh", "freeze_protocol.py")},
}


def configure(version: str) -> None:
    global FREEZE, FORMAL_CONFIGS, VERSION
    VERSION = version
    FREEZE = ROOT / "docs" / "protocol" / f"FREEZE_protocol_{version}.txt"
    if version in LATER:
        FORMAL_CONFIGS = tuple(sorted(p.stem for p in (ROOT / "configs" / version).glob(LATER[version]["glob"])))


def frozen_files() -> list[Path]:
    if VERSION in LATER:
        spec = LATER[VERSION]
        files = [ROOT / "docs" / "protocol" / d for d in spec["docs"]]
        files += [ROOT / "materials" / "tokenizer_manifest.json", ROOT / "requirements.txt", ROOT / "pyproject.toml"]
        files += [ROOT / "scripts" / s for s in spec["scripts"]]
        files += sorted((ROOT / "src" / "mb").glob("*.py"))
        files += [ROOT / "configs" / VERSION / f"{name}.yaml" for name in FORMAL_CONFIGS]
        return files
    files = [ROOT / "docs" / "protocol" / "EXPERIMENT_DESIGN.md", ROOT / "materials" / "tokenizer_manifest.json",
             ROOT / "requirements.txt", ROOT / "pyproject.toml", ROOT / "scripts" / "make_main.py",
             ROOT / "scripts" / "run_formal.sh", ROOT / "scripts" / "freeze_protocol.py"]
    files += sorted((ROOT / "src" / "mb").glob("*.py"))
    files += [ROOT / "configs" / f"{name}.yaml" for name in FORMAL_CONFIGS]
    return files


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write() -> int:
    if FREEZE.exists():
        raise SystemExit(f"{FREEZE} exists; a frozen protocol is never overwritten")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True)
    if dirty.strip():
        raise SystemExit("commit the formal configs first: the tracked tree is dirty")
    import yaml

    lines = [
        f"# protocol-{VERSION} freeze manifest (sha256  path). Verify with: "
        f"python scripts/freeze_protocol.py --verify --version {VERSION}",
        f"# frozen_at: {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}",
        f"# commit: {commit}",
    ]
    if VERSION == "v1":
        frozen = yaml.safe_load((ROOT / "configs" / "main.yaml").read_text())["frozen"]
        lines += [
            f"# frozen parameters: {json.dumps({k: frozen[k] for k in ('form', 'layer', 'g_star', 'main_gains', 'g_static', 'static_neighbors', 'per_layer_gain', 'N', 'N_ext')})}",
            f"# sources: {json.dumps(frozen['sources'])}",
        ]
    else:
        for name in FORMAL_CONFIGS:
            cfg = yaml.safe_load((ROOT / "configs" / VERSION / f"{name}.yaml").read_text())
            params = cfg.get("params") or {}
            lines.append(f"# {name}: N={cfg['n_episodes']} arms={len(cfg['arms'])} "
                         f"families={json.dumps(params.get('families', {}))}"
                         + (f" equivalence={json.dumps(params['equivalence'])}" if params.get("equivalence") else ""))
    lines += [f"{digest(p)}  {p.relative_to(ROOT)}" for p in frozen_files()]
    FREEZE.write_text("\n".join(lines) + "\n")
    print(f"wrote {FREEZE}; now commit it and tag protocol-{VERSION}")
    return 0


def verify() -> int:
    if not FREEZE.exists():
        print("no freeze manifest", file=sys.stderr)
        return 2
    bad = []
    for line in FREEZE.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        sha, rel = line.split("  ", 1)
        path = ROOT / rel
        if not path.exists() or digest(path) != sha:
            bad.append(rel)
    listed = {line.split("  ", 1)[1] for line in FREEZE.read_text().splitlines() if line and not line.startswith("#")}
    missing = [str(p.relative_to(ROOT)) for p in frozen_files() if str(p.relative_to(ROOT)) not in listed]
    if bad or missing:
        print(f"freeze verification FAILED: changed {bad}, unlisted {missing}", file=sys.stderr)
        return 1
    print("freeze verification ok")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    ap.add_argument("--version", default="v1", choices=["v1", *LATER])
    args = ap.parse_args()
    configure(args.version)
    return write() if args.write else verify()


if __name__ == "__main__":
    raise SystemExit(main())
