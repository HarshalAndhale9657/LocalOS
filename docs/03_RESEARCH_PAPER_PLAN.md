# 03 — Research Paper Plan

> The plan to turn Groundwork into an **IEEE-level-and-above** publication that strengthens an ML/NLP/LLM research career. Companion to [00_MASTER](00_MASTER_Vision_and_Knowledge.md) (thesis) and [04_RELATED_WORK](04_RELATED_WORK.md) (bibliography). Audience of this doc: you, writing the paper.

---

## 1. The paper in one sentence

> *We show that a single small on-device model family, refined by SFT then preference optimization on its own mined failures, can act in and answer about the browser while **knowing when it doesn't know** — a unified **calibrated-grounding** framework that abstains from unsupported answers and defers uncertain/high-risk actions, matching far larger cloud agents on a private research/extraction/recall distribution at a fraction of the cost, and turning abstention into an indirect-prompt-injection fail-safe — released with a reproducible benchmark.*

**Paper archetype:** a **benchmark/dataset + method** paper (reviewers reward well-documented, reusable artifacts over raw SOTA — the realistic winning shape for a solo author).

---

## 2. Research questions

- **RQ1 (Unification).** Can web **action deferral** and grounded-QA **answer abstention** be posed and solved as *one* selective-prediction problem — one conformal calibration method + one mined-failure preference pipeline — rather than two separate systems?
- **RQ2 (Small-model calibration).** Does SFT→DPO on *mined failures* move a 3B–8B on-device model to a **better selective-risk operating point** (risk-coverage / abstention AUROC) than off-the-shelf models and its own SFT-only variant, on *both* tracks?
- **RQ3 (Retrieval-augmented grounding).** Does using the user's **own browsing history** as in-context exemplars close the **unseen-site generalization gap** for a small action model (the gap WebLINX reports)?
- **RQ4 (Safety fail-safe).** Does calibrated deferral **reduce indirect-prompt-injection success and raise Completion-under-Policy under adaptive attack**, as defense-in-depth *on top of* spotlighting/instruction-hierarchy? Can we characterize and defend **cross-session stored injection** via the RAG index?
- **RQ5 (Efficiency).** What is the **accuracy-vs-cost/latency/energy Pareto** for running the two fine-tuned GGUF models (+ a calibrated local↔cloud router) on one consumer GPU — and how gracefully does the system degrade fully offline?

---

## 3. Contributions (map to [00 §5](00_MASTER_Vision_and_Knowledge.md))

- **C1 — Conceptual:** the **unified calibrated-grounding framework** (RQ1). *No cited work unifies grounded-QA refusal (Trust-Align/RefusalBench) with action-abstention (KnowNo/WebGuard/UQ-for-CUA).*
- **C2 — Method:** **calibrated safe-action deferral on a small on-device web-action model** — conformal *when-to-ask* + SAFE/CAUTION/UNSAFE risk head + DPO-on-mined-failures in one 3B–8B GGUF model over a DOM/AX-tree (RQ2, RQ4).
- **C3 — Method:** **retrieval-augmented action grounding** using personal history as per-site priors (RQ3).
- **C4 — Artifact:** **Personal-Memory-RGB**, the first grounded-QA + must-abstain benchmark over a user's own browsing history (answerable / not-in-history / stale / false-premise), + a **browser action-safety split** (CuP under adaptive attack). Released with a datasheet.
- **C5 — System/efficiency:** the **on-device accuracy-vs-cost Pareto** for two concurrent fine-tuned GGUF models + a calibrated escalation router (RQ5).
- **C6 — (stretch):** a **privacy-preserving, on-device failure-mining flywheel** (DPO/KTO pairs built from real user-flagged failures, never leaving the device) and a **local WebJudge** auto-evaluator validated against human agreement.

> **Priority if time is short:** C1 + C4 + the QA half of C2 are the guaranteed core; C3, C5, C6 and the action half of C2 are stretch. The unified framing carries the paper even if one track thins.

---

## 4. Methodology

