# 02 — Technical Architecture & Feasibility

> Companion to [01_PRODUCT_PLAN](01_PRODUCT_PLAN.md). This is the buildable blueprint: how LocalOS *sees*, *acts*, *remembers*, *reasons locally*, and *stays safe* — with the MV3 constraints and mitigations that make it feasible on a single consumer GPU. Feasibility grounded in the deep-research pass; citations in [04_RELATED_WORK](04_RELATED_WORK.md).

---

## 1. Architecture at a glance

LocalOS is a **hybrid, local-first** system with five subsystems:

1. **Sense** — observe the page (content script + CDP; Readability + compressed accessibility tree).
2. **Act** — execute browser actions via trusted CDP input events, gated by risk + confirmation.
3. **Remember** — local RAG memory over browsing history (PGlite + pgvector, in-browser embeddings).
4. **Reason (local)** — two fine-tuned small models (action grounding; grounded QA/refusal) served via Ollama/llama.cpp.
5. **Escalate + Guard** — optional content-blind cloud planner; safety layer (spotlighting, CaMeL split, calibration).

```
                         ┌────────────── SIDE PANEL (React) ──────────────┐
                         │ chat · citations · action log · risk gates      │
                         └───────────────▲───────────────┬────────────────┘
                                         │ messages       │ user intent
┌──────────── SERVICE WORKER (background, MV3) ───────────▼────────────────┐
│ Router → Consent/Blocklist gate → DOM Sanitizer → Spotlighting           │
│   ├─ RAG pipeline: retrieve (dense+BM25/RRF) → rerank → time-decay → MMR  │
│   ├─ Calibration: conformal / Semantic-Entropy-Probe refusal-deferral gate│
│   ├─ Risk head: SAFE / CAUTION / UNSAFE  → confirmation policy            │
│   └─ Escalation router: local ⇄ (optional) cloud planner                 │
└──────▲───────────────▲────────────────────────────────▲─────────────────┘
       │ a11y snapshot  │ trusted actions (CDP)          │ inference
┌──────┴──────┐  ┌──────┴───────┐               ┌────────┴─────────────────┐
│ CONTENT     │  │ chrome.       │               │ LOCAL SIDECAR             │
│ SCRIPT      │  │ debugger (CDP)│               │ Ollama / llama.cpp        │
│ Readability │  │ DOMSnapshot   │               │ GGUF Q4_K_M               │
│ a11y/DOM    │  │ Accessibility │               │ ├ action-grounding adapter│
│ extraction  │  │ Input.dispatch│               │ └ grounded-QA/refusal     │
└─────────────┘  └───────────────┘               └───────────────────────────┘
┌───────────── OFFSCREEN DOCUMENT (ML host) ───────────────────────────────┐
│ transformers.js / ONNX embeddings (bge-small / nomic, Matryoshka 128–256)│
│ PGlite + pgvector (HNSW) over IndexedDB  ·  encrypted  ·  CS-isolated     │
└──────────────────────────────────────────────────────────────────────────┘
        (optional, opt-in, content-blind) → Cloud LLM planner (BYO key)
```

---

## 2. Sense — page observation

**Why the accessibility tree, not raw DOM or screenshots.** The a11y/semantic tree compresses a page to ~5–10% of raw DOM nodes (~12.6k vs 43k+ tokens), fits a 3B–8B context, and — per the 2025 "Beyond Pixels" ablation and SeeAct — carries the signal that matters. Screenshots add little once structured input + grounding are good, and Set-of-Mark grounding is *weak* on dense real webpages. So: **text-first, vision-optional.**

**Pipeline.**
1. **Content script** injects into the active tab; extracts readable content with **Readability.js** and walks the DOM for interactive elements.
2. **CDP** (`chrome.debugger`) pulls `DOMSnapshot` + `Accessibility.getFullAXTree` for a structured, most-recent-snapshot observation. (CDP also keeps the service worker alive — see §7.)
3. **Compressor** prunes to an on-task, budget-aware subset: interactive + visible + semantically-relevant nodes, each assigned a stable **element INDEX** and a **snapshot version-id**.
4. **DOM Sanitizer** (safety, §6) down-weights/marks hidden, off-screen, off-task, and freshly-injected elements; unexpected new UI becomes a deferral trigger.

**Observation object (to the model):** `{ goal, url, ax_snapshot(version_id, [ {index, role, name, value, state} ]), recent_actions[], retrieved_history_exemplars[] }`.

**Latency note.** `buildDomTree.js`-style full rebuilds are ~5–6 s on heavy pages. Mitigation: CDP Accessibility + snapshot caching + version-id diffing + most-recent-only compression; rebuild only on real navigation/mutation.

---

## 3. Act — the action layer

**Action space (fixed, small vocabulary):**
`click(index)`, `type(index, text)`, `select(index, option)`, `scroll(dir|index)`, `navigate(url|back|forward)`, `open_tab / switch_tab(id)`, `extract(fields)`, `wait`, `ask_user(question)` (**deferral**), `done(answer|result)`.

