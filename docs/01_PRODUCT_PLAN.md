# 01 — Product Plan

> Companion to [00_MASTER](00_MASTER_Vision_and_Knowledge.md). Technical depth lives in [02_TECHNICAL_ARCHITECTURE](02_TECHNICAL_ARCHITECTURE.md); the research side in [03_RESEARCH_PAPER_PLAN](03_RESEARCH_PAPER_PLAN.md).
> **Product:** Groundwork. **Form factor:** Chrome MV3 extension + side panel. **Posture:** privacy-first, local-first, hybrid.

---

## 1. Product summary

Groundwork is an **agentic browser assistant** that lives in the Chrome side panel and can **see and control** the browser to do private research, pull structured data from pages on demand, and recall anything you've read — powered by **fine-tuned small local models** that cite their sources and **abstain or ask when unsure**. Page content, the memory index, and the primary models stay **on your device**. Cloud is optional, opt-in, and never sees your page content.

**The wedge:** every agentic competitor is cloud-based and holds your full account privileges — and every one of them has been shown to leak data via hidden page instructions (indirect prompt injection). Groundwork is the private, calibrated, research-focused alternative that treats every page as untrusted and keeps the blast radius small by *not* doing transactions.

---

## 2. Target users & personas

| Persona | Who | Pain today | Groundwork value |
|---|---|---|---|
| **The Researcher** (primary) | Grad students, analysts, academics | Reads 30+ tabs; loses what they read; cloud tools expose sensitive lit/IP | Private cross-tab synthesis with citations; grounded recall; nothing leaves the device |
| **The Privacy-Conscious Pro** | Lawyers, healthcare, finance, journalists | Cannot paste client/patient/source data into cloud AI; compliance risk | On-device processing; auditable actions; no account, no egress |
| **The Cost-Sensitive Student** | Undergrads, self-learners, users in geo-locked regions | Comet autonomy is $200/mo; Auto-Browse is US-only + paywalled | Free, offline-capable, no geo-lock |
| **The Data Wrangler** | Ops, sales, e-comm researchers | Manually copies tables/listings/prices across pages | "Extract this as a table/CSV" on demand, locally |

**Not our user (v1):** people who want the agent to *buy/book/submit* things for them across authenticated third-party sites. That's future scope (higher risk + CFAA exposure).

---

## 3. Jobs-to-be-done (the flagship trio)

### JTBD-1 — Cross-tab research & synthesis *(hero)*
> "I have a question and 12 open tabs. Read across them, extract the relevant bits, and give me a cited answer — privately."

- Agent reads the relevant open tabs (or navigates to gather more, with consent), extracts on-topic content, and synthesizes an answer **with inline citations back to the exact page + the date read**.
- **Calibrated:** if the tabs/history don't support an answer, it says **"not found in your history / open tabs"** instead of guessing.

### JTBD-2 — On-demand structured data extraction
> "Pull every product's name, price, and rating on this page into a table."

- Point Groundwork at a page (or a set of pages); it returns clean structured output (table / JSON / CSV) you can copy or export.
- **Calibrated:** flags low-confidence fields rather than fabricating values.

### JTBD-3 — Personal memory & recall
> "What was that article about QLoRA I read last week? What did it say about VRAM?"

- Passive local capture (opt-in, allow/block-listed) → local RAG index → ask-anything grounded recall with citations and **time-scoped** queries ("last week").
- **Calibrated:** refuses on topics never read; handles **staleness** ("that changed since you read it") when timestamps warrant.

### Future scope (explicitly deferred)
Transactional automation (checkout/booking/form-submission across authenticated sites), multimodal capture (images/PDFs/diagrams), cross-device encrypted sync, podcasts via local ASR, a personal knowledge graph. Listed so the committee sees the roadmap; **not built in v1.**

---

## 4. Feature spec (MoSCoW)

