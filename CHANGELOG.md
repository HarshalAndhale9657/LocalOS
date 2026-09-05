# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project aims to follow [Semantic Versioning](https://semver.org/) once released.

Safety- and privacy-relevant changes are additionally logged in
[`SAFETY_CHANGELOG.md`](SAFETY_CHANGELOG.md).

## [Unreleased]

### Added
- **Revised plan (`docs/07`)** under confirmed constraints (3–4 months, borrowed GPU laptop, Colab,
  small API budget, two teammates): one fine-tuning track (QA refusal), unification tested as a
  transfer hypothesis, action track deferred; consented on-device student evaluation (E9b).
- **Shared core:** prompts live once in `shared/prompts/` and are loaded verbatim by the extension
  (`lib/model/core.ts`, Vite `?raw`) and the benchmark (`pmrgb/core.py`); refusal/citation parsing
  is checked in both languages against `shared/tests/refusal_cases.json` (vitest + unittest, in CI).
- **Model harness** `benchmark/eval/run_model.py`: retrieval → shared prompt → Ollama → shared
  parser, with auditable per-item predictions (M1.6 plumbing).
- **Wikipedia revision miner** `benchmark/pmrgb/revisions.py`: real stale-vs-fresh fact pairs from
  article revision history (v1 staleness source) + `benchmark/sources/titles_v1_seed.txt`.

- **End-to-end runtime smoke test** `extension/e2e/smoke.mjs` (`npm run e2e`): real Chrome via the
  DevTools pipe (`installExtension`), fixture article, side-panel messages; 10/10 passing.

### Fixed
- **Offline embeddings actually offline:** onnxruntime-web fetched its WASM engine from a CDN and
  failed under the extension CSP ("no available backend found"). `npm run fetch-model` now bundles
  the engine into `public/ort/` and `lib/memory/embed.ts` loads it from the extension origin.

### Changed
- Default local model is now `qwen2.5:3b-instruct` (3B primary per docs/07 §5).
- Docs corrected where they overstated the code (safety changelog, spotlighting figure, v0 benchmark
  narrative); 12 nearest-neighbor papers added to `docs/04` with verified arXiv IDs.

### Added (M1)
- **Planning knowledge base** (`docs/00`–`docs/06`): vision, product plan, technical
  architecture, research-paper plan, related-work bibliography, the Personal-Memory-RGB
  benchmark spec, and the M1 build plan.
- **Extension scaffold** (`extension/`, WXT + React + MV3): side panel, offscreen ML host,
  background message router, and the `lib/` subsystem skeleton (observe/act/memory/model/safety).
- **M1.2 Observe:** CDP accessibility-tree snapshot → compressed indexed nodes with a
  change-detecting `versionId` and executor-only `backendNodeId`; `OBSERVE_ACTIVE_TAB` route.
- **M1.3 Act:** CDP executor mapping element `index → backendNodeId → CDP` (click/type/scroll/
  navigate) with a stale-snapshot guard and SAFE/CAUTION/UNSAFE confirmation gating.
- **M1.4 Memory:** local RAG pipeline — Readability capture → chunk → SimHash dedup →
  transformers.js embeddings → PGlite store → retrieve (cosine + time-decay + MMR +
  negative-rejection); wired into the side panel ("Remember page" + "Ask").
- **Offline embedding model:** `npm run fetch-model` bundles `bge-small-en-v1.5` (quantized
  ONNX) locally; transformers.js configured for local-only load (no HF Hub call at runtime).
- **M1.5 Grounded answering (QA half):** Ollama client with a grounded-QA prompt (inline
  `[n]` citations, calibrated "Not found in your history." refusal, spotlighted sources);
  `ASK` route degrades to retrieval-only when Ollama is unreachable.
- **Agentic task loop + action UI:** `model.act()` decides the next action from a spotlighted
  observation; `lib/agent` runs observe → decide → risk-gate → confirm → act → re-observe
  (cancelable, step-limited), streaming events to the panel. Side panel adds an Ask/Do mode
  toggle, a live action log, a confirmation card (Approve/Reject) for non-SAFE actions, and Stop.
- **Settings & privacy panel:** typed `lib/settings` persisted in `chrome.storage`; a capture
  on/off toggle and a sensitive-domain **blocklist that gates capture** (banking/webmail/health/
  messaging/password-manager defaults), a local-model picker (used by ASK + the agent loop), and
  a one-click **wipe all memory** (two-step confirm). Reachable via a gear in the side panel.
- **Personal-Memory-RGB v0 benchmark:** synthetic-history generator (6 question classes),
  train/dev/test split by history, and an evaluation harness (refusal precision/recall/F1,
  decision accuracy, risk-coverage, abstention AUROC) with a BM25 + threshold-abstention
  reference system.
- **Project scaffolding:** `CLAUDE.md`, `LICENSE` (MIT), `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SAFETY_CHANGELOG.md`, `CITATION.cff`, CI workflow,
  GitHub issue/PR templates, `.editorconfig`, `.gitattributes`, `.nvmrc`, and a benchmark
  datasheet.

### Notes
- Extension changes are **build- and typecheck-verified**; CDP/PGlite/embeddings/Ollama
  runtime behavior requires a Chrome load and is noted as such.
- Model weights and generated data are gitignored (fetched/generated locally).

[Unreleased]: https://github.com/HarshalAndhale9657/Groundwork/commits/main
