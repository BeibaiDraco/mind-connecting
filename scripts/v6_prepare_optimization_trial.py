"""Prepare an inert engineering package. This CLI cannot start hardware."""
import argparse
from pathlib import Path
from mb.v6_efficiency_trial import prepare

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();prepare(args.output)
    print(f"Prepared inert package: {args.output/'package.json'}")