### Must have (v1)
- **Side-panel chat UI** with streaming answers and clickable citations.
- **See:** capture the active tab's readable content + compressed accessibility tree via content script + CDP.
- **Act (read-oriented):** navigate, open/switch tabs, scroll, click links, expand sections, paginate — the actions needed for *research & extraction* (not form submission).
- **Local RAG memory:** passive capture (opt-in) → clean → dedup → chunk → embed → PGlite/pgvector; hybrid retrieval + rerank + time-decay + MMR.
- **Two calibrated local models:** action-grounding + grounded-QA/refusal (shared base, LoRA adapters), served via local Ollama/llama.cpp.
- **Calibrated behaviors:** "not found in your history" refusal; **confirmation gates** for any state-changing action; **SAFE/CAUTION/UNSAFE** risk labels on proposed actions.
- **Action log / audit trail:** every action the agent takes is visible and reversible-by-review.
- **Privacy controls (one-click):** pause capture, exclude a site, delete an entry, wipe the index; default sensitive-domain blocklist (banking, webmail, health, messaging, password managers).
- **Offline mode:** fully functional with local models only (degraded planning quality).
- **Settings:** choose local model tier (3B/7B); optional BYO cloud key for the planner (off by default).

### Should have
- **Extract-to-table/CSV/JSON** export.
- **Local-then-cloud escalation router** (auto-escalate hard steps if a cloud key is configured; show when/why).
- **Failure-flagging:** thumbs-down on a wrong recall/action → stored locally as a training-signal candidate (the flywheel).
- **Multi-tab "research session"** object you can name, revisit, and export.
- **Injection defense surfacing:** when the DOM sanitizer flags suspicious hidden instructions, tell the user.

### Could have
- Vision fallback grounder (small VLM) for canvas/shadow-DOM/image-heavy pages.
- Per-site "learned workflow" memory (reusable extraction recipes).
- Keyboard-first command palette.

### Won't have (v1)
- Autonomous checkout/booking/form-submission on authenticated third-party sites.
- Full-browser build (extension only).
- Cloud sync of page content or index.

---

## 5. Key UX flows (described)

