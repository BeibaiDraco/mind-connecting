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
PHASE = "formal"
# Later versions (--version v2 / v3): protocol text, generator and driver scripts; configs in configs/<version>/.
LATER = {
    "v2": {"docs": ("PROTOCOL_V2.md",), "glob": "v2_*.yaml",
           "scripts": ("make_v2_main.py", "make_v2_signal.py", "run_formal_v2.sh", "freeze_protocol.py")},
    "v3": {"docs": ("PROTOCOL_V3.md",), "glob": "v3_confirm*.yaml",
           "scripts": ("make_v3_confirm.py", "run_chain.sh", "freeze_protocol.py")},
}


def configure(version: str, phase: str = "formal") -> None:
    global FREEZE, FORMAL_CONFIGS, VERSION, PHASE
    VERSION = version
    PHASE = phase
    suffix = f"_{phase}" if version == "v4" and phase != "formal" else ""
    FREEZE = ROOT / "docs" / "protocol" / f"FREEZE_protocol_{version}{suffix}.txt"
    if version == "v4":
        names = ["v4_smoke", "v4_base", "v4_cal", "v4_strength"]
        if phase in ("settings", "formal"):
            if (ROOT / "configs" / "v4" / "v4_match.yaml").exists():
                names.append("v4_match")
            names.append("v4_validity")
        if phase == "formal":
            names.append("v4_confirm")
        FORMAL_CONFIGS = tuple(names)
    elif version == "v1":
        FORMAL_CONFIGS = ("main", "main_diag", "ext_layers", "ext_masks")
    if version in LATER:
        FORMAL_CONFIGS = tuple(sorted(p.stem for p in (ROOT / "configs" / version).glob(LATER[version]["glob"])))


def frozen_files() -> list[Path]:
    if VERSION == "v4":
        return v4_files()
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


def v4_files() -> list[Path]:
    """Freeze algorithms, then selected settings, then validated formal input.

    Selection outputs are frozen through their referenced snapshots. New later
    outcome artifacts do not silently expand an earlier manifest's membership.
    Actual model assets are checked against their pinned manifest each time.
    """
    import yaml
    from mb.model_profiles import resolve_profile

    profile = resolve_profile("llama31_8b_instruct")
    assets = profile.validate_manifest()
    protocol = ROOT / "docs" / "protocol" / "PROTOCOL_V4.md"
    if "Approved by the PI" not in protocol.read_text().split("## 1.", 1)[0]:
        raise ValueError("v4 requires the approved final protocol, not a draft")
    files = [protocol, ROOT / "requirements.txt", ROOT / "pyproject.toml", profile.manifest_path,
             ROOT / "scripts" / "make_v4_configs.py", ROOT / "scripts" / "freeze_protocol.py",
             ROOT / "scripts" / "fetch_model_assets.py", ROOT / "scripts" / "setup_replication_gpu.sh",
             ROOT / "scripts" / "check_llama_acceptance.py", ROOT / "tests" / "test_llama_acceptance.py",
             ROOT / "scripts" / "supervise_v4.py", ROOT / "tests" / "test_v4_supervision.py",
             ROOT / "scripts" / "check_v4_smoke.py", ROOT / "tests" / "test_v4_smoke_audit.py",
             ROOT / "configs" / "v4" / "split_manifest.json"]
    files += sorted((ROOT / "src" / "mb").glob("*.py"))
    files += [profile.tokenizer_dir / name for name in sorted(assets["files"])]
    if PHASE in ("settings", "formal"):
        files.append(ROOT / "docs" / "protocol" / "FREEZE_protocol_v4_algorithm.txt")
    if PHASE == "formal":
        files.append(ROOT / "docs" / "protocol" / "FREEZE_protocol_v4_settings.txt")
    for name in FORMAL_CONFIGS:
        path = ROOT / "configs" / "v4" / f"{name}.yaml"
        cfg = yaml.safe_load(path.read_text())
        if cfg.get("model_profile") != profile.key:
            raise ValueError(f"{path}: wrong v4 model profile")
        if name == "v4_confirm" and cfg["n_episodes"] != 600:
            raise ValueError("v4 formal N must remain 600")
        files.append(path)
        params = cfg.get("params") or {}
        pins = {**params.get("sources", {}), "model_assets": params["model_assets"]}
        for label, spec in pins.items():
            source = Path(spec["path"])
            source = source if source.is_absolute() else ROOT / source
            source.relative_to(ROOT)  # archival freezes must not depend on a private external path
            if digest(source) != spec["sha256"]:
                raise ValueError(f"changed {label} artifact for {name}")
            files.append(source)
    return sorted(set(files))


def _verify_v4_predecessor() -> None:
    if PHASE == "algorithm":
        return
    prior = "algorithm" if PHASE == "settings" else "settings"
    path = ROOT / "docs" / "protocol" / f"FREEZE_protocol_v4_{prior}.txt"
    if not path.exists():
        raise ValueError(f"v4 {prior} must be frozen first")
    for line in path.read_text().splitlines():
        if line and not line.startswith("#"):
            sha, rel = line.split("  ", 1)
            if not (ROOT / rel).exists() or digest(ROOT / rel) != sha:
                raise ValueError(f"v4 {prior} freeze changed: {rel}")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write() -> int:
    if FREEZE.exists():
        raise SystemExit(f"{FREEZE} exists; a frozen protocol is never overwritten")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True)
    if dirty.strip():
        raise SystemExit("commit the formal configs first: the tracked tree is dirty")
    if VERSION == "v4":
        _verify_v4_predecessor()
    import yaml

    phase_option = f" --phase {PHASE}" if VERSION == "v4" else ""
    lines = [
        f"# protocol-{VERSION} freeze manifest (sha256  path). Verify with: "
        f"python scripts/freeze_protocol.py --verify --version {VERSION}{phase_option}",
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
    tag = f"protocol-v4-{PHASE}" if VERSION == "v4" and PHASE != "formal" else f"protocol-{VERSION}"
    print(f"wrote {FREEZE}; now commit it and tag {tag}")
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
    ap.add_argument("--version", default="v1", choices=["v1", *LATER, "v4"])
    ap.add_argument("--phase", default="formal", choices=["algorithm", "settings", "formal"],
                    help="v4 only: algorithm before pilots, settings before validity, formal before N=600")
    args = ap.parse_args()
    if args.version != "v4" and args.phase != "formal":
        ap.error("--phase is only available for v4")
    configure(args.version, args.phase)
    return write() if args.write else verify()


if __name__ == "__main__":
    raise SystemExit(main())
