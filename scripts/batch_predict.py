"""Batch prediction CLI script."""
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.inference.batch import predict_race_batch


def main():
    parser = argparse.ArgumentParser(description="Run batch predictions on F1 race data")
    parser.add_argument("--input", required=True, help="Input CSV path")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--registry", default="data/registry", help="Model registry path")

    args = parser.parse_args()

    predict_race_batch(args.input, args.output, args.registry)


if __name__ == "__main__":
    main()
