"""Validate the eval harness end-to-end with trivial 'systems'.

These need no model — they prove the metrics work and frame the calibration axis:
an oracle scores 1.0, while always-answer / always-abstain both fail, so only a
CALIBRATED system can win. Real systems (base model, SFT, SFT+DPO) plug in at M1.5+.

Usage: python -m eval.run_baseline --data data/v0
"""
from __future__ import annotations

import argparse
import json
import os
import random

from .metrics import refusal_metrics


def load_items(path: str) -> list[dict]:
    items = []
    with open(os.path.join(path, "items.jsonl"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def systems(items, seed=0):
    rng = random.Random(seed)
    gold = {it["id"]: it["gold_decision"] for it in items}
    return {
        "always_answer": {it["id"]: "answer" for it in items},
        "always_abstain": {it["id"]: "abstain" for it in items},
        "random": {it["id"]: rng.choice(["answer", "abstain"]) for it in items},
        "oracle": dict(gold),
    }, gold


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/v0")
    args = ap.parse_args()

    items = load_items(args.data)
    preds, gold = systems(items)

    n_abstain = sum(1 for g in gold.values() if g == "abstain")
    print(f"\nPersonal-Memory-RGB v0 — {len(items)} items "
          f"({n_abstain} must-abstain / {len(items)-n_abstain} answerable)\n")

    hdr = f"{'system':<16}{'abst_P':>8}{'abst_R':>8}{'abst_F1':>9}{'dec_acc':>9}"
    print(hdr)
    print("-" * len(hdr))
    for name, pred in preds.items():
        m = refusal_metrics(gold, pred)
        print(f"{name:<16}{m['abstain_precision']:>8.3f}{m['abstain_recall']:>8.3f}"
              f"{m['abstain_f1']:>9.3f}{m['decision_accuracy']:>9.3f}")
    print("\n(Only a calibrated system beats the trivial baselines — that gap is the paper's point.)\n")


if __name__ == "__main__":
    main()
