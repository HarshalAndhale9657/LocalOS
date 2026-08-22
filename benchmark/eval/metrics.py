"""Metrics for Personal-Memory-RGB (docs/03 §5, docs/05 §8).

v0 focuses on the CALIBRATED-REFUSAL decision (answer vs abstain), which is computable
without a model and is the paper's headline axis. Answer-quality metrics (RAGAS/ALCE)
require a judge/model and are defined as interfaces to fill in M2+.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Prediction:
    id: str
    decision: str                 # "answer" | "abstain"
    answer: Optional[str] = None
    citations: Optional[list] = None
    confidence: Optional[float] = None   # P(correct/should-answer); enables risk-coverage


def refusal_metrics(gold: dict[str, str], pred: dict[str, str]) -> dict:
    """Treat ABSTAIN as the positive class (the thing we must get right)."""
    tp = fp = fn = tn = 0
    for i, g in gold.items():
        p = pred.get(i, "answer")
        if g == "abstain" and p == "abstain":
            tp += 1
        elif g == "answer" and p == "abstain":
            fp += 1
        elif g == "abstain" and p == "answer":
            fn += 1
        else:
            tn += 1
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    acc = (tp + tn) / max(1, len(gold))
    return {"abstain_precision": prec, "abstain_recall": rec, "abstain_f1": f1,
            "decision_accuracy": acc, "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def risk_coverage(preds: list[Prediction], correct: dict[str, bool]) -> list[tuple[float, float]]:
    """Curve points (coverage, selective_risk) by thresholding confidence descending.

    `correct[id]` = whether the emitted decision/answer was right. Returns points from
    high-confidence (low coverage) to answering everything (full coverage).
    """
    scored = [p for p in preds if p.confidence is not None]
    if not scored:
        return []
    scored.sort(key=lambda p: p.confidence, reverse=True)
    pts, errors = [], 0
    for k, p in enumerate(scored, start=1):
        if not correct.get(p.id, False):
            errors += 1
        pts.append((k / len(scored), errors / k))
    return pts


# --- interfaces to implement in M2+ (need a judge/model) --------------------
def ragas_faithfulness(*_a, **_k):  # pragma: no cover - interface
    raise NotImplementedError("RAGAS faithfulness needs a judge model (M2)")


def alce_citation_pr(*_a, **_k):  # pragma: no cover - interface
    raise NotImplementedError("ALCE citation precision/recall needs NLI (M2)")