**Element-INDEX actions, not coordinates.** The model emits `verb + element_index` (+ args). Before executing, the executor verifies the snapshot **version-id** still matches (guards against state divergence). Index-based actions are easier to SFT/DPO and deterministically checkable vs coordinate clicking.

**Execution channel:** CDP `Input.dispatchMouseEvent` / `dispatchKeyEvent` produce **trusted** input events (more reliable than synthetic JS clicks; survive many anti-bot checks; and are what keeps the worker alive).

**Optional functional-token decoding.** Following Octopus, the fixed verb+index vocabulary can be encoded as special tokens to cut action context ~95% and latency — an on-device optimization and a paper ablation.

**Guarded by default:** `SAFE` actions (navigate/scroll/read/extract) auto-execute; anything **state-changing** (`type` into forms, `click` submit-like elements) is `CAUTION`/`UNSAFE` → confirmation card with the target element highlighted. Low element-confidence → `ask_user` (deferral) instead of a blind click.

---

## 4. Remember — local RAG memory subsystem

Reuses and hardens the Second Brain pattern; runs **server-free, in-browser**.

**Capture → clean → dedup → chunk → embed → store:**
- **Capture:** opt-in, allow/block-listed; SPA-aware (MutationObserver + `pushState`/`replaceState`).
- **Clean:** Readability + per-domain boilerplate stripping.
- **Dedup:** SimHash (64-bit) + Hamming distance to collapse re-visits / near-duplicate SPA states.
- **Chunk:** recursive **400–512 tokens, no overlap** (2026 evidence: overlap gives no benefit; semantic chunking ~+9% recall).
- **Embed:** `bge-small-en-v1.5` (384-d, 32 MB int8) or `nomic-embed-v1.5` (**Matryoshka** → truncate to **128–256 dims** to shrink the IndexedDB index) via **transformers.js/ONNX in the offscreen document**.
- **Store:** **PGlite + pgvector** (HNSW; sub-20 ms, >95% recall) over IndexedDB; **encrypted**, isolated from content scripts.

**Retrieve (hybrid):**
1. Dense ANN (low-dim Matryoshka) **+ BM25**, merged via **RRF**.
2. **Cross-encoder rerank** (`bge-reranker-v2-m3`) at full 768-d (hybrid + rerank ≈ +17–39% Recall@5 in 2026 benchmarks).
3. **Time-decay** (exponential) + **MMR** diversity + document-diversity + negative-rejection threshold.
4. **Low top-rerank score ⇒ abstain** ("not found in your history") — the retrieval-side calibration signal.

**Retrieved history is untrusted** (it may carry text injected on a past visit — see cross-session injection, §6).

---

## 5. Reason (local) — model serving & the two tracks

**Two adapters on one shared base** (default; halves footprint):

| Track | Input → Output | Base | Training |
|---|---|---|---|
| **Action grounding** | goal + a11y snapshot + history exemplars → `verb + index (+args)` or `ask_user` | Qwen2.5-7B / Qwen3-4B (or 3B tier) | distill (teacher) → execute-verified SFT (+negatives) → DPO on mined failures; conformal deferral head |
| **Grounded QA / refusal** | question + retrieved chunks → cited answer **or** "not found in your history" | same base, second LoRA | Trust-Align-style SFT (pos/neg + NLI citations) → DPO on hallucination-vs-refusal pairs |

**Serving:** fine-tuned adapters merged/exported to **GGUF Q4_K_M**, served by **Ollama / llama.cpp** natively (7B ≈ 5 GB, 3B ≈ 2 GB). The extension reaches the sidecar over **localhost** (`OLLAMA_ORIGINS` must allow the extension origin) or **native messaging**. **Not WebLLM** for the main models (browser inference is 5–10× slower than native).

**Router-driven loading:** keep one adapter hot at a time to fit consumer memory; the escalation router decides local-vs-cloud and which adapter to load.

**Why on-device is credible (feasibility):** QLoRA on 3B–8B fits a single 16–24 GB GPU (~7 GB peak for 8B via Unsloth); GGUF Q4_K_M keeps quality within ~6% perplexity while fitting laptop VRAM. Small fine-tuned models beating zero-shot GPT-4V (WebLINX) and 8B beating GPT-4-Turbo on WebArena-Lite (WebRL) de-risk the accuracy question.

---

## 6. Escalate + Guard — routing, safety & privacy

### 6.1 Escalation router (hybrid)
A calibrated router decides per-step: **local** (default) vs **cloud planner** (optional, if a BYO key is set). Escalate only on hard multi-step or low-confidence steps. The paper reports the **success-vs-$/latency/token** curve and offline-mode degradation. **The cloud planner is content-blind:** it receives an approved, abstracted plan/goal representation — never raw page text or history.

### 6.2 Safety architecture (defense-in-depth — never "solved")
Layered, because adaptive attacks break any single defense:

