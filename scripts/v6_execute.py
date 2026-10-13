#!/usr/bin/env python3
"""Run an explicitly admitted V6 native stage; no provider or download actions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mb.v6_execution import audit_noop_resume, execute, _plan
from mb.v6_run import _write_new


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--admission", required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--resume-audit-out", type=Path)
    args = parser.parse_args()
    if args.resume_audit_out:
        if args.resume or args.validate_only:
            parser.error("--resume-audit-out is separate from --resume/--validate-only")
        plan = _plan(Path(args.plan), Path(args.admission))
        if args.resume_audit_out.resolve().is_relative_to(Path(plan["output_dir"]).resolve()):
            parser.error("Resume certificate must be outside the unchanged scientific run")
        result = audit_noop_resume(args.plan, args.admission)
        _write_new(args.resume_audit_out, result)
    else:
        result = execute(args.plan, args.admission, resume=args.resume, validate_only=args.validate_only)
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    gate = result.get("validation", {}).get("gate")
    return 3 if gate is not None and gate != "pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
