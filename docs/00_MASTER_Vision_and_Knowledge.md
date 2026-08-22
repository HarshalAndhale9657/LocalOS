# 00 — Master Vision & Knowledge Base

> **Product:** Groundwork (chosen name — see [§9 Naming](#9-naming-decision)). Repo dir: `d:\LocalOS`.
> **Type:** Final-year graduation / major project + IEEE-level research paper.
> **One line:** A privacy-first, *local-first* **agentic browser assistant** (Chrome MV3 extension) that can **see and control** your browser to do private research, on-demand data extraction, and grounded recall over your own browsing — powered by **fine-tuned small local models** that know **when they don't know**.
> **Status:** Planning. This document is the single source of truth for *what* we are building and *why*. Product execution lives in [01_PRODUCT_PLAN](01_PRODUCT_PLAN.md); the paper lives in [03_RESEARCH_PAPER_PLAN](03_RESEARCH_PAPER_PLAN.md).
> **Date:** 2026-08-21.

---

## 0. How to read these docs

| Doc | Audience | Purpose |
|---|---|---|
| **00 — Master Vision & Knowledge** (this) | You + committee | The "why", the landscape, positioning, the unified thesis, glossary, decisions |
| [01 — Product Plan](01_PRODUCT_PLAN.md) | Builder / user / committee | Personas, features, UX, roadmap, metrics, go-to-market |
| [02 — Technical Architecture](02_TECHNICAL_ARCHITECTURE.md) | Builder | MV3 sense+act layer, RAG memory, local model serving, safety architecture |
| [03 — Research Paper Plan](03_RESEARCH_PAPER_PLAN.md) | ML/NLP + IEEE reviewers | RQs, contributions, method, datasets, experiments, venues, paper outline |
| [04 — Related Work](04_RELATED_WORK.md) | You (writing the paper) | Annotated bibliography by theme + the gap we fill |

The **product's differentiation claims** (01) and the **paper's baselines** (03/04) intentionally share one bibliography so they never drift apart.

---

## 1. What you asked for (requirements, restated)

You want to build **one thing that serves two goals at once**:

1. **A real, useful product** — a browser extension that can *control and see all over the browser*, with strong **agentic** properties, that people will actually adopt.
2. **An IEEE-level-and-above research paper** that materially strengthens your **ML / NLP / LLM researcher** career.

Hard requirements you set:

- **Agentic browser control** — the extension must *act* (not just read/summarize).
- **Local RAG** — retrieval-augmented memory over your browsing, on-device.
- **Fine-tuning a local language model** for specific tasks in the project.
- **Privacy / local-first** posture (implied by "local RAG" + "local model" + the reference docs).
- **Rigor** — this is your graduation project *and* best paper; treat it carefully.

Decisions you locked in (via the scoping questions):

| # | Decision | Choice |
|---|---|---|
| A | **Architecture** | **Hybrid, local-first**: fine-tuned small local models do high-frequency/specialized work on-device; an *optional* cloud LLM handles hard multi-step planning; degrades gracefully offline. |
| B | **Research core (fine-tuning)** | **Two tracks:** (1) **Web action grounding** + (2) **Grounded memory QA + calibrated refusal**. |
| C | **Flagship product use** | **Research & knowledge work** + **personal memory/recall** + **on-demand structured data extraction**. (Transactional automation = future scope.) |
| D | **Compute** | **Single consumer GPU / Colab** → QLoRA on 3B–8B, 4-bit GGUF inference. |

**Assumptions I'm running with (confirm or correct — see [§10](#10-decisions-to-confirm)):** ~6-month solo timeline; a small cloud budget for teacher-distillation data is acceptable; you're willing to release an artifact/benchmark.

---

## 2. The reference docs (what they are, and how we differ)

The two files in the repo root (`secondbrain.md`, `Second_Brain_Project_Documentation_Professional.pdf`) describe **"Second Brain"** — *inspiration only, not our project*:

- A **passive** local RAG-over-browsing-history Chrome extension. It indexes pages you read (Readability.js → chunk → embed with `Xenova/all-MiniLM-L6-v2` → PGlite+pgvector in-browser), then answers questions grounded in what you read, with a small model fine-tuned via **SFT + DPO** for grounded answering + calibrated refusal. Stack: WXT, Transformers.js, PGlite/pgvector, Groq/Gemini/Ollama, SimHash dedup, hybrid retrieval (vector + time-decay + MMR).

**Groundwork is a strict superset in ambition.** Second Brain is *memory*. Groundwork is *memory + agency*:

| | Second Brain (inspiration) | **Groundwork (our project)** |
|---|---|---|
| Core behavior | Passive capture, answer questions | **Active: sees + controls the browser to do tasks**, plus memory |
| Fine-tuning | 1 track (grounded QA + refusal) | **2 tracks (action grounding + grounded QA/refusal), unified** |
| Model role | Answering | **Acting *and* answering, both calibrated to abstain/defer** |
| Research claim | Reduced hallucination on a personal corpus | **A unified *calibrated-grounding* framework + on-device efficiency Pareto + a released benchmark** |
| Rigor | Hobby-grade eval (30 Qs) | **Multi-run variance, ablations, risk-coverage curves, artifact release** |

We keep everything good about Second Brain's *retrieval* subsystem and go far beyond it.

---

## 3. The market reality (why now, why this)

Findings from the deep research pass (2023–2026), condensed:

**The category exploded, then started consolidating — and already killed its weakest bets.**
- **Standalone AI browsers are dying.** OpenAI **discontinued Atlas** (Aug 9 2026) and folded agent capability back into ChatGPT + a Chrome extension. Google **shut Project Mariner** (May 2026) into Gemini/Chrome. Arc was **frozen** (May 2025) for Dia (parent acquired by Atlassian, $610M). Lesson: **building a whole browser is a losing "novelty tax" bet; an extension that augments the browser people already use is the durable surface.** ([OpenAI/Atlas](https://www.adgully.com/post/17951/openai-discontinues-atlas-browser-shifting-agent-capabilities-directly-into-chatgpt), [Mariner](https://www.androidheadlines.com/2026/05/google-shuts-down-project-mariner-ai-agent.html))
- **The agentic incumbents are cloud + paywalled + geo-locked.** Perplexity **Comet** (real autonomy on $200/mo Max), **Claude for Chrome** (Pro $20/mo, MV3 extension + sidecar), **Chrome Auto-Browse** (AI Pro/Ultra, US-only), **Copilot Mode** (Edge, enterprise). All route page content + actions through the cloud with the LLM holding the user's full authenticated privileges.

**Prompt injection is the whole category's unsolved wound.**
- Brave demonstrated **Comet exfiltrating a user's email + OTP** from hidden text in a Reddit comment; a follow-up did it via a screenshot. Traditional web protections (SOP/CORS) are useless against agents. Atlas was rated "least secure"; OpenAI publicly conceded prompt injection **may never be fully solved**. Claude for Chrome cut its injection success rate from 23.6% → **11.2%** — *cut, not eliminated*. ([Brave](https://brave.com/blog/comet-prompt-injection/))
- **Legal tailwind:** a court found Comet likely violated the **CFAA** by accessing a logged-in Amazon account "with permission of the user but without authorization by Amazon." Acting on third-party authenticated sessions is now a live liability.

**The local-first primitives now exist but nobody has assembled the whole.**
- Private-but-read-only: **Brave Leo** (BYOM via Ollama, no-log, TEE) — but agentic control is Nightly-only.
- Agentic-but-cloud: **Comet / Claude / Copilot**.
- Dev frameworks, not products: **browser-use** (100k+ stars, DOM/accessibility-tree-driven; validates our observation format) and **Nanobrowser** (MV3 extension, multi-agent Navigator/Planner/Validator — but **BYO cloud API key**, no fine-tuned models, no memory).

**The small-model bet is validated by research** (see [04](04_RELATED_WORK.md)): WebLINX (small fine-tuned models beat zero-shot GPT-4V), WebRL (8B → 2.4× GPT-4-Turbo on WebArena-Lite), Agent-Q (DPO on mined failures), UI-TARS (7B, SFT+DPO), Trust-Align (SFT+DPO grounded refusal). QLoRA on 3B–8B fits a single 16–24 GB GPU.

### The white space Groundwork owns

> **No shipping product combines all four pillars at once:** (1) **Chrome MV3 extension** form factor, (2) **fine-tuned *small local* models** (not BYO cloud keys), (3) **local-first RAG memory** over the user's own history, and (4) **agentic browser control** — with **calibrated grounding** (citations + principled abstention/deferral) as the trust guarantee. Incumbents own any *three* at most; Groundwork owns the intersection.

---

## 4. Product positioning (the one paragraph)

> **Groundwork is a privacy-first, local-first agentic browser assistant shipped as a Chrome MV3 extension that can see and control the browser to do three jobs the incumbents only do in the cloud: (a) cross-tab research & knowledge synthesis with inline citations, (b) on-demand structured data extraction from pages, and (c) grounded recall over the user's own browsing history.** Small QLoRA-fine-tuned models (3B–8B, 4-bit GGUF via llama.cpp/Ollama) run high-frequency, specialized tasks fully on-device; an *optional* cloud LLM handles only hard multi-step planning; the system degrades gracefully to fully offline. It is for privacy- and cost-sensitive knowledge workers, students, researchers, and regulated users under-served by cloud-only, subscription-gated, geo-locked agents. It deliberately defers transactional automation (checkout/booking), which **shrinks the prompt-injection blast radius** and sidesteps the CFAA/authorization liability. Its trust guarantee is **calibrated grounding**: it acts only on what is actually on the page, answers only from what you actually read, cites its sources, and **abstains or asks** when it is uncertain.

---

## 5. The unified research thesis — *Calibrated Grounding for On-Device Browser Agents*

This is the intellectual spine that turns "a nice product" into "a defensible paper."

> **Thesis.** A single family of small local models, refined by **SFT → preference optimization (DPO and cheaper reference-free variants) on the agent's own mined failures**, can learn not just to *act* and *answer* but to **know when it does not know** — abstaining from unsupported answers ("not found in your history") and deferring uncertain or high-risk browser actions to the user — under **one shared selective-prediction / conformal calibration framework**. A unified abstention objective spanning **(1) web action grounding over a compressed DOM/accessibility tree** and **(2) grounded memory-QA over a personal browsing-history RAG index** yields a small, private, offline-capable agent whose reliability under uncertainty and adversarial page content rivals far larger cloud agents on a targeted research/extraction/recall task distribution — at a fraction of the tokens, latency, and energy — and where **calibrated abstention doubles as a defense-in-depth fail-safe against indirect prompt injection.**

**Why it's one idea, not two bolted together:** both tracks are the *same* statistical problem — *selective prediction under uncertainty*. "I can't reliably find that button, so I'll ask" (action deferral) and "your history doesn't support an answer, so I'll abstain" (QA refusal) share one conformal calibration method and one mined-failure preference-optimization pipeline. **No cited work unifies grounded-QA refusal (Trust-Align, RefusalBench) with action-abstention (KnowNo, WebGuard, UQ-for-CUA).**

### The novelty claims (each phrased as a paper contribution)

1. **Unified calibrated-grounding framework** — first to treat memory-QA abstention and web-action deferral as one selective-prediction problem sharing a conformal method and a single mined-failure preference pipeline.
2. **Calibrated safe-action deferral on a *small on-device* web-action model** — KnowNo is for robots; WebGuard uses frontier guardrails; 2026 UQ-for-computer-use only benchmarks miscalibration. Combining conformal *when-to-ask* + a SAFE/CAUTION/UNSAFE risk head + DPO-on-failures inside a single 3B–8B GGUF model over a DOM/AX-tree is unaddressed.
3. **Retrieval-augmented action grounding** — use the user's *own* browsing history as per-site priors/exemplars to attack the **unseen-site generalization gap** WebLINX explicitly reports. No cited paper couples a personal-history RAG with a small on-device action model.
4. **A privacy-preserving self-improvement flywheel** — mine *real personal* failure cases (user-flagged wrong recalls, failed actions) from a deployed extension and build DPO/KTO pairs **fully on-device**, never sending trajectories to the cloud. WebRL/Agent-Q/UI-TARS can't do this (they run in labs).
5. **Calibrated grounding as an injection fail-safe** — abstention/deferral as defense-in-depth that holds when instruction-hierarchy/spotlighting defenses are bypassed, plus handling **cross-session stored injection** carried through the personal RAG index (a page visited yesterday firing when recalled today) — a threat no surveyed system defends against.
6. **A released benchmark** — the first grounded-QA + must-abstain benchmark over a user's own browsing history (working title **"Personal-Memory-RGB"**), with answerable vs "not-in-your-history" / stale / false-premise splits, jointly reporting Trust-Score-style refusal F1, ALCE citation precision/recall, and RAGAS faithfulness — plus a browser-adapted **action-safety split** reporting Completion-under-Policy under adaptive attack.
7. **A systems/efficiency result** — end-to-end measured **accuracy-vs-cost/latency/energy Pareto** for running two fine-tuned small GGUF models (action + grounded-QA) concurrently on one consumer GPU alongside a Chrome MV3 extension, including a calibrated **local-then-cloud escalation router**.

> **Scoping note (honesty):** claims 1–3 + 6 form the **guaranteed core**; 4, 5, 7 are **stretch**. Even if a track thins out under time pressure, the *unified framing* still carries the paper. We never claim to *solve* prompt injection — only to add a measurable fail-safe.

---

## 6. Competitive differentiation (the short table)

Full detail in [01 §7](01_PRODUCT_PLAN.md). The essence:

| Competitor | What it is | **How Groundwork differs** |
|---|---|---|
| **Perplexity Comet** | Free, cloud agentic browser | Cloud routing + full account privileges (proven email/OTP exfiltration, CFAA ruling). Groundwork keeps content/actions/index **on-device**, treats pages as untrusted, gates sensitive actions, leads with research/recall not transactions → smaller blast radius. |
| **Claude for Chrome** | Cloud MV3 extension + sidecar, $20/mo | Closest form factor, but cloud-only + admitted **11.2% residual injection**. Groundwork is local-first, free/no-account/offline, safety-as-architecture (quarantined on-device executor + deferral fail-safe). |
| **Chrome Auto-Browse / Gemini** | Cloud, paywalled, US-only | Groundwork: offline mode, no account, no geo-lock — serves the segment Google ignores. |
| **Copilot Mode (Edge)** | Cloud, enterprise, auditable | Groundwork matches auditability (action log, confirmation gates, risk labels) **with data never leaving the device**. |
| **browser-use** | Open dev framework (Python/TS), BYO cloud LLM | Validates our DOM/AX-tree + element-index design; but it's a library, not a consumer product. Groundwork owns the on-device, non-technical-user, extension niche with fine-tuned specialists. |
| **Nanobrowser** | Open MV3 multi-agent extension, BYO cloud key | We **fork its proven skeleton** (WXT, side panel, CDP) but swap cloud calls for fine-tuned local models + add RAG memory + calibrated refusal. |
| **Brave Leo** | Private, BYOM/Ollama, mostly read-only | Groundwork marries the privacy plumbing to **true agentic control + task-specialized fine-tuned models**. |
| **Fellou** | Cloud "agentic browser", acts from logged-in sessions | Same research job-to-be-done, but Groundwork does it **without acting on third-party authenticated sessions** (no CFAA exposure). |
| **Sider / Monica / Merlin / HARPA** | Cheap cloud sidebar assistants | Commoditized "summarize + chat." Groundwork competes on **agentic control + private long-term memory with calibrated grounding**, not summarization. |

---

## 7. Recommended technology stack (summary — full detail in [02](02_TECHNICAL_ARCHITECTURE.md))

- **Extension shell:** fork **Nanobrowser's** skeleton — WXT, Chrome MV3, **side-panel UX**, `chrome.debugger` (**CDP**) as the observe-and-act path (DOMSnapshot + Accessibility + `Input.dispatch*Event`; an active CDP session keeps the service worker alive past the 30 s/5 min kill). Permissions: `activeTab` + **narrow** `host_permissions`, `tabs`, `scripting`, `sidePanel`, `storage`, `debugger`.
- **Observation:** compressed **accessibility/semantic tree** (~5–10% of raw DOM nodes; ~12.6k vs 43k+ tokens), most-recent-snapshot only. **Action space = element-INDEX + verb** (click/type/scroll/select/navigate) with a snapshot **version-id** the executor verifies before acting. Text-first, vision-optional.
- **Local inference:** fine-tuned models as **GGUF Q4_K_M** via **Ollama/llama.cpp** over localhost/native messaging (7B ≈ 5 GB, 3B ≈ 2 GB). **Do not** put the main agent model in WebLLM (browser inference is 5–10× slower).
- **In-browser (offscreen ML host):** **transformers.js/ONNX for embeddings only** — `bge-small-en-v1.5` or `nomic-embed-v1.5` with **Matryoshka** truncation (128–256 dims) to shrink the IndexedDB index.
- **Local RAG memory:** **PGlite + pgvector** (HNSW, sub-20 ms, >95% recall); hybrid dense + BM25 with **RRF**, then a cross-encoder reranker (`bge-reranker-v2-m3`); **time-decay + MMR**; recursive 400–512-token chunks, no overlap; SimHash dedup; Readability.js extraction; **encrypted, content-script-isolated** store.
- **Base models:** **Qwen2.5-7B-Instruct** (primary) or **Qwen3-4B-Instruct-2507**; **Llama-3.2-3B / SmolLM3-3B** for the offline/low-VRAM tier; **Phi-4-mini** as a function-calling-focused alternative.
- **Training:** **QLoRA** (4-bit NF4, r=16 α=32) via **Unsloth** on one 16–24 GB GPU (~7 GB peak for 8B). Pipeline: teacher-distilled + execute-verified **SFT** (with explicit **negative samples**, Agent-FLAN-style) → **DPO**, then ablate **ORPO / SimPO / KTO**.
- **Data:** **AgentTrek**-style tutorial-replay trajectory synthesis (~$0.55/trajectory); **APIGen**-style execute-and-verify quality gate; **Trust-Align**-style pos/neg pairs with NLI-verified citations; seed refusal data from SQuAD 2.0 unanswerable + RealTimeQA (stale).
- **Safety:** **CaMeL**-inspired privileged/quarantined split; **spotlighting** + instruction-hierarchy fine-tuning; **Magentic-UI**-style two-stage action-guard; DOM sanitizer that down-weights hidden/off-task/freshly-injected elements.
- **Calibration/eval:** **conformal prediction** (KnowNo-style) for coverage guarantees; single-pass **Semantic Entropy Probes** as an in-browser refusal gate; ECE for thresholds; a **local WebJudge-style** auto-evaluator validated against human agreement.

---

## 8. Glossary (so the docs read consistently)

| Term | Meaning |
|---|---|
| **Calibrated grounding** | Our unifying thesis: acting only on what's on the page, answering only from what's been read, and **abstaining/deferring** under uncertainty — with citations. |
| **Action grounding** | Mapping a goal + page observation → the correct next UI action *and the specific element* it targets. |
| **Grounded memory QA** | Answering strictly from retrieved browsing-history chunks, with inline citations, or refusing. |
| **Calibrated refusal / abstention** | Saying "not found in your history" (or deferring an action) *at the right times* — measured by refusal precision/recall, risk-coverage, AUROC — not refusing constantly. |
| **Deferral** | The action-side of abstention: the agent asks the user instead of acting when uncertain/risky. |
| **SFT** | Supervised fine-tuning on (input → target) pairs. |
| **DPO / ORPO / SimPO / KTO** | Preference-optimization methods; DPO = reference-model pairwise; ORPO = single-stage no-reference; SimPO = reference-free; KTO = unpaired binary labels. |
| **QLoRA** | 4-bit-quantized LoRA fine-tuning; fits large-ish models on small GPUs. |
| **GGUF Q4_K_M** | The on-device 4-bit weight format served by llama.cpp/Ollama. |
| **CDP** | Chrome DevTools Protocol (via `chrome.debugger`) — our trusted observe+act channel. |
| **a11y tree** | Accessibility tree; a compact semantic subset of the DOM used as the model's observation. |
| **RRF / MMR** | Reciprocal Rank Fusion (hybrid retrieval merge) / Maximal Marginal Relevance (diversity re-ranking). |
| **IPI** | Indirect Prompt Injection — malicious instructions hidden in page content. |
| **CuP** | Completion-under-Policy — a web-agent *safety* success metric (from ST-WebAgentBench). |
| **Personal-Memory-RGB** | Our proposed released benchmark for grounded QA + must-abstain over browsing history. |
| **Conformal prediction** | A calibration method giving a formal coverage guarantee on when to abstain/defer. |

---

## 9. Naming decision — ✅ resolved

**Product name: Groundwork.** It signals the *calibrated-grounding* core (grounded answers + grounded actions) and "does the groundwork" of research; it's plain, memorable, and product-friendly. The repo directory remains `d:\LocalOS` for historical reasons (no need to move it).

Alternatives that were considered (kept here for the record): **Marginalia** (notes in the margins of what you read), **Understory** (the private layer beneath the browsing canopy), **Lodestone** (grounded navigation without a cloud compass), **Palimpsest / Tabula / Kestrel / Keep**. Before publishing to the Chrome Web Store, do a quick trademark check on "Groundwork" in the software category.

---

## 10. Decisions — status

Confirmed with the user on 2026-08-21: **name = Groundwork**, **timeline ≈ 6 months**, **training compute = Colab Pro / paid cloud (A100/L4 — 7B–8B QLoRA comfortable)**, **build + benchmark start now**.

| # | Decision | Status / value | Notes |
|---|---|---|---|
| 1 | **Model count** | **Default: one shared base, two LoRA adapters** (action + QA), router-hot-swapped; multi-task single model as an ablation | Halves footprint & training effort; keeps the "two tracks" story |
| 2 | **Priority track if time runs short** | **QA-refusal first** (Trust-Align recipe, lower risk) → then action-grounding+deferral (headline novelty) | Guarantees a deliverable; unified framing works either way |
| 3 | **Cloud planner policy** | **Optional BYO-key cloud planner** *(page content + history never leave device)* **+** first-class **offline mode** | Enables the local-vs-cloud ablation |
| 4 | **Benchmark release** | ✅ **Yes — Personal-Memory-RGB** (spec in [05](05_BENCHMARK_Personal_Memory_RGB.md)) | Highest-leverage move for a top-tier D&B submission |
| 5 | **Naming** | ✅ **Groundwork** (repo dir stays `d:\LocalOS`) | See §9 |
| 6 | **Timeline** | ✅ **~6 months, solo** (M1–M6 roadmap in [01](01_PRODUCT_PLAN.md)) | Anchor M1 to your actual start date |
| 7 | **Compute** | ✅ **Training: Colab Pro / paid cloud (A100/L4)** — 7B–8B QLoRA comfortable, teacher-distillation calls easy | ⚠️ *Still needed:* the **consumer machine** you'll benchmark **inference/latency/energy** on for the efficiency Pareto (the product is local-first, so the paper's on-device numbers must come from consumer HW, not the A100) |
| 8 | **Data budget** | Small cloud spend assumed OK (teacher distillation + AgentTrek ~$0.55/traj × a few k) | Confirm the ceiling |
| 9 | **Primary archival venue** | **IEEE Access** (rolling) guaranteed deliverable + **NeurIPS/ICLR 2027 D&B** stretch | See [03 §10](03_RESEARCH_PAPER_PLAN.md); near-term 2026 workshop deadlines are out of reach from an Aug-2026 start |

---

## 11. Guiding principles

1. **Local-first is the moat and the message.** Every design choice defaults to on-device; cloud is opt-in and content-blind.
2. **Calibration over confidence.** A well-timed "I don't know / let me ask you" is the product *and* the paper.
3. **Reuse, don't rebuild.** Fork Nanobrowser's shell; use Unsloth/QLoRA; synthesize data with AgentTrek. A 6-month solo project cannot build plumbing from scratch.
4. **Honesty beats hype.** We never claim to solve prompt injection or to beat cloud SOTA on raw success — we claim a better *reliability-under-uncertainty-per-watt* operating point, with variance and ablations.
5. **Ship an artifact.** A released benchmark + code + datasheet is what converts a student project into a citable contribution.

---

*Next: read [01_PRODUCT_PLAN](01_PRODUCT_PLAN.md) for the build, or [03_RESEARCH_PAPER_PLAN](03_RESEARCH_PAPER_PLAN.md) for the paper.*
