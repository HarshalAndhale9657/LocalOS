# 06 — M1 Build Plan

> The first engineering milestone: stand up a **runnable Groundwork extension** that can *observe* a page, *act* (read-oriented) on it, *remember* via local RAG, and answer **grounded, cited, refusable** questions with a **base model** — plus an eval harness that produces the **base-model baseline** against [Personal-Memory-RGB](05_BENCHMARK_Personal_Memory_RGB.md). Everything after M1 is *improving* this baseline. Maps to [01 §8 roadmap](01_PRODUCT_PLAN.md) Month 1.

---

## 1. Definition of done for M1

- [ ] Extension loads in Chrome (unpacked), opens a **side panel** chat.
- [ ] **Observe:** on the active tab, produce a compressed observation (Readability text + accessibility-tree snapshot with element indices + version-id).
- [ ] **Act (SAFE only):** navigate / scroll / click-link / open-tab via CDP, each shown in a visible **action log**; state-changing actions are gated behind a confirmation stub.
- [ ] **Remember:** capture → clean → SimHash-dedup → chunk → embed (in offscreen doc) → store in PGlite/pgvector; hybrid retrieve + rerank works.
- [ ] **Answer:** grounded QA with inline citations **or** "not found in your history", using a **base** local model via Ollama (no fine-tuning yet).
- [ ] **Baseline:** eval harness runs the base model over Personal-Memory-RGB **v0** and logs refusal P/R + RAGAS + citation metrics.
- [ ] Privacy basics: default sensitive-domain blocklist + capture on/off toggle + wipe.

**Why this DoD:** it makes the product *demonstrable* and gives the paper its **base (untuned) baseline** — the thing every fine-tuning result is measured against ([03 §6](03_RESEARCH_PAPER_PLAN.md)).

---

## 2. Toolchain status (verified 2026-08-21)

| Tool | Status | Note |
|---|---|---|
| Node | ✅ v22.17.0 | fine for WXT |
| npm | ✅ 10.9.2 | (pnpm optional; not installed) |
| git | ✅ 2.50.1 | repo already initialized |
| Python | ✅ 3.12.0 | for data pipeline + training scripts |
| **Ollama** | ❌ **not installed** | **Action item:** install from ollama.com to serve local GGUF models; set `OLLAMA_ORIGINS` to allow the extension origin |

---

## 3. Key build decision: scaffold our own, *study* Nanobrowser

The plan earlier said "fork Nanobrowser." On reflection, for a **graduation project + research paper you must own and understand**, we will **build our own WXT + MV3 + React scaffold** and **use Nanobrowser (and browser-use) as architectural references**, not a wholesale fork. Rationale:

- **Ownership/defensibility:** committee + reviewers expect code you can explain; a vendored third-party extension muddies authorship and license.
- **Cleanliness:** we only need a few patterns from Nanobrowser (CDP observe/act, the Planner/Navigator/Validator loop, the Ollama call path) — copy the *ideas*, cite the *source*.
- **Right-sized:** our action space is read-oriented (research/extraction), smaller than Nanobrowser's full automation surface.

We will keep a `REFERENCES.md` in the app noting which patterns were informed by Nanobrowser/browser-use (Apache-2.0) for honest attribution.

---

## 4. Proposed repo structure

```
d:\LocalOS\
├─ docs\                     # planning docs (done)
├─ extension\                # the Chrome MV3 extension (WXT + React)  ← M1
│  ├─ entrypoints\
│  │  ├─ background.ts       # service worker: router, RAG, safety, CDP orchestration
│  │  ├─ content.ts          # Readability + DOM/a11y extraction, action executor
│  │  ├─ sidepanel\          # React chat UI, action log, citations, privacy panel
│  │  └─ offscreen\          # transformers.js embeddings + PGlite/pgvector host
│  ├─ lib\
│  │  ├─ observe\            # a11y-tree compression, element indexing, version-id
│  │  ├─ act\                # action space, CDP input dispatch, risk labels/gates
│  │  ├─ memory\             # capture/clean/dedup(SimHash)/chunk/embed/retrieve/rerank
│  │  ├─ model\              # Ollama client, prompt templates, escalation router
│  │  └─ safety\             # spotlighting, DOM sanitizer, confirmation policy
│  ├─ wxt.config.ts
│  └─ package.json
├─ benchmark\                # Personal-Memory-RGB construction + loader + evaluator  ← M1–M6
│  ├─ build\                 # history assembler, QA generator, NLI verify gate
│  ├─ data\                  # generated histories + items (gitignored until release)
│  └─ eval\                  # RAGAS/ALCE/refusal metrics, local judge
├─ training\                 # QLoRA SFT/DPO scripts (Unsloth) — M2+
└─ README.md
```

---

## 5. M1 tickets

