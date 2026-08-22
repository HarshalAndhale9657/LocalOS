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
- 🧠 **M1.4 memory implemented** (builds + typechecks): capture (Readability) → chunk → SimHash-dedup → transformers.js embeddings → PGlite store → retrieve (cosine + time-decay + MMR + negative-rejection), wired into the side panel ("Remember page" + "Ask"). *Runtime pending a Chrome load.*
- 📦 **Offline embedding model bundled:** `npm run fetch-model` downloads `bge-small-en-v1.5` (quantized ONNX) into `public/models/` (gitignored) and transformers.js is configured to load it locally — **no HF Hub call at runtime**. Remaining caveats: JS-side cosine (pgvector/HNSW later); confirm the ORT-wasm runtime loads from the bundled asset offline; PGlite's `eval` vs the extension CSP — all to check on a Chrome load.
- 👁 **M1.2 observe + 🖱 M1.3 act implemented** (build + typecheck): CDP a11y snapshot → compressed indexed nodes + `versionId`; executor maps `index → backendNodeId → CDP` (click/type/scroll/navigate) with a stale-snapshot guard + SAFE/CAUTION/UNSAFE confirmation gate.
- 💬 **M1.5 grounded answering (QA half) implemented** (build + typecheck): Ollama client with a grounded-QA prompt (inline `[n]` citations + calibrated "Not found in your history" refusal, sources spotlighted as untrusted); side-panel "Ask" wired, degrades to retrieval-only if Ollama is down. **The priority QA track is now end-to-end** (runtime needs Ollama).
- ⏭ Next: install Ollama & verify the QA loop in Chrome → M1.6 (extension vs Personal-Memory-RGB base number) → the deciding agent loop for actions + confirmation UI/action log. See [`docs/06`](docs/06_M1_BUILD_PLAN.md).

## Develop the extension

```bash
cd extension
npm install
npm run dev      # loads unpacked into a dev Chrome; open the side panel
npm run build    # production build → extension/.output/chrome-mv3
npm run compile  # typecheck
```

For the local model path (M1.5): install [Ollama](https://ollama.com), `ollama pull qwen2.5:7b-instruct`, and allow the extension origin via `OLLAMA_ORIGINS`.
