"""64-bit SimHash + Hamming distance for near-duplicate detection.

Mirrors the extension's dedup step (docs/02 §4) so the benchmark can inject and
label realistic near-duplicate pages. Stdlib-only (hashlib).
"""
from __future__ import annotations

import hashlib
import re

_TOKEN = re.compile(r"[a-z0-9]+")


def _token_hash(token: str) -> int:
    h = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(h, "big")


def simhash64(text: str) -> int:
    tokens = _TOKEN.findall(text.lower())
    if not tokens:
        return 0
    v = [0] * 64
    for tok in tokens:
        hv = _token_hash(tok)
        for i in range(64):
            v[i] += 1 if (hv >> i) & 1 else -1
    out = 0
    for i in range(64):
        if v[i] > 0:
            out |= (1 << i)
    return out


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def is_near_dup(a: str, b: str, threshold: int = 3) -> bool:
    return hamming(simhash64(a), simhash64(b)) <= threshold


def simhash_hex(text: str) -> str:
    return f"0x{simhash64(text):016x}"
