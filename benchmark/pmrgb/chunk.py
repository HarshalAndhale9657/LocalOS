"""Recursive chunker (~400–512 tokens, no overlap) — mirrors docs/02 §4.

Token count approximated by whitespace splitting (good enough for v0; the extension
uses the model tokenizer). Splits on paragraph boundaries first, then packs.
"""
from __future__ import annotations

from .schema import Chunk


def _ntokens(s: str) -> int:
    return len(s.split())


def chunk_text(text: str, target: int = 480, hard_max: int = 512) -> list[Chunk]:
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[Chunk] = []
    buf: list[str] = []
    buf_tok = 0
    cursor = 0  # char offset into `text`

    def flush():
        nonlocal buf, buf_tok, cursor
        if not buf:
            return
        body = "\n".join(buf)
        start = text.find(buf[0], cursor)
        start = start if start >= 0 else cursor
        end = start + len(body)
        chunks.append(Chunk(chunk_id=f"c_{len(chunks)}", text=body, offset=(start, end)))
        cursor = end
        buf, buf_tok = [], 0

    for p in paras:
        pt = _ntokens(p)
        if buf_tok + pt > hard_max and buf:
            flush()
        buf.append(p)
        buf_tok += pt
        if buf_tok >= target:
            flush()
    flush()
    return chunks or [Chunk(chunk_id="c_0", text=text, offset=(0, len(text)))]
