#!/usr/bin/env python3
"""Prepare an inert engineering comparison package; never acquire/run a GPU."""

import argparse
import json
from pathlib import Path

from mb.v6_benchmark import prepare
from mb.v6_contract import canonical_digest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    plan = prepare(args.directory)
    print(json.dumps({"prepared": True, "package_sha256": canonical_digest(plan),
                      "paid_launch_authorized": False, "formal_authorized": False}))
