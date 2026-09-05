"""Provider-agnostic teacher-LLM client (stdlib only) for Personal-Memory-RGB v1 generation.

Speaks the OpenAI chat-completions wire format, which every candidate provider exposes:
  - Ollama (local, free):       TEACHER_BASE_URL=http://localhost:11434/v1   TEACHER_API_KEY=ollama
  - Groq (free tier):           TEACHER_BASE_URL=https://api.groq.com/openai/v1
  - Google Gemini (free tier):  TEACHER_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
  - OpenAI:                     TEACHER_BASE_URL=https://api.openai.com/v1
  - Anthropic (OpenAI-compat):  TEACHER_BASE_URL=https://api.anthropic.com/v1
Set TEACHER_MODEL to the provider's model id. Defaults to the local Ollama 3B so the pipeline
runs with zero budget; swap the env vars to upgrade the teacher without touching code.

Budget discipline (docs/07 §9: 5–10 USD total): every call is disk-cached by content hash, and a
running ledger of prompt/completion tokens per model is appended to data/cache/teacher_ledger.jsonl
so spend can be audited. Generation prompts should therefore be deterministic (temperature 0 or a
fixed seed) so re-runs are free.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache", "teacher")
LEDGER = os.path.join(os.path.dirname(__file__), "..", "data", "cache", "teacher_ledger.jsonl")


class Teacher:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None,
                 timeout: int = 180, min_interval_s: float = 0.0):
        self.base_url = (base_url or os.environ.get("TEACHER_BASE_URL") or "http://localhost:11434/v1").rstrip("/")
        self.api_key = api_key or os.environ.get("TEACHER_API_KEY") or "ollama"
        self.model = model or os.environ.get("TEACHER_MODEL") or "qwen2.5:3b-instruct"
        self.timeout = timeout
        self.min_interval_s = min_interval_s  # crude client-side rate limit for free tiers
        self._last = 0.0
        os.makedirs(CACHE_DIR, exist_ok=True)

    # --- core ---------------------------------------------------------------------------
    def chat(self, system: str, user: str, *, temperature: float = 0.0, seed: int | None = 7,
             json_mode: bool = False, max_tokens: int = 1024, tag: str = "") -> str:
        body = {
            "model": self.model, "temperature": temperature, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        if seed is not None:
            body["seed"] = seed
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        key = hashlib.sha1(json.dumps([self.base_url, body], sort_keys=True).encode()).hexdigest()
        path = os.path.join(CACHE_DIR, key + ".json")
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)["content"]

        wait = self.min_interval_s - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions", data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
        )
        data = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    data = json.loads(r.read().decode())
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503) and attempt < 3:
                    time.sleep(5 * (attempt + 1))
                    continue
                detail = e.read().decode(errors="replace")[:300]
                raise RuntimeError(f"teacher HTTP {e.code}: {detail}") from None
        self._last = time.time()
        content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        usage = data.get("usage") or {}
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"content": content, "usage": usage, "model": self.model, "tag": tag}, f, ensure_ascii=False)
        with open(LEDGER, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.time(), "model": self.model, "base_url": self.base_url, "tag": tag,
                                "prompt_tokens": usage.get("prompt_tokens"),
                                "completion_tokens": usage.get("completion_tokens")}) + "\n")
        return content

    def json(self, system: str, user: str, **kw):
        """chat() then parse the first JSON object/array in the reply (tolerates code fences)."""
        text = self.chat(system, user, json_mode=True, **kw)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
            if not m:
                raise ValueError(f"teacher returned no JSON: {text[:200]!r}")
            return json.loads(m.group(1))

    # --- accounting -----------------------------------------------------------------------
    @staticmethod
    def ledger_summary() -> dict:
        tot: dict[str, dict] = {}
        if not os.path.exists(LEDGER):
            return tot
        with open(LEDGER, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                m = tot.setdefault(r["model"], {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0})
                m["calls"] += 1
                m["prompt_tokens"] += r.get("prompt_tokens") or 0
                m["completion_tokens"] += r.get("completion_tokens") or 0
        return tot


if __name__ == "__main__":  # smoke: python -m pmrgb.teacher
    t = Teacher()
    print(f"teacher = {t.model} @ {t.base_url}")
    print(t.json("Reply with JSON only.", 'Return {"ok": true, "n": 3}'))
    print("ledger:", t.ledger_summary())
