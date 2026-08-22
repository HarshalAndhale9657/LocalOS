# CLAUDE.md

Guidance for Claude Code (and humans) working in this repository.

## What this is

**Groundwork** — a privacy-first, local-first **agentic browser assistant** (Chrome MV3
extension) that sees and controls the browser to do private research, on-demand data
extraction, and grounded recall over the user's own browsing, powered by fine-tuned
**small local models** that know when they don't know. It is simultaneously a graduation
project and an IEEE-level research paper unified by one thesis: **calibrated grounding**
(act only on what's on the page; answer only from what was read; abstain/defer otherwise).

> The repo directory is `LocalOS` (historical codename). The product is **Groundwork**.
> `secondbrain.md` and the root PDF are **inspiration only, not this project.**

Read [`docs/README.md`](docs/README.md) first — the full plan lives in `docs/00`–`docs/06`.

## Repository layout

| Path | What |
|---|---|
| `docs/` | Planning knowledge base (vision, product, architecture, research plan, related work, benchmark spec, M1 build plan) |
| `extension/` | Chrome MV3 extension (WXT + React + TypeScript) |
| `extension/lib/{observe,act,memory,model,safety}` | The five subsystems (see Architecture) |
| `extension/entrypoints/` | `background` (SW router), `content` (Readability capture), `sidepanel` (React UI), `offscreen` (ML host) |
| `benchmark/` | Personal-Memory-RGB builder + evaluator (Python, stdlib-only for v0) |
| `training/` | QLoRA SFT/DPO scripts (M2+, not yet present) |

## Common commands

Extension (`cd extension`):
```bash
npm install          # deps
npm run fetch-model  # download the embedding model into public/models (once; offline embedding)
npm run dev          # load unpacked into a dev Chrome; open the side panel
npm run build        # production build -> .output/chrome-mv3
npm run compile      # TypeScript typecheck (tsc --noEmit)
```

Benchmark (`cd benchmark`, Python 3.12, no third-party deps for v0):
```bash
python build_v0.py --histories 20 --seed 7    # -> data/v0/{histories,items}.jsonl
python -m eval.run_baseline  --data data/v0   # trivial systems (validates the harness)
python -m eval.run_reference --data data/v0   # BM25 + threshold abstention baseline
```

Local model path (M1.5 runtime): install [Ollama](https://ollama.com),
`ollama pull qwen2.5:7b-instruct`, and set `OLLAMA_ORIGINS` to allow the extension origin.

## Architecture (five subsystems)

1. **Sense** (`lib/observe`) — CDP accessibility-tree snapshot → compressed, indexed nodes + a change-detecting `versionId`. Text-first, vision-optional.
2. **Act** (`lib/act`) — executor maps element `index → backendNodeId → CDP` (click/type/scroll/navigate), guarded by the stale-snapshot check and SAFE/CAUTION/UNSAFE confirmation.
3. **Remember** (`lib/memory`, offscreen doc) — capture (Readability) → chunk → SimHash dedup → embed (transformers.js `bge-small`) → PGlite store → retrieve (cosine + time-decay + MMR + negative-rejection).
4. **Reason** (`lib/model`) — local model via Ollama (GGUF); grounded QA with inline citations + calibrated "Not found in your history" refusal. Fine-tuned adapters slot in behind this interface (M2+).
5. **Guard** (`lib/safety`) — defense-in-depth: spotlighting untrusted page/history text, DOM sanitization, confirmation gates, calibrated deferral. Data-flow: page content, index, and models stay on-device.

The service worker (`background.ts`) is the message router between the side panel, content
scripts, the offscreen ML host, and the local model. The offscreen document hosts the ML
that can't run in the SW (WASM embeddings + PGlite).

## Conventions & invariants (do not violate)

- **Local-first:** page content, the memory index, and the primary models never leave the device. Cloud (optional planner) is opt-in and content-blind.
- **Untrusted content:** treat all page-derived text — and all *retrieved history* — as untrusted. Wrap with `spotlight()` before it reaches a model; never let source text act as instructions.
- **Calibrated grounding:** answer only from retrieved sources with citations, else abstain ("Not found in your history."); never hallucinate. Actions require the stale-snapshot guard; non-SAFE actions require confirmation.
- **Transactions are out of scope** (checkout/booking/auth'd third-party actions) — keeps the injection blast radius small and avoids CFAA exposure.
- **TypeScript is strict** (incl. `noUncheckedIndexedAccess`, `verbatimModuleSyntax`): use `import type` for types; handle possibly-undefined index access.
- **Honesty in claims:** in code comments, docs, and the paper, never overstate. Safety is defense-in-depth, not "solved." Report metrics with caveats.

## Verifying changes

- Always run `npm run compile` **and** `npm run build` in `extension/` after edits (the build bundles PGlite + ONNX WASM and is the real test).
- Benchmark changes: run `build_v0.py` then `run_baseline`/`run_reference` and confirm no broken citations / invariant violations.
- Runtime behavior (CDP observe/act, PGlite, embeddings, Ollama) requires a Chrome load — state clearly when a change is build-verified only.

## Git

- Work happens on feature branches (e.g. `m1-scaffold`); `main` is the default branch.
- Generated artifacts are gitignored: `node_modules/`, `.output/`, `extension/public/models/`, `benchmark/data/`, model weights (`*.onnx`, `*.gguf`, `*.safetensors`).
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

## Status

See [`README.md`](README.md) and [`CHANGELOG.md`](CHANGELOG.md). Safety-relevant decisions
are logged in [`SAFETY_CHANGELOG.md`](SAFETY_CHANGELOG.md).