| # | Ticket | Acceptance | Refs |
|---|---|---|---|
| **M1.1** | Scaffold WXT MV3 React project (`extension/`): background SW, content script, side panel, offscreen doc; manifest perms `activeTab, tabs, scripting, sidePanel, storage, debugger` + narrow hosts; CSP `wasm-unsafe-eval` | `npm run dev` loads; side panel opens; hello-world message round-trips SW↔panel↔content | [02 §7](02_TECHNICAL_ARCHITECTURE.md) |
| **M1.2** | **Observe:** content-script Readability + CDP `Accessibility.getFullAXTree`/`DOMSnapshot` → compressed observation (interactive+visible nodes, element index, version-id); cache + diff | Given a page, returns a stable JSON observation < ~13k tokens on heavy pages | [02 §2](02_TECHNICAL_ARCHITECTURE.md) |
| **M1.3** | **Act (SAFE):** action space enum + CDP `Input.dispatch*` executor for navigate/scroll/click-link/open-tab; **action log** in panel; confirmation stub for CAUTION/UNSAFE; version-id check before acting | Agent can navigate + scroll + click a link; each logged; a form-submit is blocked pending confirmation | [02 §3](02_TECHNICAL_ARCHITECTURE.md) |
| **M1.4** | **Memory:** offscreen doc hosts transformers.js (`bge-small`/`nomic`, Matryoshka 128–256) + PGlite/pgvector (HNSW); capture→clean→SimHash-dedup→chunk(400–512, no overlap)→embed→store; hybrid dense+BM25 (RRF) → `bge-reranker-v2-m3`; time-decay+MMR; low-score ⇒ abstain signal | Visit 10 pages → indexed; a query returns ranked chunks with scores; near-dups collapsed | [02 §4](02_TECHNICAL_ARCHITECTURE.md) |
| **M1.5** | **Model wiring (base):** Ollama client; prompt template for grounded QA with inline citations + explicit "not found in your history" refusal; wire retrieval→prompt→answer→citation-chips in panel | Ask a question about a read page → cited answer; ask about an unread topic → refusal | [02 §5](02_TECHNICAL_ARCHITECTURE.md) |
| **M1.6** | **Eval harness skeleton:** load Personal-Memory-RGB v0; run the base model end-to-end; compute refusal P/R + RAGAS faithfulness/context-precision + ALCE citation P/R; dump a results table | One command produces the **base-model baseline** table | [05](05_BENCHMARK_Personal_Memory_RGB.md), [03 §5](03_RESEARCH_PAPER_PLAN.md) |
| **M1.7** | **Privacy basics + polish:** default sensitive blocklist, capture toggle, one-click wipe; brief onboarding | Blocklisted domains never captured; wipe empties the index | [01 §5](01_PRODUCT_PLAN.md) |

Suggested order: M1.1 → M1.2 → M1.4 → M1.5 → M1.3 → M1.6 → M1.7 (get *observe + memory + grounded answer* working before the action layer, since the QA-refusal track is the priority deliverable).

---

## 6. Setup commands (run in `d:\LocalOS`)

```bash
# 1. scaffold the extension (WXT + React)
npx --yes wxt@latest init extension --template react --pm npm
cd extension && npm install

# 2. add the core deps
npm install @electric-sql/pglite @huggingface/transformers @mozilla/readability

# 3. run in dev (loads unpacked into a Chrome instance)
npm run dev

# 4. (separately) install Ollama from https://ollama.com , then:
ollama pull qwen2.5:7b-instruct        # base model for the M1.5 baseline
#   set OLLAMA_ORIGINS to allow the extension origin (see Ollama docs)
```

*(Exact package names/versions confirmed at scaffold time; `@huggingface/transformers` is the maintained successor to `@xenova/transformers`.)*

---

## 7. Risks & notes specific to M1

- **`chrome.debugger` shows a banner** ("X is debugging this browser"). Acceptable for dev/research; document it; it's the price of trusted CDP input + keeping the SW alive.
- **MV3 service-worker death:** keep an active CDP session during agent loops; checkpoint state to `chrome.storage`.
- **Offscreen doc for ML:** WebGPU in workers is unreliable — host embeddings in the **offscreen document**, not the SW.
- **Ollama dependency:** the local-model path needs Ollama running; the extension should detect its absence and degrade to "memory/observe only" gracefully.
- **Don't gold-plate the action layer in M1** — SAFE actions are enough to demo research/extraction; the trained action model + deferral come in M4.

---

## 8. What M1 unlocks

- A **working, demoable product** (observe + remember + cited/refusable answers).
- The **base-model baseline** for the paper.
- A stable substrate to plug the **QA adapter** (M2–M3) then the **action adapter** (M4) into — turning the base baseline into the paper's headline results.

---

*Prev: [05 — Benchmark spec](05_BENCHMARK_Personal_Memory_RGB.md). Up: [README](README.md).*
