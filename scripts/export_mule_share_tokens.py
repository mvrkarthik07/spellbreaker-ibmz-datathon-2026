#!/usr/bin/env python3
"""Export receiver scores with HMAC pseudonyms, never raw account IDs."""
import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ml.mule_share import receiver_token


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="results/mule_scores.csv")
    parser.add_argument("--output", default="results/mule_share_tokens.csv")
    args = parser.parse_args()
    source, target = ROOT / args.input, ROOT / args.output
    target.parent.mkdir(parents=True, exist_ok=True)
    with source.open(newline="", encoding="utf-8") as src, target.open("w", newline="", encoding="utf-8") as dst:
        reader = csv.DictReader(src)
        if not {"account", "score", "is_mule"}.issubset(reader.fieldnames or []):
            raise ValueError("input must contain account, score and is_mule columns")
        writer = csv.DictWriter(dst, fieldnames=("account_token", "score", "is_mule"))
        writer.writeheader()
        for row in reader:
            writer.writerow({
                "account_token": receiver_token(row["account"]),
                "score": row["score"],
                "is_mule": row["is_mule"],
            })
    print(f"Wrote tokenized receiver scores to {target}; raw account IDs are omitted.")


if __name__ == "__main__":
    main()
