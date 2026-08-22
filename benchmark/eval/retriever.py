"""Stdlib BM25 retriever over a single history's chunks.

A deliberately simple *lexical* baseline retriever, so we can build a genuine
(non-oracle) reference system for the calibrated-refusal evaluation without any
model. Mirrors the "sparse" half of the extension's hybrid retrieval (docs/02 §4).
"""
from __future__ import annotations

import math
import re
from collections import Counter

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = {"the", "of", "a", "is", "are", "was", "were", "to", "in", "on", "and", "or",
         "what", "which", "did", "you", "read", "about", "has", "have", "its", "it",
         "current", "listed", "higher", "than"}


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in _STOP]


class BM25:
    def __init__(self, docs: list[tuple[str, str]], k1: float = 1.5, b: float = 0.75):
        # docs: list of (doc_id, text)
        self.ids = [d[0] for d in docs]
        self.toks = [tokenize(d[1]) for d in docs]
        self.k1, self.b = k1, b
        self.N = len(docs)
        self.len = [len(t) for t in self.toks]
        self.avg = (sum(self.len) / self.N) if self.N else 0.0
        df: Counter = Counter()
        for t in self.toks:
            for w in set(t):
                df[w] += 1
        self.idf = {w: math.log(1 + (self.N - n + 0.5) / (n + 0.5)) for w, n in df.items()}
        self.tf = [Counter(t) for t in self.toks]

    def score(self, query: str) -> list[tuple[str, float]]:
        q = tokenize(query)
        out = []
        for i, docid in enumerate(self.ids):
            s = 0.0
            dl = self.len[i] or 1
            for w in q:
                if w not in self.tf[i]:
                    continue
                f = self.tf[i][w]
                idf = self.idf.get(w, 0.0)
                s += idf * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / (self.avg or 1)))
            out.append((docid, s))
        out.sort(key=lambda x: x[1], reverse=True)
        return out

    def top(self, query: str) -> tuple[str, float]:
        r = self.score(query)
        return r[0] if r else ("", 0.0)
