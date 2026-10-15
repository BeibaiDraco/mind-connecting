"""Prepare an inert operator-only experiment; never launch hardware."""

from argparse import ArgumentParser
from pathlib import Path

from mb.v6_efficient import KERNELS
from mb.v6_efficient_probe import prepare


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--kernel", choices=KERNELS, required=True)
    args = parser.parse_args()
    prepare(args.output, args.kernel)
    print("Prepared engineering-only operator package. No hardware or model started.")


if __name__ == "__main__":
    main()
