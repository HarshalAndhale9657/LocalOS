# Groundwork — Mentor Briefing

*A privacy-first, on-device agentic browser assistant, and the research that anchors it.*
Final-year major project + IEEE-level research paper. Prepared 2026-08.

---

## 0. One-paragraph summary

**Groundwork is a Chrome extension that can *see and control* your browser to do private research, pull structured data from pages, and answer questions from your own reading history — powered by *small language models that run on your own machine* and are trained to know when they don't know.** The whole system runs locally (your page content and browsing history never leave your device), which is the opposite of every mainstream "AI browser" today. The research contribution is a single idea we call **calibrated grounding**: the agent *acts only on what is actually on the page*, *answers only from what it has actually read*, and **abstains or asks the user whenever it is unsure** — and we show that a small, fine-tuned, on-device model can do this reliably, rivaling far larger cloud models on a focused set of tasks while being private, cheap, and offline-capable. We also release a new benchmark to measure this.

---

## 1. The product

### 1.1 What it is
A **Manifest V3 Chrome extension** with a side-panel interface. Two modes:
- **Ask** — you ask a question; it answers *from the pages you've captured*, with inline citations, or replies **"Not found in your history."** instead of guessing.
- **Do** — you give it a task on the current page (e.g., "gather the key points from these tabs", "pull the product names and prices into a table"); it observes the page, decides one action at a time, executes safe actions automatically, and **asks your permission** before anything risky.

