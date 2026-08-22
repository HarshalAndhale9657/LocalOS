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

    # choose tau
    if args.tau == "auto":
        cands = sorted(set(top_scores.values()))
        best_tau, best_acc = 0.0, -1.0
        for tau in cands:
            pred = {i: ("answer" if s >= tau else "abstain") for i, s in top_scores.items()}
            acc = refusal_metrics(gold, pred)["decision_accuracy"]
            if acc > best_acc:
                best_acc, best_tau = acc, tau
        tau = best_tau
    else:
        tau = float(args.tau)

    pred = {i: ("answer" if s >= tau else "abstain") for i, s in top_scores.items()}
    m = refusal_metrics(gold, pred)

    # abstention AUROC: positive = should-abstain; signal = LOW retrieval score
    ids = [it["id"] for it in items]
    labels = [1 if gold[i] == "abstain" else 0 for i in ids]
    abstain_signal = [1.0 - top_scores[i] / smax for i in ids]
    au = auroc(abstain_signal, labels)

    note = "fit on eval set - OPTIMISTIC upper bound; use a dev split in M2" if args.tau == "auto" else "fixed"
    print(f"\nReference system: BM25 + score-threshold abstention (tau={tau:.3f}, {note})")
    print(f"  abstain P/R/F1 = {m['abstain_precision']:.3f} / {m['abstain_recall']:.3f} / {m['abstain_f1']:.3f}"
          f"   decision_acc = {m['decision_accuracy']:.3f}")
    print(f"  abstention AUROC (retrieval-score signal) = {au:.3f}")

    # per-type decision accuracy — the diagnostic that motivates the fine-tuned model
    per = defaultdict(lambda: [0, 0])
    for it in items:
        ok = (pred[it["id"]] == gold[it["id"]])
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