**Onboarding**
1. Install → side panel opens → 3-screen explainer (what's local, what's optional-cloud, what's never captured).
2. Pick model tier (auto-detect VRAM → recommend 3B or 7B); optional local model download via Ollama with a guided step.
3. Choose capture mode: *Off* / *Ask each site* / *On with blocklist* (default). Show the default sensitive blocklist.

**Ask (research/recall)**
1. User types a question in the side panel.
2. Agent shows a short plan ("I'll read tabs 2, 5, 7 and your history on X").
3. Streams a cited answer; each citation chip → opens the source page at the read date.
4. If unsupported: **"I couldn't find this in your open tabs or history."** (with an offer to search the web if a cloud/search path is enabled).

**Act (guarded)**
1. Agent proposes an action with a **risk label**. `SAFE` (navigate/scroll/read) executes; `CAUTION`/`UNSAFE` (anything state-changing) shows a **confirmation card** with the exact target element highlighted.
2. Every executed action appends to the visible **action log**.
3. If the model's confidence in the target element is low → **"I'm not sure which element — can you point?"** (deferral), rather than clicking blindly.

**Extract**
1. "Extract [fields] from this page." → agent returns a table preview → user confirms → export.
2. Low-confidence cells are marked, not silently filled.

**Privacy panel**
- Pause capture (global toggle), site exclusions, per-entry delete, "wipe everything," blocklist editor, and a plain-language data-inventory ("what's stored, where, and that it never leaves").

---

## 6. System architecture (product view)

Full detail in [02](02_TECHNICAL_ARCHITECTURE.md). At a glance:

```
┌───────────────────────── Chrome (user's device) ─────────────────────────┐
│  Content Script(s)        Service Worker (MV3)         Offscreen Doc      │
│  ├ Readability extract     ├ Message router             ├ transformers.js │
│  ├ a11y/DOM snapshot   →   ├ Blocklist/consent gate     │   embeddings    │
│  └ trusted-event actions   ├ RAG pipeline (retrieve/    ├ PGlite+pgvector │
│         ▲ (via CDP)        │   rerank/decay/MMR)        │   (IndexedDB)    │
│         │                  ├ Safety: DOM sanitizer,     └ (encrypted)     │
│  Side Panel (React)   ←→   │   spotlighting, risk head                    │
│  ├ chat + citations        ├ Calibration: conformal/SEP gate              │
│  ├ action log + gates      └ Escalation router ──────────────┐           │
│  └ privacy controls                                          │            │
│                                                              ▼            │
│  Local model sidecar (Ollama / llama.cpp, GGUF Q4_K_M)                    │
│  ├ action-grounding adapter    └ grounded-QA/refusal adapter              │
└──────────────────────────────────────────────────────────────┬──────────┘
                                                                 │ (opt-in, content-blind)
                                                          Optional Cloud LLM (BYO key)
                                                          — hard multi-step planning only
```

**Data-flow guarantee:** page content, embeddings, and the index never leave the device. The optional cloud planner receives *only* an abstracted task/plan representation the user has approved — never raw page text or history (see [02 §safety](02_TECHNICAL_ARCHITECTURE.md)).

---

## 7. Competitive differentiation (product-facing)

| Competitor | Local? | Agentic? | Fine-tuned local models? | Memory/RAG? | Calibrated refusal/citations? | Transactions? |
|---|---|---|---|---|---|---|
| Comet | ❌ | ✅ | ❌ | partial | ❌ | ✅ (risky) |
| Claude for Chrome | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Chrome Auto-Browse | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Copilot Mode | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| browser-use | can be | ✅ | ❌ (BYO) | ❌ | ❌ | ✅ |
| Nanobrowser | ❌ (BYO cloud) | ✅ | ❌ | ❌ | ❌ | ✅ |
| Brave Leo | ✅ | ⚠️ Nightly | ❌ (BYOM) | ❌ | ❌ | ❌ |
| Second Brain (ref) | ✅ | ❌ | ✅ (1 track) | ✅ | ✅ | ❌ |
| **Groundwork** | **✅** | **✅** | **✅ (2 tracks)** | **✅** | **✅** | **deferred (by design)** |

**Groundwork is the only row that is all-local, agentic, fine-tuned, memory-grounded, and calibrated at once.**

---

## 8. Roadmap (generic 6-month plan — anchor to your real dates)

> Sequenced **QA-refusal-track first** (de-risked; Trust-Align recipe) then **action-grounding track** (headline novelty). Reuses Nanobrowser's shell so month 1 isn't spent on plumbing.

| Month | Product milestone | Research milestone | De-risking |
|---|---|---|---|
| **M1** | Fork Nanobrowser shell; side panel + CDP observe/act working; passive capture + PGlite RAG memory (reuse Second Brain patterns); baseline eval harness | Literature review finalized ([04](04_RELATED_WORK.md)); reproduce a base-model grounded-QA baseline; **draft Personal-Memory-RGB** schema | Prove the shell + memory before any training |
| **M2** | Grounded-QA chat with citations + refusal (using base model) live in the panel | Build QA SFT data (Trust-Align-style pos/neg + NLI citations; seed from SQuAD 2.0 / RealTimeQA); **SFT the QA adapter** | QA track is the guaranteed deliverable |
| **M3** | Confirmation gates, action log, risk labels; extract-to-table | **DPO** on mined QA failures; risk-coverage/AUROC eval; conformal refusal gate | Lock the calibrated-refusal result |
| **M4** | Action grounding in the loop (navigate/click/scroll/paginate); escalation router | Build action SFT data (AgentTrek tutorial-replay + execute-verify); **SFT + DPO** the action adapter; deferral head | Headline novelty comes online |
| **M5** | Offline mode polish; injection defenses (spotlighting, sanitizer, CaMeL split); privacy panel; perf tuning | Safety eval (AgentDojo/WASP + ST-WebAgentBench-style CuP under adaptive attack); on-device **efficiency Pareto** (latency/energy/tokens) | Safety + systems contributions |
| **M6** | Beta build, demo video, Chrome Web Store listing (or unpacked release), docs | Preference-optimizer bake-off (DPO/ORPO/SimPO/KTO); finalize benchmark + datasheet; **write the paper**; buffer | Reproducibility + write-up |

**Critical-path risks & buffers** are in [§10](#10-risks--mitigations).

---

## 9. Success metrics

**Product (adoption/quality)**
- Time-to-first-value < 5 min from install.
- Grounded-answer usefulness (thumbs-up rate) and citation-click-through.
- % of answers correctly refused when unsupported (user-perceived trust).
- Median action-plan latency; % of sessions completed fully offline.
- Retention: weekly-active researchers; # of research sessions saved/revisited.

**Research (see [03](03_RESEARCH_PAPER_PLAN.md) for full metric stack)**
- QA: RAGAS faithfulness, ALCE citation precision/recall, **refusal precision/recall + risk-coverage AUROC**.
- Action: Element Accuracy, Step-SR, Action-F1, live Task-SR (local WebJudge), **deferral coverage guarantee**.
- Efficiency: TTFT, tokens/task, tok/s, peak memory, tok/J — the **accuracy-vs-cost Pareto**.
- Safety: attack-success reduction + **Completion-under-Policy under adaptive attack**.

---

## 10. Risks & mitigations (product)

| Risk | Mitigation |
|---|---|
| **6-month solo timeline is tight** for 2 tracks + product + paper | Reuse Nanobrowser shell + Unsloth QLoRA + AgentTrek data; QA-track-first as guaranteed deliverable; action-track as stretch |
| **DOM-build latency** (~5–6 s on heavy pages) hurts UX | CDP Accessibility tree + most-recent-snapshot compression + snapshot caching + version-id verification; vision fallback only when a11y fails |
| **Prompt injection** is unsolved | Defense-in-depth (spotlighting + instruction hierarchy + CaMeL quarantine + confirmation gates); **transactions out of scope shrinks blast radius**; never over-claim |
| **Unseen-site generalization** (small models fail on new sites) | Reframe as the research opportunity (history-RAG-augmented grounding); scope promised competence to the user's frequent research sites; failure-mining flywheel |
| **Two models + embeddings + extension exceed consumer memory** | Ship 3B tier; keep one model hot at a time (router-driven loading); Q4_K_M; treat the concurrent-resource benchmark as a publishable finding |
| **MV3 sandbox doesn't protect against a malicious extension** | `activeTab` + narrow host perms; no remote code (CSP); local + encrypted index isolated from content scripts; trust via on-device processing + auditability |
| **Fast-moving competitive/legal landscape** | Extension-first + research/recall-first + defer-transactions are exactly the decisions validated by Atlas/Mariner deaths and the CFAA ruling |
| **Chrome Web Store review** of `debugger`/broad perms | Justify permissions in the listing; prefer `activeTab`; document the on-device data model; consider unpacked/enterprise distribution for the beta |

---

## 11. Go-to-market (lightweight)

- **Positioning line:** *"The private research agent that lives in your browser — sees your tabs, remembers what you read, cites its sources, and never sends your pages to the cloud."*
- **Wedge audiences:** grad-student/research Twitter/Reddit, privacy communities (r/privacy, HN), regulated-industry knowledge workers.
- **Distribution:** Chrome Web Store (primary) + unpacked build for the beta; open-source the extension shell (fork of Nanobrowser's license permitting) to build trust — models + benchmark released alongside the paper.
- **Trust as marketing:** the same *calibrated grounding + local-first* story that makes the paper makes the pitch. Publish the threat model.
- **Moat:** the fine-tuned specialist models + the on-device failure-mining flywheel improve exactly where each user browses — hard for a generic cloud agent to match privately.

---

*Next: [02_TECHNICAL_ARCHITECTURE](02_TECHNICAL_ARCHITECTURE.md) for the build details, or [03_RESEARCH_PAPER_PLAN](03_RESEARCH_PAPER_PLAN.md) for the paper.*