### 4.1 Models
- **Base:** Qwen2.5-7B-Instruct (primary) / Qwen3-4B-Instruct-2507; 3B tier: Llama-3.2-3B or SmolLM3-3B; Phi-4-mini as a function-calling alternative.
- **Adapters:** two LoRA adapters on the shared base (action; QA), 4-bit **QLoRA** (NF4, r=16, α=32, dropout 0.05, on attn+MLP proj) via **Unsloth**.
- **Serving:** merge → **GGUF Q4_K_M** → llama.cpp/Ollama (measure pre/post-quant quality & latency).

### 4.2 Track 1 — Web action grounding (+ deferral)
- **Data:** teacher (cloud LLM) trajectories over the target domains (research/extraction), synthesized cheaply via **AgentTrek**-style tutorial replay (~$0.55/traj); **APIGen**-style **execute-and-verify** gate (keep only trajectories whose actions actually succeed in a headless browser); inject **negative samples** (nonexistent-element clicks, malformed calls) Agent-FLAN-style.
- **Train:** distill → SFT (+negatives) → **DPO on mined failures** (contrast failed vs successful trajectories; Agent-Q logic).
- **Deferral head:** conformal calibration (KnowNo) over next-action likelihood → abstain/ask when coverage target isn't met; SAFE/CAUTION/UNSAFE risk head trained on WebGuard-style labels.

### 4.3 Track 2 — Grounded memory QA (+ refusal)
- **Data:** **Trust-Align**-style pos/neg pairs with **NLI-verified citations**; seed unanswerable/stale from **SQuAD 2.0** + **RealTimeQA**, re-instantiated over synthetic browsing histories; mine negatives from the deployed agent's own recall failures.
- **Train:** abstention-aware **SFT** (target = cited answer **or** "not found in your history") → **DPO** on hallucination-vs-refusal pairs.
- **Refusal gate:** retrieval-score threshold + **Semantic Entropy Probe** (single-pass, on-device) + NLI entailment of each claim vs cited chunk; ECE-calibrated threshold; conformal option for a coverage guarantee.

### 4.4 Unified calibration (the C1 glue)
Both heads expose an abstention/deferral signal in **one selective-prediction interface**; one conformal procedure sets thresholds for both; one **mined-failure preference pipeline** feeds both. This shared machinery *is* the conceptual contribution — describe it as a single algorithm instantiated twice.

### 4.5 Preference-optimizer bake-off
Because agent/RAG failures are **naturally binary** (action succeeded/failed; answer grounded/hallucinated), compare **DPO vs ORPO vs SimPO vs KTO** under the 16–24 GB budget, reporting quality **and** VRAM/wall-clock. (Agent papers almost universally use plain DPO — this ablation is low-cost, high-value.)

---

## 5. Evaluation harness (three-pronged, matching the three claims)

### 5.1 Action grounding
- **Metrics:** Element Accuracy, Step Success Rate, Action-F1, trajectory Progress Rate; live **Task Success Rate** via a **WebJudge-style auto-judge** (validated vs human, report κ/accuracy — AGENTREWARDBENCH methodology).
- **Benchmarks:** **Online-Mind2Web + WebJudge** (300 live tasks/136 sites, difficulty tiers) primary; **Mind2Web** (offline element/step) for the unseen-site gap; **WebArena / WebArena-Lite** (BrowserGym) with **WebRL** (8B 4.8→42.4%) as the failure-refinement baseline; **WebVoyager** (multimodal reference).

### 5.2 Grounded memory QA
- **Metrics:** **RAGAS** quartet (faithfulness, answer relevancy, context precision/recall); **ALCE** citation precision/recall (NLI-checked, with CIs — attribution judging tops out ~80% F1, so report honestly); **Trust-Score** (mean of refusal-F1, answer-correctness-F1, NLI-citation-F1).
- **Benchmarks:** **Personal-Memory-RGB** (ours) + re-instantiated **RGB / CRAG / RAGTruth** categories.

