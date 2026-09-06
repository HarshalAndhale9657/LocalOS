# Groundwork — Project Docs

**A privacy-first, local-first *agentic browser assistant* (Chrome MV3) that sees and controls your browser to do private research, on-demand data extraction, and grounded recall — powered by fine-tuned small local models that know when they don't know.**

This folder is the planning knowledge base for a final-year graduation project **and** an IEEE-level-and-above research paper. Product name **Groundwork** (repo dir `d:\LocalOS`).

> These docs were produced from a deep research pass over the 2023–2026 agentic-browser product landscape and the web-agent / RAG / fine-tuning / agent-safety literature (~40 papers + the full competitor field). The two files in the repo root (`secondbrain.md`, `Second_Brain_Project_Documentation_Professional.pdf`) are **inspiration only, not this project.**

---

## Read in this order

0. **[07 — Revised Plan (2026-09-06)](07_REVISED_PLAN_2026-09.md)** — **the current plan.** Supersedes the timelines, scope, and experiment matrix in 01/03/06 wherever they disagree: one fine-tuning track (QA refusal), unification tested as a transfer hypothesis, action track deferred, 16-week schedule to a January 2027 submission. *Read this before anything below.*
1. **[00 — Master Vision & Knowledge](00_MASTER_Vision_and_Knowledge.md)** — the "why", the market reality, positioning, the unified **calibrated-grounding** thesis, novelty claims, glossary, and the open decisions. *Start here.*
2. **[01 — Product Plan](01_PRODUCT_PLAN.md)** — personas, jobs-to-be-done, feature spec (MoSCoW), UX flows, roadmap, metrics, risks, go-to-market.
3. **[02 — Technical Architecture](02_TECHNICAL_ARCHITECTURE.md)** — MV3 sense+act layer, local RAG memory, model serving, safety architecture, feasibility & MV3 constraints.
4. **[03 — Research Paper Plan](03_RESEARCH_PAPER_PLAN.md)** — RQs, contributions, methodology (both fine-tuning tracks), the released benchmark, experiment matrix, metrics, reproducibility, ethics, venue strategy, paper outline.
5. **[08 — Learning Roadmap](08_LEARNING_ROADMAP.md)** — what the owner needs to learn to *defend* this work: ordered topics, verified paper IDs, courses/blogs, a mock-viva question bank. Read alongside 07.
6. **[04 — Related Work](04_RELATED_WORK.md)** — annotated bibliography by theme + the exact gap Groundwork fills.

---

## The thesis in one line

> **Calibrated grounding for on-device browser agents:** one small local model family, refined by SFT→DPO on its own mined failures, learns to *act*, *answer*, and — crucially — to **abstain or ask** when uncertain, under one selective-prediction framework spanning both **web action grounding** and **grounded memory QA**. Calibrated abstention doubles as a prompt-injection fail-safe.

## Why it's novel (and safe to claim)

The literature treats **action grounding**, **grounded-QA refusal**, and **agent safety** as three separate conversations. **No shipping product** combines an MV3 extension + fine-tuned *small local* models + local RAG memory + agentic control. Groundwork unifies the first three on a small on-device model over a personal-history RAG, in the unoccupied product intersection — and releases a benchmark. See [00 §5](00_MASTER_Vision_and_Knowledge.md) / [04](04_RELATED_WORK.md).

---

## Locked decisions

| Architecture | Research core | Flagship use | Compute |
|---|---|---|---|
| Hybrid, **local-first** | **2 tracks:** action grounding + grounded QA/refusal | Research · recall · extraction (transactions deferred) | Train on **Colab Pro / paid cloud (A100/L4)**; ship **QLoRA 3B–8B, GGUF 4-bit** on-device |

**Confirmed 2026-08-21:** name = **Groundwork** · timeline ≈ **6 months** · training compute = **Colab Pro / paid cloud** · **build + benchmark start now**.

Defaults still standing (accept or correct): model count (shared base + 2 LoRA adapters), priority track (QA-refusal first), cloud planner (optional BYO-key + offline), venue (IEEE Access + NeurIPS 2027 D&B). Still needed: the **consumer machine** for inference/efficiency benchmarking, and the **data-budget ceiling**. Full status in [00 §10](00_MASTER_Vision_and_Knowledge.md#10-decisions--status).

---

## Now building (M1) + drafting the benchmark

- **[05 — Personal-Memory-RGB benchmark spec](05_BENCHMARK_Personal_Memory_RGB.md)** — the released research artifact.
- **[06 — M1 build plan](06_M1_BUILD_PLAN.md)** — concrete engineering tickets to stand up the extension shell + local RAG memory + base-model baseline.

*Status: M1 code complete but not yet run in Chrome; benchmark v0 validates the harness only. Plan revised 2026-09-06 under confirmed constraints (3–4 months, borrowed GPU laptop, Colab, small API budget, two teammates) — see [07](07_REVISED_PLAN_2026-09.md). Last updated 2026-09-06.*
