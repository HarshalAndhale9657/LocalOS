"""Build the Personal-Memory-RGB v0 dataset.

Usage:
    python build_v0.py --histories 12 --pages-per 6 --universe 40 --seed 7 --out data/v0
"""
from __future__ import annotations

import argparse
import json
import os
import random
from collections import Counter

from pmrgb.generate import generate
from pmrgb.schema import ANSWERABLE


def assign_splits(history_ids: list[str], seed: int) -> dict[str, str]:
    """Deterministic ~60/20/20 train/dev/test split BY HISTORY (no history leaks
    across splits — docs/03 §8)."""
    ids = list(history_ids)
    random.Random(seed + 1).shuffle(ids)
    n = len(ids)
    n_test = max(1, round(0.2 * n))
    n_dev = max(1, round(0.2 * n))
    test = set(ids[:n_test])
    dev = set(ids[n_test:n_test + n_dev])
    return {h: ("test" if h in test else "dev" if h in dev else "train") for h in history_ids}


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
    split_of = assign_splits([h.history_id for h in histories], args.seed)

    hist_rows = [{**h.to_dict(), "split": split_of[h.history_id]} for h in histories]
    item_rows = [{**it.to_dict(), "split": split_of[it.history_id]} for it in items]

    os.makedirs(args.out, exist_ok=True)
    write_jsonl(os.path.join(args.out, "histories.jsonl"), hist_rows)
    write_jsonl(os.path.join(args.out, "items.jsonl"), item_rows)

    by_type = Counter(it.type for it in items)
    by_split = Counter(r["split"] for r in item_rows)
    n_ans = sum(1 for it in items if it.type in ANSWERABLE)
    n_pages = sum(len(h.pages) for h in histories)
    print(f"wrote {len(histories)} histories ({n_pages} pages) and {len(items)} items -> {args.out}")
    print(f"  answerable {n_ans}  /  must-abstain {len(items)-n_ans}")
    print(f"  splits: " + "  ".join(f"{s}={by_split[s]}" for s in ("train", "dev", "test")))
    for t in sorted(by_type):
        print(f"    {t:<16} {by_type[t]}")


if __name__ == "__main__":
    main()