### 5.3 Calibrated refusal / deferral (selective prediction)
- **Metrics:** refusal **precision/recall** on unanswerable/negative splits; **risk-coverage curves**; **abstention AUROC** (note: output-confidence readouts ≈ 0.54–0.67 vs hidden-state ≈ 0.97–0.99 — test both); deferral **coverage guarantee** (conformal).
- **Method sources:** AbstentionBench, "Two Axes of Abstention", RefusalBench.

### 5.4 Safety
- **Metrics:** attack-success rate, **Completion-under-Policy (CuP)** + Risk-Ratio (ST-WebAgentBench); utility-under-**adaptive**-attack.
- **Testbeds:** **AgentDojo**, **WASP**, **Mind-the-Web**, **InjecAgent**; **WebGuard** risk data; + our **cross-session stored-injection** experiment.

### 5.5 Efficiency
- **Metrics:** TTFT, end-to-end latency, tokens/task, tok/s, **peak memory**, **tok/J energy**; **pass@k / pass^k** reliability.
- **Deliverable:** the **accuracy-vs-cost/latency/energy Pareto** (local 4-bit vs cloud planner vs router), the paper's headline efficiency figure.

---

## 6. Experiment matrix (the results tables)

| # | Experiment | Answers | Decisiveness |
|---|---|---|---|
| E1 | **SFT vs SFT+DPO** on both tracks, with risk-coverage + AUROC before/after | RQ2 | ★★★ most reviewer-decisive |
| E2 | **DPO vs ORPO vs SimPO vs KTO** on binary on-device failures (quality/VRAM/time) | RQ2 | ★★ cheap, novel-ish |
| E3 | **History-RAG-augmented grounding vs no-memory** on unseen sites; step-SR uplift vs #exemplars | RQ3 | ★★★ |
| E4 | **Conformal deferral sweep:** interventions-asked vs task-success vs attack-success; verify coverage guarantee | RQ1/RQ4 | ★★ |
| E5 | **Injection fail-safe:** attacks with defenses/deferral ON vs OFF; **adaptive** attacks; CuP | RQ4 | ★★★ |
| E6 | **Cross-session stored injection:** plant day-1, trigger recall day-2; exploitation w/ vs w/o untrusted-history handling | RQ4 | ★★ novel threat |
| E7 | **Local↔cloud escalation router:** success vs $/tokens/latency; offline degradation | RQ5 | ★★ |
| E8 | **Negative-sample SFT ablation** (Agent-FLAN): hallucinated-action reduction *before* DPO | RQ2 | ★ isolates data vs tuning |
| E9 | **Functional-token vs JSON actions:** context/latency/accuracy | RQ5 | ★ |
| E10 | **Matryoshka index sweep:** retrieval quality vs IndexedDB footprint (128/256/512/768) | RQ5 | ★ |
| E11 | **Local WebJudge vs GPT-4V-judge:** human-agreement | C6 | ★ methods |
| E12 | **Concurrent-model systems benchmark:** peak mem/TTFT/tok-s/energy running both models + extension | RQ5 | ★★ undocumented |

**Baselines throughout:** the **teacher** cloud LLM; an **off-the-shelf** same-size SLM (no fine-tuning); a **cloud** frontier planner; the **SFT-only** ablation; and (where available) published web-agent numbers (WebRL, Agent-Q). Every accuracy number is paired with cost/latency to argue an **efficiency-accuracy Pareto**, not raw SR.

---

## 7. The released benchmark — *Personal-Memory-RGB*

**Why it's the highest-leverage move:** no standard benchmark exists for grounded QA + calibrated refusal over a user's *own* browsing history. Releasing one is a natural **NeurIPS/ICLR Datasets & Benchmarks** contribution and a durable citation magnet.

