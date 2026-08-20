# LocalOS — Project Docs

**A privacy-first, local-first *agentic browser assistant* (Chrome MV3) that sees and controls your browser to do private research, on-demand data extraction, and grounded recall — powered by fine-tuned small local models that know when they don't know.**

This folder is the planning knowledge base for a final-year graduation project **and** an IEEE-level-and-above research paper. Codename `LocalOS` (naming TBD — see below).

> These docs were produced from a deep research pass over the 2023–2026 agentic-browser product landscape and the web-agent / RAG / fine-tuning / agent-safety literature (~40 papers + the full competitor field). The two files in the repo root (`secondbrain.md`, `Second_Brain_Project_Documentation_Professional.pdf`) are **inspiration only, not this project.**

---

## Read in this order

1. **[00 — Master Vision & Knowledge](00_MASTER_Vision_and_Knowledge.md)** — the "why", the market reality, positioning, the unified **calibrated-grounding** thesis, novelty claims, glossary, and the open decisions. *Start here.*
2. **[01 — Product Plan](01_PRODUCT_PLAN.md)** — personas, jobs-to-be-done, feature spec (MoSCoW), UX flows, roadmap, metrics, risks, go-to-market.
3. **[02 — Technical Architecture](02_TECHNICAL_ARCHITECTURE.md)** — MV3 sense+act layer, local RAG memory, model serving, safety architecture, feasibility & MV3 constraints.
4. **[03 — Research Paper Plan](03_RESEARCH_PAPER_PLAN.md)** — RQs, contributions, methodology (both fine-tuning tracks), the released benchmark, experiment matrix, metrics, reproducibility, ethics, venue strategy, paper outline.
5. **[04 — Related Work](04_RELATED_WORK.md)** — annotated bibliography by theme + the exact gap LocalOS fills.

---

## The thesis in one line

> **Calibrated grounding for on-device browser agents:** one small local model family, refined by SFT→DPO on its own mined failures, learns to *act*, *answer*, and — crucially — to **abstain or ask** when uncertain, under one selective-prediction framework spanning both **web action grounding** and **grounded memory QA**. Calibrated abstention doubles as a prompt-injection fail-safe.

## Why it's novel (and safe to claim)

The literature treats **action grounding**, **grounded-QA refusal**, and **agent safety** as three separate conversations. **No shipping product** combines an MV3 extension + fine-tuned *small local* models + local RAG memory + agentic control. LocalOS unifies the first three on a small on-device model over a personal-history RAG, in the unoccupied product intersection — and releases a benchmark. See [00 §5](00_MASTER_Vision_and_Knowledge.md) / [04](04_RELATED_WORK.md).

---

## Locked decisions

| Architecture | Research core | Flagship use | Compute |
|---|---|---|---|
| Hybrid, **local-first** | **2 tracks:** action grounding + grounded QA/refusal | Research · recall · extraction (transactions deferred) | Single consumer GPU / Colab → QLoRA 3B–8B, GGUF 4-bit |

## Decisions to confirm (I defaulted these — correct any)

1. **Model count** → shared base + **two LoRA adapters** (default).
2. **Priority track if time is short** → **QA-refusal first**, action-grounding as headline stretch.
3. **Cloud planner** → **optional BYO-key** (content-blind) **+** first-class **offline mode**.
4. **Benchmark release** → **yes** (Personal-Memory-RGB) — highest-leverage move.
5. **Name** → keep `LocalOS` as codename; recommend **Groundwork** (alts: Marginalia, Understory).
6. **Timeline** → assumed ~6 months solo — *tell me your real dates.*
7. **Target GPU** for the paper's efficiency numbers — *tell me your actual card.*
8. **Data budget** → small cloud spend OK for teacher/AgentTrek data? Confirm.
9. **Primary archival venue** → **IEEE Access** (rolling, guaranteed) + **NeurIPS 2027 D&B** stretch (near-term 2026 workshop deadlines are largely unreachable from an Aug-2026 start).

Full rationale in [00 §10](00_MASTER_Vision_and_Knowledge.md#10-decisions-to-confirm).

---

## Immediate next steps

- **You:** answer the 9 confirmations above (especially timeline, GPU, name, venue priority).
- **Then:** M1 of the [roadmap](01_PRODUCT_PLAN.md#8-roadmap-generic-6-month-plan--anchor-to-your-real-dates) — fork Nanobrowser's shell, stand up the PGlite RAG memory, reproduce a base-model grounded-QA baseline, and draft the Personal-Memory-RGB schema.

*Status: planning complete, awaiting your confirmations. Last updated 2026-08-21.*