1. **Spotlighting** (datamarking/delimiting/encoding) — all page-derived text is marked *untrusted* before it reaches any model (cuts IPI >50% → <2% in Microsoft's study).
2. **Instruction-hierarchy fine-tuning** — page text cannot override the user goal.
3. **CaMeL-inspired privileged/quarantined split** — the on-device action model is the **quarantined executor** over untrusted DOM; the (optional) cloud planner is the **privileged orchestrator** that never sees raw untrusted content with tools.
4. **DOM Sanitizer** — down-weights hidden/off-task/freshly-injected elements; treats unexpected new UI as a deferral trigger (defends the pop-up/adversarial-element attacks).
5. **Risk head + confirmation gates** (WebGuard-style SAFE/CAUTION/UNSAFE + Magentic-UI-style two-stage guard) — irreversible/state-changing actions require the human.
6. **Calibrated deferral as fail-safe** — when defenses are bypassed, low-confidence/high-risk steps still route to the user.
7. **Scope shrink** — transactions out of scope ⇒ minimal blast radius even on a successful injection.

### 6.3 Privacy & local-index threat model
On-device removes server collection but adds local threats:

| Threat | Mitigation |
|---|---|
| **Indirect prompt injection** (page → agent) | §6.2 defense-in-depth |
| **Cross-session stored injection** (yesterday's page fires when recalled today) | Treat retrieved history as untrusted; re-apply spotlighting/sanitizer to retrieved chunks; flag/segregate instruction-like retrieved text |
| **Embedding inversion** (reconstruct text from vectors) | Encrypt the vector store; isolate from content scripts; Matryoshka low-dim index reduces recoverable signal |
| **Index tampering** (bias retrieval) | Integrity checks; encrypted store; extension-origin-scoped IndexedDB |
| **Malicious extension / MV3 limits** | `activeTab` + narrow `host_permissions`; **no remote code** (CSP `script-src 'self' 'wasm-unsafe-eval'`); document that trust comes from on-device processing + auditability, *not* the sandbox alone |
| **Sensitive-page capture** (banking, webmail, health) | Default sensitive blocklist + content-type heuristics + `/login /checkout /payment` path exclusion; opt-in capture |
| **Device compromise** | Same threat model as browser history itself; one-click wipe; encryption at rest |

---

## 7. MV3 constraints & how we live within them

| Constraint | Impact | Mitigation |
|---|---|---|
| **Service worker dies** (~30 s idle / 5 min) | Long agent loops die | An **active CDP session keeps the worker alive**; checkpoint state to `chrome.storage`; resume |
| **Content scripts can't call `chrome.*`** | Actions must be brokered | Content script ↔ service worker messaging; CDP from the worker |
| **No remote code (CSP)** | Can't `eval` remote models | All code/models local; wasm needs `'wasm-unsafe-eval'` |
| **WebGPU in workers is flaky** (ORT-Web issue) | In-worker ML unreliable | Host ML in the **offscreen document**; embeddings there; main models in the native sidecar |
| **Broad `host_permissions` hurt review + trust** | Store friction | Prefer `activeTab` + user gesture; request minimal hosts |
| **In-browser LLM is 5–10× slower** | Can't run 7B in-page | Native Ollama/llama.cpp sidecar; browser only for embeddings/tiny fallback |

**Reference implementation to fork:** **Nanobrowser** already does WXT + MV3 + side panel + CDP + a Planner/Navigator/Validator loop with an Ollama option — the exact skeleton, minus fine-tuned models + memory + calibration. We fork it and replace cloud calls with our local specialists.

---

## 8. Build path (concrete)

1. **Fork Nanobrowser** → get side panel + CDP observe/act + multi-agent loop running unchanged.
2. **Add the memory subsystem** (port Second Brain's PGlite/pgvector + embeddings into the offscreen doc).
3. **Wire a base model** via Ollama; get grounded-QA-with-citations + refusal working *before any training* (baseline).
4. **Train the QA adapter** (SFT→DPO), swap it in, measure the lift.
5. **Add risk head + confirmation gates + action log + DOM sanitizer** (safety UX).
6. **Train the action adapter** (distill→SFT+negatives→DPO + deferral head); put it in the loop.
7. **Add the escalation router + offline mode**; benchmark the efficiency Pareto.
8. **Harden** (spotlighting, CaMeL split, encryption), polish, beta.

---

## 9. Open technical questions (track these)

- **One multi-task model vs two adapters vs two models** — default: shared base + two adapters; validate footprint/latency empirically ([00 §10 #1](00_MASTER_Vision_and_Knowledge.md)).
- **Sidecar delivery** — bundle an Ollama setup step vs native-messaging host vs a packaged llama.cpp binary. Affects install friction; decide by M4.
- **Vision fallback** — whether/when to ship a small VLM (Qwen2-VL-2B) for canvas/shadow-DOM pages. Default: future scope.
- **Functional-token vs JSON actions** — measure before committing (ablation).
- **Exact consumer GPU** for the efficiency numbers — needed from you to finalize model-size ceiling.

---

*Next: [03_RESEARCH_PAPER_PLAN](03_RESEARCH_PAPER_PLAN.md) for how this architecture becomes a paper, or back to [01_PRODUCT_PLAN](01_PRODUCT_PLAN.md).*
