"""Prepare an inert local compiler diagnostic; no provider or CUDA dispatch."""
from __future__ import annotations
import argparse
from pathlib import Path

from mb.v6_efficiency_trial import prepare_compiler_check


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args=parser.parse_args()
    package=prepare_compiler_check(args.directory)
    print(f"Prepared {len(package['source_sha256'])} source pins; paid launch remains unauthorized.")


if __name__ == "__main__": main()
