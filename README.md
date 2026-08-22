# Groundwork

**A privacy-first, local-first *agentic browser assistant* (Chrome MV3) that sees and controls your browser to do private research, on-demand data extraction, and grounded recall — powered by fine-tuned small local models that know when they don't know.**

Graduation / major project **and** an IEEE-level-and-above research paper, unified by one thesis: **calibrated grounding** — act only on what's on the page, answer only from what you actually read, and abstain/defer otherwise.

> The repo directory is `LocalOS` (historical codename); the product is **Groundwork**.
> The root files `secondbrain.md` and `Second_Brain_Project_Documentation_Professional.pdf` are **inspiration only, not this project.**

## Layout

| Path | What |
|---|---|
| [`docs/`](docs/) | Full planning knowledge base — start at [`docs/README.md`](docs/README.md) |
| [`extension/`](extension/) | The Chrome MV3 extension (WXT + React) — **M1 scaffold, builds & typechecks** |
| [`benchmark/`](benchmark/) | Personal-Memory-RGB builder + evaluator (spec: [`docs/05`](docs/05_BENCHMARK_Personal_Memory_RGB.md)) — **v0 runs (stdlib-only)** |
| `training/` | QLoRA SFT/DPO scripts — *to come (M2+)* |

## Status (2026-08-21)

- ✅ Planning complete (vision, product, architecture, research plan, related work, benchmark spec, M1 plan).
- 🔨 **M1.1 done:** extension scaffold — side panel, offscreen ML host, background router, `lib/` skeleton (observe/act/memory/model/safety). Builds + typechecks.
- 🔬 **Benchmark v0 done:** `benchmark/` generates synthetic Personal-Memory-RGB data (all 6 classes) + a working refusal-metrics eval harness (validated: 0 broken citations; oracle 1.0 vs trivial baselines; BM25 reference system on held-out test). Teacher-LLM enrichment + action-safety split come in M2/M4.
- 🧠 **M1.4 memory implemented** (builds + typechecks): capture (Readability) → chunk → SimHash-dedup → transformers.js embeddings → PGlite store → retrieve (cosine + time-decay + MMR + negative-rejection), wired into the side panel ("Remember page" + "Ask"). *Runtime pending a Chrome load.* Caveats: v1 uses JS-side cosine (pgvector/HNSW is a drop-in later); embedding model is fetched from the HF Hub on first use (bundle it for true offline — follow-up); PGlite's direct `eval` vs the extension CSP needs a runtime check.
- ⏭ Next: verify M1.4 in Chrome + bundle the embedding model → M1.2 observe (CDP a11y) → M1.5 grounded answering (base model via Ollama → first Personal-Memory-RGB number). See [`docs/06`](docs/06_M1_BUILD_PLAN.md).

## Develop the extension

```bash
cd extension
npm install
npm run dev      # loads unpacked into a dev Chrome; open the side panel
npm run build    # production build → extension/.output/chrome-mv3
npm run compile  # typecheck
```

For the local model path (M1.5): install [Ollama](https://ollama.com), `ollama pull qwen2.5:7b-instruct`, and allow the extension origin via `OLLAMA_ORIGINS`.
