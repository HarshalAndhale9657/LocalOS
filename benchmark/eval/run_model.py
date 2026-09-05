"""Model-based evaluation harness (M1.6): run a local model through Ollama on Personal-Memory-RGB
using the PRODUCT'S OWN prompt and parser (shared/prompts + pmrgb/core.py), so the numbers describe
the extension and not a re-implementation (docs/07 §10.1).

System = retrieval over the item's own history -> top-k chunks -> shared grounded-QA prompt ->
Ollama chat (temperature 0) -> shared refusal/citation parser -> decision metrics.

v0 retrieval here is BM25 (stdlib). The dense retriever the extension uses arrives with the v1
harness (optional deps). Every output row records prompt_version, model, retriever, and the raw
model text so runs are auditable.

Usage:
  python -m eval.run_model --data data/v0 --model qwen2.5:3b-instruct --split test
  python -m eval.run_model --data data/v0 --limit 6            # smoke test
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pmrgb import core  # noqa: E402
from .retriever import BM25  # noqa: E402
from .metrics import refusal_metrics, auroc  # noqa: E402

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")


def load(path):
    def jl(name):
        with open(os.path.join(path, name), encoding="utf-8") as f:
            return [json.loads(l) for l in f if l.strip()]
    return jl("histories.jsonl"), jl("items.jsonl")


def chat(model: str, system: str, user: str, timeout: int = 300) -> str:
    body = json.dumps({
        "model": model, "stream": False, "options": {"temperature": 0},
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }).encode()
    req = urllib.request.Request(f"{OLLAMA}/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())["message"]["content"].strip()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/v0")
    ap.add_argument("--model", default="qwen2.5:3b-instruct")
    ap.add_argument("--split", default="test", help="test | dev | train | all")
    ap.add_argument("--k", type=int, default=4, help="retrieved chunks per question (extension uses 4)")
    ap.add_argument("--limit", type=int, default=0, help="stop after N items (smoke test)")
    ap.add_argument("--out", default=None, help="JSONL of per-item predictions (default: data/<split>_<model>.preds.jsonl)")
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    histories, items = load(args.data)
    if args.split != "all":
        items = [it for it in items if it.get("split", "all") == args.split]
    if args.limit:
        items = items[: args.limit]
    if not items:
        sys.exit(f"no items for split={args.split}")

    # per-history retrievers over chunk text (page metadata is joined for the prompt)
    chunk_meta = {}
    retr = {}
    for h in histories:
        docs = []
        for p in h["pages"]:
            for c in p["chunks"]:
                did = f"{p['page_id']}::{c['chunk_id']}"
                docs.append((did, c["text"]))
                chunk_meta[did] = {"title": p["title"], "url": p["url"], "read_at": p["read_at"], "text": c["text"]}
        retr[h["history_id"]] = BM25(docs)

    out_path = args.out or os.path.join(args.data, f"{args.split}_{args.model.replace(':', '_').replace('/', '_')}.preds.jsonl")
    system = core.qa_system_prompt()
    preds, rows = {}, []
    t0 = time.time()
    for i, it in enumerate(items, 1):
        ranked = retr[it["history_id"]].score(it["question"])[: args.k]
        top_score = ranked[0][1] if ranked else 0.0
        sources = [chunk_meta[d] for d, s in ranked if s > 0]
        if not sources:  # mirrors LocalModel.answer(): nothing retrieved -> abstain without a model call
            raw, parsed = "", {"decision": "abstain", "text": core.REFUSAL, "cited": []}
        else:
            user = core.qa_user_prompt(it["question"], sources)
            try:
                raw = chat(args.model, system, user)
            except (urllib.error.URLError, TimeoutError) as e:
                sys.exit(f"Ollama unreachable or timed out ({e}). Is the Ollama app running and is '{args.model}' pulled?")
            parsed = core.parse_answer(raw, len(sources))
        preds[it["id"]] = parsed["decision"]
        rows.append({
            "id": it["id"], "type": it["type"], "gold_decision": it["gold_decision"], "gold_answer": it.get("gold_answer"),
            "pred_decision": parsed["decision"], "pred_text": parsed["text"], "cited": parsed["cited"],
            "retrieval_top_score": top_score, "n_sources": len(sources), "raw": raw,
            "model": args.model, "prompt_version": core.prompt_version(), "retriever": f"bm25@k{args.k}",
        })
        el = time.time() - t0
        print(f"[{i}/{len(items)}] {it['type']:<16} gold={it['gold_decision']:<7} pred={parsed['decision']:<7} "
              f"({el/i:.1f}s/item)  {parsed['text'][:70]!r}")

    with open(out_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    gold = {it["id"]: it["gold_decision"] for it in items}
    m = refusal_metrics(gold, preds)
    ids = [it["id"] for it in items]
    labels = [1 if gold[i] == "abstain" else 0 for i in ids]
    by_id = {r["id"]: r for r in rows}
    smax = max((r["retrieval_top_score"] for r in rows), default=1.0) or 1.0
    au_retr = auroc([1.0 - by_id[i]["retrieval_top_score"] / smax for i in ids], labels)
    au_dec = auroc([1.0 if by_id[i]["pred_decision"] == "abstain" else 0.0 for i in ids], labels)

    print(f"\nModel: {args.model}   split={args.split}   n={len(items)}   prompt_version={core.prompt_version()}")
    print(f"  abstain P/R/F1 = {m['abstain_precision']:.3f} / {m['abstain_recall']:.3f} / {m['abstain_f1']:.3f}"
          f"   decision_acc = {m['decision_accuracy']:.3f}")
    print(f"  abstention AUROC: model decision = {au_dec:.3f}   retrieval-score signal = {au_retr:.3f}")
    per = defaultdict(lambda: [0, 0])
    for it in items:
        per[it["type"]][0] += int(preds[it["id"]] == it["gold_decision"])
        per[it["type"]][1] += 1
    print("  per-type decision accuracy:")
    for t in sorted(per):
        c, n = per[t]
        print(f"    {t:<16} {c/n:.3f}  ({c}/{n})")
    print(f"  predictions -> {out_path}")


if __name__ == "__main__":
    main()