**Construction:**
- **Corpus:** privacy-scrubbed **synthetic browsing histories** (generated + curated so nothing personal is released) with realistic noise, timestamps, near-duplicates.
- **Splits:** **Answerable** (single-hop, multi-hop, time-scoped) · **Not-in-history** (never read → must refuse) · **Stale** (read, but time-sensitive/outdated) · **False-premise** (question presupposes something untrue).
- **Labels:** ground-truth answer + exact source chunk + read-date; gold "abstain" targets for negatives.
- **Action-safety split:** a browser DOM/AX-tree adaptation of ST-WebAgentBench tasks with policy annotations for **CuP under adaptive attack**.
- **Reporting bundle:** Trust-Score + ALCE citation P/R + RAGAS faithfulness/context-precision + refusal P/R + risk-coverage/AUROC — jointly, which nothing currently does.
- **Release:** datasheet (Gebru et al.), public code+data, fixed seeds, a **local** auto-evaluator.

---

## 8. Reproducibility & rigor (the acceptance gate)

ML papers are rejected for **weak evidence** far more than for unoriginal ideas, and review is noisy (~25% of decisions flip). So front-load rigor:

- **Multi-run:** every task 3–5×; report **mean ± std** and **pass^k** consistency; test **paraphrase robustness**.
- **Ablations:** E1/E2/E3/E8 are the spine — reviewers reject papers lacking exactly these.
- **Full disclosure:** seeds, all hyperparameters (QLoRA rank/α, DPO β, learning rates, data sizes), hardware.
- **Artifacts:** public code + data + models + **datasheet**; satisfy the **ACL Responsible NLP checklist** / **NeurIPS D&B** requirements *from the start* (desk-reject risk otherwise).
- **Honesty:** frame safety as **defense-in-depth, never solved**; report against the public **11.2% Claude-for-Chrome** injection number; give citation accuracy with CIs; don't inflate.

---

## 9. Ethics & threat-model section (required, and a strength here)

- **Dual-use / safety:** an agent that controls a browser is attackable; we evaluate against adaptive injection and *reduce* (not eliminate) risk; transactions are out of scope.
- **Privacy:** page content/index/models stay on-device; only privacy-scrubbed synthetic data is released; the deployed flywheel mines failures **locally**.
- **Legal:** we do **not** act on third-party authenticated sessions (CFAA-aware).
- **Threat table:** IPI, cross-session stored injection, embedding inversion, index tampering, malicious-extension limits (from [02 §6.3](02_TECHNICAL_ARCHITECTURE.md)).

---

## 10. Venue strategy (timeline-aware; today is 2026-08-21)

> ⚠️ **Reality check on dates.** From an Aug-2026 start with a ~6-month build, results land ~**Feb–Apr 2027**. Several attractive 2026 deadlines are **already unreachable** (NeurIPS 2026 SLM-Agents workshop ~Aug 29 2026; NeurIPS 2026 D&B ~May 2026). Plan around **rolling** venues and **2027** cycles.

**Tier 0 — feedback/visibility (non-archival, if you can accelerate the QA track):**
- **TrustNLP @ ACL 2026** (~Mar 5 2026 deadline) — ideal for the calibrated-refusal angle, but *very* tight from an Aug-2026 start; only if the QA track is done early. Otherwise target its **2027** edition.
- Any **agents / efficient-ML workshop** at ICLR/ACL/EMNLP **2027** — near-perfect topical fit; non-archival, so you can extend later.

**Tier 1 — highest-prestige archival (the strongest career play):**
- **NeurIPS 2027 Datasets & Benchmarks** (~May 2027 deadline) built around **Personal-Memory-RGB** + the on-device action-trajectory data + local WebJudge. D&B reviewers reward reusable, well-documented artifacts over SOTA — the best fit for a solo timeline.
- **ICLR 2028** (~Sept 2027) as the alternative.