### 1.2 The problem we're solving
Knowledge workers, students, and researchers read far more than they can remember, and the meaning of what they read is lost in a browser history that only stores URLs and timestamps. Meanwhile, a new wave of "AI browsers" (Perplexity Comet, OpenAI's Atlas, Google's Gemini-in-Chrome, Anthropic's Claude for Chrome) can now *act* on the web — but they all share three serious problems:
1. **Privacy** — they send your page content and actions to the cloud, with the AI holding your full logged-in privileges.
2. **Safety** — they are vulnerable to *indirect prompt injection* (hidden instructions on a web page hijacking the agent). This is a documented, industry-wide, **unsolved** problem — e.g., a security firm showed Comet could be tricked into leaking a user's email and one-time password from hidden text on a page.
3. **Cost & access** — real autonomy is behind expensive subscriptions and often geo-locked.

### 1.3 Who it's for
Privacy- and cost-sensitive knowledge workers: **graduate students, researchers, analysts**, and professionals in regulated fields (law, healthcare, finance, journalism) who *cannot* paste sensitive material into cloud AI.

### 1.4 What makes it different — the "white space"
We surveyed the whole 2023–2026 landscape. Every product is either:
- **private but read-only** (e.g., Brave's assistant — local models, but it can't really *act*), or
- **agentic but cloud-based** (Comet, Claude for Chrome, Copilot), or
- **a developer library, not a consumer product** (browser-use, Nanobrowser).

**No shipping product combines all four of:** (1) a Chrome extension form factor, (2) *fine-tuned small local models* (not just "bring your own cloud key"), (3) *local memory* over your own history, and (4) *agentic control* — with **calibrated grounding** as the trust guarantee. Groundwork occupies exactly that intersection.

Strategic validation: OpenAI **discontinued** its standalone Atlas browser and Google **shut down** its Project Mariner agent, both folding back into extensions/existing browsers — confirming that *an extension that augments the browser you already use* is the durable bet, not a whole new browser.

### 1.5 Scope decision (important, and deliberate)
We **exclude transactional automation** (checkout, booking, actions on your logged-in third-party accounts) from the current scope. This is a deliberate safety and legal decision: it dramatically shrinks the "blast radius" if an injection attack ever succeeds, and it avoids the legal exposure highlighted when a court found a cloud agent likely violated the US Computer Fraud and Abuse Act by acting on a user's logged-in Amazon account. Our flagship is **research + extraction + recall over the user's own content** — genuinely useful, and much safer.

### 1.6 How it works (five subsystems)
The extension has five cooperating parts:

| Subsystem | Role | How |
|---|---|---|
| **Sense** | See the page | Reads a compressed *accessibility tree* of the page via the Chrome DevTools Protocol — a compact, text-first representation (~5–10% the size of the raw page) that a small model can reason over. |
| **Act** | Control the browser | Executes actions (click, type, scroll, navigate) by mapping an element to a real interaction, with a *stale-snapshot guard* (won't act on an outdated view) and *risk gating* (safe actions run; risky ones ask first). |
| **Remember** | Local memory | Captures readable page text → cleans it → de-duplicates → splits into chunks → creates *embeddings* on-device → stores them in an in-browser vector database (PGlite) → retrieves the relevant chunks for a question, with recency weighting and a "nothing relevant → abstain" threshold. |
| **Reason** | The local model | Runs a small language model locally (via Ollama) to (a) answer questions grounded in retrieved chunks with citations, or refuse; and (b) decide the next browser action. Fine-tuned versions plug in behind the same interface. |
| **Guard** | Safety | Treats all page text (and all retrieved history) as *untrusted*: wraps it so it can't act as instructions to the model, gates risky actions behind confirmation, and enforces a sensitive-domain blocklist + one-click memory wipe. |

Everything sensitive — page content, the memory index, and the model — stays **on the device**. (An *optional* cloud model can be enabled for hard planning, but it never sees raw page content.)

---

## 2. The research

This is what elevates the project from "a working tool" to a defensible research contribution.

### 2.1 The core thesis — *calibrated grounding*
General-purpose LLMs are optimized to be confidently helpful, which makes them **hallucinate** when the true answer is unknown, and makes browser agents **act wrongly** (clicking the wrong thing, or being manipulated by the page). For a *personal memory* and a *browser controller*, a confident wrong answer/action is the worst failure.

Our thesis is that both failures are the **same statistical problem** — *selective prediction under uncertainty* — and can be solved together:
> **"I can't reliably find that button, so I'll ask you"** (action **deferral**) and
> **"your history doesn't support an answer, so I'll say 'not found'"** (answer **abstention**)
> are two faces of one skill: **knowing when not to commit.**

We train a *small, on-device* model to have this calibrated behavior across **both** its jobs, using one shared calibration method and one shared training pipeline.

### 2.2 The two fine-tuning tracks (the ML core)
We fine-tune small open models (3–8B parameters, e.g., Qwen2.5-7B) using **QLoRA** — a memory-efficient method that fits on a single consumer GPU / Colab. Two tracks, same recipe:

1. **Grounded memory QA + calibrated refusal** — given a question + retrieved history chunks, produce a *cited* answer, or *abstain* when unsupported.
2. **Web action grounding + calibrated deferral** — given a goal + the page's accessibility tree, produce the *next action*, or *defer to the user* when uncertain or when the action is risky.

**Training method (per track):**
- **Distillation + SFT (Supervised Fine-Tuning):** learn the task shape from thousands of examples (a strong "teacher" model generates and verifies them; cheap to produce). We deliberately include *negative examples* (hallucinations, invalid actions) so the model learns what *not* to do.
- **DPO (Direct Preference Optimization):** refine using *preference pairs* — "this grounded/cited answer is better than that fabricated one," "this safe deferral is better than that reckless click." Crucially, these pairs are **mined from the model's own failures**, so the model improves exactly where it's weak.
- **Quantization to GGUF** for fast, low-memory on-device inference.

The fine-tuned model then **plugs into the extension unchanged** — the product already talks to the local model through a fixed interface, so we simply swap the base model for the fine-tuned one.

### 2.3 What is *new* (the contributions)
Reviewers reward clear, defensible novelty. Ours:
1. **A unified calibrated-grounding framework** — the first to treat *answer abstention* and *action deferral* as one selective-prediction problem with one shared calibration + preference-tuning pipeline. (The literature treats grounded-QA refusal and web-action safety as two separate fields; nobody has connected them.)
2. **Calibrated safe-action deferral on a *small on-device* model** — prior work on "when to ask for help" is for robots or uses huge frontier models; doing it inside a 3–8B model running in a browser extension is unaddressed.
3. **Retrieval-augmented action grounding** — using the user's *own browsing history* as in-context examples to help the small model handle *unseen websites* (a known open problem for small web agents).
4. **A released benchmark** — see §2.4.
5. **A safety result** — calibrated deferral as a *defense-in-depth fail-safe* against prompt injection (it holds even when other defenses are bypassed), plus a first look at *cross-session* injection (malicious text captured yesterday firing when recalled today).
6. **An efficiency result** — an honest accuracy-vs-cost/latency/energy comparison of the small local model against a cloud model (the on-device story cloud-only papers can't tell).

### 2.4 The benchmark we release — *Personal-Memory-RGB*
There is **no standard benchmark** for grounded QA + calibrated refusal over a *user's own, timestamped, noisy browsing memory*. We build and release one:
- **Fully synthetic** (fabricated but self-consistent facts) so it is freely shareable — no privacy risk, no copyright.
- Six question types: *answerable* (single-hop, multi-hop, time-scoped) and *must-abstain* (not-in-history, **stale**, **false-premise**).
- Split by user-history so we test true generalization.
- Reports refusal precision/recall, risk-coverage curves, abstention AUROC, plus answer-faithfulness and citation accuracy.

A released, well-documented benchmark is often the *highest-impact* part of a student paper (reviewers value reusable artifacts), and is a natural fit for a "Datasets & Benchmarks" track.

### 2.5 How we evaluate (rigor)
Three-pronged, matching the three claims:
- **Grounded QA:** faithfulness, citation precision/recall, and refusal calibration (does it abstain at the right times?).
- **Action grounding:** element/step accuracy and task success on standard web-agent benchmarks, plus a *deferral coverage guarantee*.
- **Safety & efficiency:** attack-success reduction under *adaptive* injection attacks; and latency/energy/cost vs a cloud baseline.

Throughout: multiple runs with variance (not single-run numbers), clean ablations (base model vs SFT vs SFT+DPO), and full reproducibility (code, data, seeds, hyperparameters) — the things reviewers reject papers for lacking.

### 2.6 Why it's "IEEE-level and above"
It combines four areas that are individually publishable and jointly novel: **systems** (a real MV3 extension that sees+acts), **ML** (efficient fine-tuning of small models), **NLP** (retrieval-augmented generation + calibrated abstention), and **safety** (prompt-injection defense) — delivered with a **released artifact** and **honest evaluation**. Web/GUI agents are one of the hottest research areas of 2025–26, so the work is timely and career-relevant for ML/NLP/LLM research.

**Publication plan (timeline-aware):** a guaranteed archival venue (**IEEE Access**, rolling submission) for the full system, with a stretch target of a top-tier **Datasets & Benchmarks** track once the benchmark and fine-tuning results are in.

---

## 3. How the product and the research reinforce each other

This is the elegant part — they are not two separate efforts:
- The **product is the research testbed**: it runs on a real browser, generating real observations, real answers, and — importantly — **real failures**.
- Those failures become **training data** (the preference pairs for DPO), so the deployed product creates a *private, on-device self-improvement flywheel* that lab-only systems can't have.
- The **benchmark measures** whether fine-tuning actually improved calibration.
- The **fine-tuned model plugs straight back into the product**.

So the research makes the product more trustworthy, and the product makes the research possible and honest.

---

## 4. Current status (honest)

We are at the **end of the foundation phase (Month 1 of ~6)**. Everything below is committed to GitHub.

**Done and working:**
- Full planning knowledge base (vision, product, architecture, research plan, related-work survey of ~40 papers, benchmark spec) + professional project scaffolding (license, security policy, safety changelog, CI, contribution guide).
- **The benchmark (v0)** — generator + evaluator + a real baseline system — *runs today* and already produces a meaningful, reproducible result (a lexical baseline fails exactly where a learned model must help — e.g., time-scoped recall — which motivates the fine-tuning).
- **The extension** — the complete pipeline is coded and *compiles/builds*: it can observe a page, act on it (with confirmation gates), remember pages, answer with citations or refuse, run a multi-step agentic task, and it has a settings/privacy panel (capture toggle, sensitive-domain blocklist, memory wipe). The embedding model is bundled for fully-offline capture.

**Deliberately not started yet:**
- **The fine-tuning itself (the research core).** By design — you establish the *base-model baseline* first, then fine-tune, then measure the improvement. Fine-tuning without a benchmark and a baseline is flying blind. This is Months 2–4.

**Honest caveat:** the extension is *build-verified* (it compiles and bundles) but has not yet been *run in a live Chrome browser* — that runtime verification (which needs a local model server, Ollama) is the immediate next step.

---

## 5. Roadmap (~6 months)

| Month | Focus |
|---|---|
| **M1 (done)** | Foundation: extension skeleton, local memory, benchmark v0, base-model baseline. |
| **M2** | Build the QA training data; **SFT** the grounded-QA model. |
| **M3** | **DPO** on mined failures; measure the refusal-calibration improvement. |
| **M4** | The action-grounding model (SFT + DPO); the deferral behavior. |
| **M5** | Safety + efficiency evaluation; quantize + optimize for on-device. |
| **M6** | Finalize the benchmark release, run all experiments, **write the paper**. |

---

## 6. Technology stack (brief)

- **Extension:** WXT + React + TypeScript (Chrome MV3); Chrome DevTools Protocol for observe/act.
- **Local memory:** Readability (text extraction), transformers.js embeddings (bge-small, bundled offline), PGlite (in-browser vector database).
- **Local model:** Ollama serving a quantized (GGUF) small model; Qwen2.5-7B base today, fine-tuned adapters later.
- **Fine-tuning:** QLoRA via Unsloth; SFT then DPO (with ORPO/SimPO/KTO as comparison points); on a single consumer GPU / Colab Pro.
- **Benchmark & evaluation:** Python (standard-library only for v0).

---

## 7. What we are careful *not* to claim (integrity)

- We **do not** claim to "solve" prompt injection — it is an open problem; we add a measurable *fail-safe* and evaluate honestly against adaptive attacks.
- We **do not** claim to beat cloud models on raw capability — we claim a better *reliability-under-uncertainty per unit of cost/energy*, with privacy, on a focused task distribution.
- We report metrics **with variance and caveats**, and release code + data so results are checkable.

---

## 8. The one-line pitch (for your mentor)

> *"I'm building a private, on-device AI browser assistant that helps you research and remember what you read, and I'm doing the ML research to make a small local model reliable enough to be trusted — by teaching it to know when it doesn't know. The product is the testbed and the paper is the contribution; they feed each other, and I release a new benchmark to prove it works."*

---

*Deeper detail on any section: product → [`01_PRODUCT_PLAN.md`](01_PRODUCT_PLAN.md); architecture → [`02_TECHNICAL_ARCHITECTURE.md`](02_TECHNICAL_ARCHITECTURE.md); research → [`03_RESEARCH_PAPER_PLAN.md`](03_RESEARCH_PAPER_PLAN.md); prior work → [`04_RELATED_WORK.md`](04_RELATED_WORK.md); benchmark → [`05_BENCHMARK_Personal_Memory_RGB.md`](05_BENCHMARK_Personal_Memory_RGB.md).*
