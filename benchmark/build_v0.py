"""Build the Personal-Memory-RGB v0 dataset.

Usage:
    python build_v0.py --histories 12 --pages-per 6 --universe 40 --seed 7 --out data/v0
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter

from pmrgb.generate import generate
from pmrgb.schema import ANSWERABLE


def write_jsonl(path: str, rows: list[dict]):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--histories", type=int, default=12)
    ap.add_argument("--pages-per", type=int, default=6)
    ap.add_argument("--universe", type=int, default=40)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="data/v0")
    args = ap.parse_args()

    histories, items = generate(args.seed, args.histories, args.pages_per, args.universe)

    os.makedirs(args.out, exist_ok=True)
    write_jsonl(os.path.join(args.out, "histories.jsonl"), [h.to_dict() for h in histories])
    write_jsonl(os.path.join(args.out, "items.jsonl"), [it.to_dict() for it in items])

    by_type = Counter(it.type for it in items)
    n_ans = sum(1 for it in items if it.type in ANSWERABLE)
    n_pages = sum(len(h.pages) for h in histories)
    print(f"wrote {len(histories)} histories ({n_pages} pages) and {len(items)} items -> {args.out}")
    print(f"  answerable {n_ans}  /  must-abstain {len(items)-n_ans}")
    for t in sorted(by_type):
        print(f"    {t:<16} {by_type[t]}")


if __name__ == "__main__":
    main()
