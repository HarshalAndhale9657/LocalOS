# Changelog

All notable changes to this project are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the
project aims to follow [Semantic Versioning](https://semver.org/) once released.

Safety- and privacy-relevant changes are additionally logged in
[`SAFETY_CHANGELOG.md`](SAFETY_CHANGELOG.md).

## [Unreleased]

### Added
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
