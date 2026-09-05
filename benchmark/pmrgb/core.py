"""Shared core (Python side): prompt loading/rendering + refusal/citation parsing.

Mirrors extension/lib/model/core.ts exactly. Both are checked against the same behaviour
vectors in shared/tests/refusal_cases.json, so the benchmark harness measures the *product's*
prompt and parser, not a re-implementation (docs/07 §10.1).
"""
from __future__ import annotations

import os
import re
from functools import lru_cache

SHARED_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
PROMPTS_DIR = os.path.join(SHARED_DIR, "prompts")


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    with open(os.path.join(PROMPTS_DIR, name), encoding="utf-8") as f:
        return f.read()


def prompt_version() -> str:
    return load_prompt("version.txt").strip()


REFUSAL = load_prompt("refusal.txt").strip()


def render(template: str, **vars: str) -> str:
    """Plain `{name}` substitution; no format() semantics so braces in prompts are safe."""
    out = template
    for k, v in vars.items():
        out = out.replace("{" + k + "}", v)
    return out


def qa_system_prompt() -> str:
    return render(load_prompt("grounded_qa.system.txt"), refusal=REFUSAL).strip()


def qa_user_prompt(question: str, sources: list[dict]) -> str:
    """sources: [{title|url, read_at, text}] in citation order (1-based in the prompt)."""
    item_t = load_prompt("source_item.txt").rstrip("\n")
    items = [
        render(item_t, n=str(i + 1), title=(s.get("title") or s.get("url") or ""),
               read_at=str(s.get("read_at", ""))[:10], text=s.get("text", ""))
        for i, s in enumerate(sources)
    ]
    return render(load_prompt("grounded_qa.user.txt"), question=question, sources="\n\n".join(items)).strip()


_REFUSAL_RE = re.compile(re.escape(REFUSAL.rstrip(".")) + r"\.?", re.IGNORECASE)


def is_refusal(text: str) -> bool:
    """Strict rule (shared vectors): the refusal string, period optional, case-insensitive,
    with at most 7 extra characters of padding/quotes. Refusal-then-content is NOT a refusal."""
    t = text.strip()
    return bool(_REFUSAL_RE.search(t)) and len(t) < len(REFUSAL) + 8


_CITE_RE = re.compile(r"\[(\d+)\]")


def cited_indices(text: str) -> list[int]:
    """Distinct 1-based citation numbers in first-appearance order."""
    seen: list[int] = []
    for m in _CITE_RE.finditer(text):
        n = int(m.group(1))
        if n not in seen:
            seen.append(n)
    return seen


def parse_answer(text: str, n_sources: int) -> dict:
    """Decision + valid citations from raw model text (mirrors LocalModel.answer())."""
    if is_refusal(text):
        return {"decision": "abstain", "text": REFUSAL, "cited": []}
    cited = [n for n in cited_indices(text) if 1 <= n <= n_sources]
    return {"decision": "answer", "text": text.strip(), "cited": cited}
