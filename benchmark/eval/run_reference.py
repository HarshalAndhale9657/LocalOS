"""A genuine (non-oracle) reference system for Personal-Memory-RGB v0.

System = BM25 retrieval over the item's own history + a score-threshold abstention rule:
  answer if top_score >= tau else abstain.
No model required. This gives the first real calibration numbers AND exposes the gap the
fine-tuned model must close: retrieval-score is a decent abstention signal for
`not_in_history` (nothing to retrieve) but a BAD one for `stale` / `false_premise`
(the page IS in history and matches lexically, yet the correct behavior is to abstain).

Usage: python -m eval.run_reference --data data/v0 [--tau auto]
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

from .retriever import BM25
from .metrics import refusal_metrics, auroc, risk_coverage, Prediction


def load(path):
    def jl(name):
        with open(os.path.join(path, name), encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]
    return jl("histories.jsonl"), jl("items.jsonl")


def build_retrievers(histories):
    r = {}
    for h in histories:
        docs = [(f"{p['page_id']}::{c['chunk_id']}", c["text"])
                for p in h["pages"] for c in p["chunks"]]
        r[h["history_id"]] = BM25(docs)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/v0")
    ap.add_argument("--tau", default="auto", help="'auto' picks the decision-accuracy-optimal threshold")
    args = ap.parse_args()

    histories, items = load(args.data)
    retr = build_retrievers(histories)

    # score every item with its history's retriever
    top_scores = {}
    for it in items:
        _, s = retr[it["history_id"]].top(it["question"])
        top_scores[it["id"]] = s

    gold = {it["id"]: it["gold_decision"] for it in items}
    smax = max(top_scores.values()) or 1.0

    has_split = any("split" in it for it in items)
    dev = [it for it in items if it.get("split") == "dev"] if has_split else items
    test = [it for it in items if it.get("split") == "test"] if has_split else items

    def preds_at(subset, tau):
        return {it["id"]: ("answer" if top_scores[it["id"]] >= tau else "abstain") for it in subset}

    # fit tau on DEV (or the whole set if unsplit), evaluate on TEST
    if args.tau == "auto":
        dev_gold = {it["id"]: it["gold_decision"] for it in dev}
        best_tau, best_acc = 0.0, -1.0
        for tau in sorted({top_scores[it["id"]] for it in dev}):
            acc = refusal_metrics(dev_gold, preds_at(dev, tau))["decision_accuracy"]
            if acc > best_acc:
                best_acc, best_tau = acc, tau
        tau = best_tau
    else:
        tau = float(args.tau)

    test_gold = {it["id"]: it["gold_decision"] for it in test}
    pred = preds_at(test, tau)
    m = refusal_metrics(test_gold, pred)

    # abstention AUROC on TEST: positive = should-abstain; signal = LOW retrieval score
    ids = [it["id"] for it in test]
    labels = [1 if test_gold[i] == "abstain" else 0 for i in ids]
    abstain_signal = [1.0 - top_scores[i] / smax for i in ids]
    au = auroc(abstain_signal, labels)

    note = (f"tau fit on dev (n={len(dev)}), reported on test (n={len(test)})"
            if has_split else "no split found - fit & reported on all items (optimistic)")
    print(f"\nReference system: BM25 + score-threshold abstention (tau={tau:.3f})")
    print(f"  [{note}]")
    print(f"  abstain P/R/F1 = {m['abstain_precision']:.3f} / {m['abstain_recall']:.3f} / {m['abstain_f1']:.3f}"
          f"   decision_acc = {m['decision_accuracy']:.3f}")
    print(f"  abstention AUROC (retrieval-score signal) = {au:.3f}")

    # per-type decision accuracy on TEST — the diagnostic that motivates the fine-tuned model
    per = defaultdict(lambda: [0, 0])
    for it in test:
        ok = (pred[it["id"]] == test_gold[it["id"]])
        per[it["type"]][0] += 1 if ok else 0
        per[it["type"]][1] += 1
    print("\n  per-type decision accuracy:")
    accs = {t: per[t][0] / per[t][1] for t in per}
    for t in sorted(per):
        c, n = per[t]
        print(f"    {t:<16} {accs[t]:.3f}  ({c}/{n})")
    worst = sorted(accs, key=accs.get)[:2]
    worst_str = ", ".join(f"{t} ({accs[t]:.2f})" for t in worst)
    print(f"\n  Weakest classes for a pure lexical-score threshold: {worst_str}.")
    print("  A single global score cutoff cannot separate 'answerable but low lexical overlap'")
    print("  (e.g. time-scoped/recency questions) from 'must-abstain'. Closing that gap is exactly")
    print("  the job of the SFT+DPO calibrated model with a learned abstention signal (docs/03).\n")


if __name__ == "__main__":
    main()
