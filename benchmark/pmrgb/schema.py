"""Data schema for Personal-Memory-RGB (see ../../docs/05_BENCHMARK_Personal_Memory_RGB.md).

Dataclasses with plain-dict (de)serialization so the whole benchmark is stdlib-only
and trivially dumped to JSONL / loaded by HuggingFace `datasets` later.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional

# Question classes -----------------------------------------------------------
ANSWERABLE = {"single_hop", "multi_hop", "time_scoped"}
MUST_ABSTAIN = {"not_in_history", "stale", "false_premise"}
ALL_TYPES = ANSWERABLE | MUST_ABSTAIN


@dataclass
class Chunk:
    chunk_id: str
    text: str
    offset: tuple[int, int]


@dataclass
class Page:
    page_id: str
    url: str
    title: str
    read_at: str  # ISO 8601 — powers time_scoped + staleness
    text: str
    chunks: list[Chunk]
    simhash: str = ""
    near_dup_of: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["chunks"] = [{"chunk_id": c.chunk_id, "text": c.text, "offset": list(c.offset)} for c in self.chunks]
        return d


@dataclass
class History:
    history_id: str
    persona: str
    pages: list[Page]

    def to_dict(self) -> dict:
        return {"history_id": self.history_id, "persona": self.persona,
                "pages": [p.to_dict() for p in self.pages]}


@dataclass
class Citation:
    page_id: str
    chunk_id: str
    url: str
    read_at: str
    quote: str


@dataclass
class QAItem:
    id: str
    history_id: str
    question: str
    type: str                      # one of ALL_TYPES
    gold_decision: str             # "answer" | "abstain"
    gold_answer: Optional[str]
    citations: list[Citation]
    as_of: str
    difficulty: str = "easy"       # easy | medium | hard
    abstain_reason: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def __post_init__(self):
        assert self.type in ALL_TYPES, f"bad type {self.type}"
        assert self.gold_decision in ("answer", "abstain")
        # invariant: answerable => answer + >=1 citation; must-abstain => abstain
        if self.type in ANSWERABLE:
            assert self.gold_decision == "answer" and self.citations, self.id
        else:
            assert self.gold_decision == "abstain", self.id