**Tier 2 — guaranteed archival IEEE deliverable (for graduation):**
- **IEEE Access** (JIF ~4.2, Q2, ~40–45% accept, **rolling** submission, fast OA) — the reliable archival home for the full-system writeup; submit ~Feb–Apr 2027 when the system + results are ready. **This is the safe graduation deliverable.**
- **IEEE COMPSAC 2027** — the privacy-first on-device agentic **system** paper. (COMPSAC 2026's Feb-20-2026 deadline is past.)
- **IEEE Big Data 2026/2027** — the RAG-over-browsing-history subsystem (retrieval/dedup/embedding). Check the live CFP for the reachable cycle.

**Recommended sequence:** build → **IEEE Access** (guaranteed graduation publication, rolling) → extend the vetted work into **NeurIPS 2027 D&B** (prestige) → present pieces at 2027 agent/trust workshops for visibility. Confirm your archival priority ([00 §10 #9](00_MASTER_Vision_and_Knowledge.md)).

---

## 11. Paper outline (standard, ~8–10 pp + appendix)

1. **Abstract** — unified calibrated-grounding; on-device; benchmark; honest efficiency/reliability claims.
2. **Introduction** — the cloud-agent trust gap (injection, privacy, cost); the small-local-model opportunity; contributions C1–C6.
3. **Related Work** — a **grid** separating our intersection from: action grounding (Mind2Web/WebLINX/WebRL/Agent-Q/UI-TARS), grounded-QA-refusal (Trust-Align/RefusalBench/AbstentionBench), agent safety (KnowNo/WebGuard/CaMeL/ST-WebAgentBench), on-device SLMs. (Source: [04](04_RELATED_WORK.md).)
4. **Problem & Framework** — selective prediction unifying action deferral + answer abstention (C1); formalize the shared conformal/preference machinery.
5. **System** — sense/act/remember/reason/guard ([02](02_TECHNICAL_ARCHITECTURE.md)), compressed for the paper.
6. **Data & Training** — distillation, execute-verify, negatives, SFT→DPO, the optimizer bake-off.
7. **Benchmark** — Personal-Memory-RGB + action-safety split + local WebJudge (C4).
8. **Experiments** — E1–E12; the three-pronged metrics; the efficiency Pareto figure.
9. **Safety analysis** — injection fail-safe + cross-session stored injection, under adaptive attack (C2/RQ4).
10. **Discussion / limitations** — unseen-site scope, attribution-judging noise, "not solved."
11. **Conclusion + broader impact + ethics.**
12. **Appendix** — datasheet, hyperparameters, prompts, judge-agreement, per-split tables, variance.

---

## 12. Timeline mapping (research ↔ [01 roadmap](01_PRODUCT_PLAN.md))

| Month | Research deliverable |
|---|---|
| M1 | Related-work grid finalized; base-model baselines reproduced; **Personal-Memory-RGB v0 schema** |
| M2 | QA SFT data + **SFT'd QA adapter**; RAGAS/ALCE harness online |
| M3 | **QA DPO** + refusal calibration; E1 (QA half), E8; risk-coverage/AUROC tables |
| M4 | Action SFT+DPO adapter + deferral head; E1 (action half), E3; local WebJudge (E11) |
| M5 | Safety (E4/E5/E6) + efficiency Pareto (E7/E12); E2 optimizer bake-off |
| M6 | Freeze benchmark + datasheet; multi-run variance; **write paper**; submit to IEEE Access; buffer |

---

## 13. What makes this accepted (checklist)

- [ ] A crisp, unifying conceptual claim (C1) reviewers can restate in one line.
- [ ] Strong baselines: teacher, off-the-shelf SLM, cloud planner, SFT-only.
- [ ] The decisive ablations: E1, E2, E3, E8.
- [ ] Multi-run variance + pass^k + paraphrase robustness.
- [ ] A released, documented artifact (benchmark + code + datasheet).
- [ ] Honest safety framing (defense-in-depth; adaptive attacks; vs the 11.2% number).
- [ ] The efficiency Pareto figure (the on-device story cloud papers can't tell).
- [ ] Reproducibility checklist satisfied *before* submission.

---

*Bibliography and per-theme annotations: [04_RELATED_WORK](04_RELATED_WORK.md). Product build: [01](01_PRODUCT_PLAN.md) / [02](02_TECHNICAL_ARCHITECTURE.md).*
