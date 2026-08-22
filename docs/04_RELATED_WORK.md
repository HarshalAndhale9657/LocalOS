# 04 — Related Work & Annotated Bibliography

> Grouped by theme, with *how it relates to Groundwork* and *the gap we fill*. This is the raw material for the paper's Related Work grid ([03 §11](03_RESEARCH_PAPER_PLAN.md)) and the source of the product's differentiation claims ([01 §7](01_PRODUCT_PLAN.md)). Verify every arXiv ID/date against the source before citing in the paper. Compiled 2026-08-21.

**The gap in one line:** the literature has *action grounding*, *grounded-QA refusal*, and *agent safety* as **three separate conversations**. Groundwork is the first to **unify action deferral + answer abstention** as one selective-prediction problem, on a **small on-device model**, over a **personal-history RAG**, in a **Chrome MV3 extension** — with a released benchmark.

---

## A. Web / GUI agents & action grounding

| Work | ID / venue | Why it matters to us |
|---|---|---|
| **Mind2Web** | arXiv:2306.06070 (NeurIPS'23) | First generalist web-agent dataset; DOM two-stage grounding (86M DeBERTa ranks → LLM multi-choice). Element Acc ~55%, **Task SR ~5%** → single-step accuracy must be very high over long horizons ⇒ motivates DPO-on-failures. Our unseen-site baseline. |
| **Mind2Web 2 / Online-Mind2Web** | arXiv:2506.21506 (NeurIPS'25) / 2504.01382 (COLM'25) | Long-horizon agentic **search** + live-site tasks with **Agent-as-a-Judge / WebJudge**. Closest to our flagship (multi-tab research); our **primary live eval** + auto-judge template. |
| **WebArena / VisualWebArena** | 2307.13854 / 2401.13649 | Realistic self-hosted envs; GPT-4 14.4% vs human 78.2%; 2026 SOTA ~71–74%; gains came from **scaffolding/memory/planning**, not bigger bases. BrowserGym is a ready harness. |
| **WebVoyager** | 2401.13919 | 643 live tasks/15 sites; **GPT-4V LLM-as-judge** (85.3% human agreement); SoM helps live even though it hurt offline. Template for our local judge. |
| **WebLINX** | 2402.05930 (ICML'24 spotlight) | **Small fine-tuned models beat zero-shot GPT-4V**; Dense Markup Ranking compresses HTML; **explicitly reports the unseen-site gap** ⇒ our RQ3 opportunity. Key precedent for the local-first thesis. |
| **SeeAct** | 2401.01614 (ICML'24) | **Set-of-Mark grounding is weak on dense webpages** (GPT-4V hallucinates boxes 54%); HTML textual-choice grounding wins ⇒ justifies our **text-first, DOM/AX-tree** design over screenshot-SoM. |
| **UGround / SeeAct-V** | 2410.05243 (ICLR'25 Oral) | 7B **vision-only pixel-coordinate** grounder beats text-input SOTA; the visual alternative. Our **future vision fallback** for canvas/shadow-DOM; we choose DOM/AX-tree for efficiency/privacy. |
| **UI-TARS** | 2501.12326 | Native 2B/7B/72B GUI model, **SFT+DPO** variants, SOTA on 10+ benchmarks ⇒ validates a 7B-class end-to-end agent is feasible; candidate teacher/base. |
| **WebRL** | 2411.02337 | Self-evolving curriculum RL: **Llama-3.1-8B 4.8→42.4%** on WebArena-Lite (2.4× GPT-4-Turbo) via failures ⇒ near-blueprint for failure-driven refinement; our baseline. |
| **Agent Q** | 2408.07199 | MCTS + **trajectory-level DPO on mined failures**: Llama-3-70B OpenTable 18.6→81.7% ⇒ validates SFT-then-DPO-on-failures for Track 1. |
| **Agent-E** | 2407.13032 | Planner/executor split + flexible DOM distillation + change-observation → +10–30% on WebVoyager **without a bigger model** ⇒ cheap product-ready patterns. |
| **AgentTrek** | 2412.09605 (ICLR'25) | Synthesize 10,398 trajectories from web **tutorials** at **$0.55 each** ⇒ our scalable, cheap SFT-data source for a solo timeline. |
| **WebGUM / WebShop / WebGPT / ReAct / MiniWoB++** | 2305.11854 / 2207.01206 / 2112.09332 / 2210.03629 | Foundations: action vocabulary, ReAct thought traces, instruction-finetuning gains, sim benchmarks. |
| **"Beyond Pixels: DOM Downsampling"** | 2508.04412 (2025) | Screenshots add little over AXTree once grounding is good (p>0.5) ⇒ backs text-first observation. |
| **Failure taxonomies** | 2509.25370 / TRAIL 2505.08638 | Top killers = grounding errors, hallucinated elements, long-horizon error propagation ⇒ exactly what calibrated grounding + DPO target. |

**Gap we fill:** unseen-site generalization is open (WebLINX); no one couples a **personal-history RAG** with a **small on-device** action model, and none add **calibrated action abstention**.

---

## B. Agent fine-tuning, small/on-device LLMs, preference optimization

| Work | ID | Why it matters |
|---|---|---|
| **AgentTuning / AgentLM** | 2310.12823 | Generalizing agent from **1,866 GPT-4 trajectories** (reward-filtered) ⇒ Track 1 needs thousands, not millions. |
| **FireAct** | 2310.05915 | Fine-tune small LM on ~500 GPT-4 ReAct trajectories → +77% HotpotQA. |
| **Agent-FLAN** | 2403.12881 (ACL'24 Findings) | **Negative samples** cut hallucinated/invalid actions (+3.5%) ⇒ our E8 ablation. |
| **xLAM / APIGen / xLAM-2** | 2406.18518 | 7B matches GPT-4 function-calling; **execute-and-verify** 3-stage data filter ⇒ our trajectory quality gate; Top-1 BFCL v3. |
| **Octopus v2** | 2404.01744 | 0.5B on-device **functional-token** action model: 99.5% acc, 0.38 s, ~95% context cut ⇒ our optional functional-token action decoding (E9). |
| **ToolLLM / AgentGym / Lumos** | 2307.16789 / 2406.04151 / 2311.05657 | Tool-learning corpora, 14-env self-evolution (AgentEvol), modular planning+grounding data formats ⇒ reusable formats + metrics. |
| **QLoRA** | 2305.14314 | 4-bit NF4 LoRA matches 16-bit within ~2% ⇒ the compute-budget enabler. |
| **Unsloth** | (blog) | 8B QLoRA ~7 GB VRAM, 2–5× faster ⇒ fits Colab/Kaggle T4/L4. |
| **DPO / SimPO / ORPO / KTO** | 2305.18290 / 2405.14734 / 2403.07691 / (KTO) | Preference-optimization family. **SimPO** reference-free (~10% less VRAM); **ORPO** single-stage no-reference; **KTO** unpaired binary labels (natural fit — action-success/answer-grounding are binary) ⇒ our E2 bake-off. |
| **GGUF vs AWQ vs GPTQ vs bnb (2026)** | (PremAI) | **GGUF Q4_K_M** best on-device 4-bit (~6% perplexity gap); AWQ for GPU servers ⇒ our serving format. |
| **Browser vs native LLM perf** | (9bench 2025-26) | In-browser inference **5–10× slower** ⇒ native sidecar for main models; transformers.js for embeddings only. |
| **On-device SLM energy/latency** | 2511.11624 / 2508.11269 | tokens/s, peak memory, **tok/J** ⇒ metrics for our efficiency Pareto. |
| **Small agentic bases (2025)** | (KDnuggets) | Qwen3-4B-2507, SmolLM3-3B, Phi-4-mini, Gemma-3 ⇒ candidate bases beyond Qwen2.5/Llama-3.2. |

**Gap we fill:** no agent model targets a **Chrome-extension DOM/AX-tree action space** on-device; the **DPO/ORPO/SimPO/KTO** comparison on binary on-device agent/RAG failures is missing; **on-device failure-mining from real user sessions** is unexplored.

---

## C. Local / in-browser RAG & calibrated refusal (Track 2 core)

| Work | ID / venue | Why it matters |
|---|---|---|
| **Trust-Align / Trust-Score** | 2409.11242 (ICLR'25) | **Near-exact recipe:** 19K DPO pairs; Trust-Score = mean(refusal-F1, answer-correctness-F1, NLI-citation-F1); LLaMA-3-8B refusal F1 **+24–48%**; works on Qwen-2.5, Phi-3.5-mini. Our Track-2 blueprint + metric. |
| **RGB / CRAG / AbstentionBench** | 2309.01431 (AAAI'24) / 2406.04744 (NeurIPS'24) / 2506.09038 | RAG **fails to abstain**; CRAG 16–25% hallucination; AbstentionBench's 6 types (incl. **Stale**, **False-premise**) ⇒ re-instantiate over browsing history for **Personal-Memory-RGB**. |
| **RefusalBench** | 2510.10390 | Benchmarks the **answer-vs-abstain** decision + calibration for grounded LLMs ⇒ Track-2 eval target. |
| **RAGTruth / LettuceDetect / SelfCheckGPT** | 2502.17125 (+RAGTruth) | Span-level hallucination detection; 18K annotated ⇒ negatives + detection baseline. |
| **FaithBench** | 2410.13210 (NAACL'25) | Detectors ~50% acc ⇒ faithfulness detection is **open**; don't over-claim. |
| **Semantic Entropy / SEPs** | Nature 2024 / 2406.15927 | Label-free hallucination signal; **single-pass probes** ⇒ our **on-device refusal gate**. |
| **"Do RAG LMs Know When They Don't Know?"** | 2509.01476 | RGB+ECE show over-commitment; **conformal abstention** with guarantees. |
| **ALCE** | 2305.14627 | Citation **precision/recall** for attributed generation ⇒ our inline-citation metric. |
| **AttributionBench / CiteEval / CiteME** | (2024-26) | Attribution judging tops ~80% F1 ⇒ report citation accuracy with CIs. |
| **RAGAS / ARES / TruLens** | (frameworks) | Faithfulness, answer relevancy, context precision/recall ⇒ Track-2 metric quartet (computed with a **local** judge for privacy). |
| **In-browser stack** | (Supabase/PGlite; Nomic Matryoshka; rerankers-2026) | PGlite+pgvector HNSW (<20 ms, >95% recall); **Matryoshka** 128–256-d index; hybrid+RRF+**bge-reranker-v2-m3** (+17–39% Recall@5) ⇒ our memory subsystem. |
| **SQuAD 2.0 / RealTimeQA** | 1806.03822 / (RealTimeQA) | Unanswerable + stale seeds for refusal data. |

**Gap we fill:** no work applies Trust-Align-style calibrated grounding to **personal, timestamped, deduplicated browsing memory**; **staleness-aware refusal** via per-page timestamps is unaddressed; no benchmark jointly reports refusal + citation + faithfulness over browsing history.

---

## D. Agent safety, injection, human-in-the-loop, calibration-for-actions

| Work | ID / venue | Why it matters |
|---|---|---|
| **KnowNo ("Robots That Ask For Help")** | 2307.01928 (CoRL'23) | Canonical **conformal when-to-ask**: multiple-choice next actions, calibrated threshold, formal coverage guarantee ⇒ port from robots to **browser action deferral** (our C2). |
| **UQ for Computer-Use Agents** | 2606.25760 (2026) | Action prediction is **badly miscalibrated**, but abstention helps; conformal gives valid bounds ⇒ confirms the gap our small-model deferral fills. |
| **WebGuard** | 2507.14293 | **SAFE/CAUTION/UNSAFE** pre-execution risk + confirmation gating; frontier models unreliable unaided ⇒ our on-device **risk head** + labeled data. |
| **ST-WebAgentBench** | 2410.06703 (ICLR'26, IBM) | 6 safety dimensions + **Completion-under-Policy (CuP)** + Risk-Ratio; **consent is the weakest** ⇒ our action-safety eval frame + benchmark split. |
| **AgentDojo** | (NeurIPS'24, ETH) | Standard **IPI attack/defense** testbed (97 tasks, 629 cases) ⇒ measure attack-success vs utility. |
| **WASP / Mind-the-Web / InjecAgent / AgentHarm** | 2504.18575 (NeurIPS'25) / 2506.07153 / ACL'24 / 2410.09024 | Agents start executing injections **16–86%**; task-aligned injection **>80%**; exfiltration category = our privacy risk; frontier models alarmingly compliant ⇒ our safety evals + refusal policy for the cloud planner. |
| **CaMeL** | 2503.18813 (DeepMind) | **Dual-LLM capabilities** isolation secure even if the model is compromised ⇒ our privileged(cloud)/quarantined(on-device) split. |
| **Spotlighting** | (Microsoft, 2024) | Datamarking/delimiting/encoding cuts IPI **>50% → <2%** ⇒ mark all page text untrusted. |
| **Instruction Hierarchy** | (OpenAI) | Trusted vs untrusted instruction ranking ⇒ page text can't override the user goal. |
| **Magentic-UI** | 2507.22358 (Microsoft) | Two-stage (heuristic + LLM-judge) **action-guard** for irreversible actions ⇒ our confirmation UX. |
| **Attacking VLM Agents via Pop-ups / AdvAgent** | 2411.02391 / 2410.17401 | ~86% attack success via injected UI ⇒ DOM sanitizer + "unexpected UI = deferral trigger." |
| **Adaptive Attacks Break IPI Defenses** | 2503.00061 | Adapting to a known defense bypasses it ⇒ evaluate under **adaptive** attack; frame deferral as **defense-in-depth fail-safe**, not a solution. |
| **Brave Comet disclosures** | (brave.com, 2025-26) | Real email/OTP exfiltration + screenshot injection ⇒ the motivating failures of the whole category. |
| **RAG security survey / OWASP** | 2606.25533 | Embedding inversion, index tampering, side channels ⇒ our local-index threat table. |
| **Chrome MV3 security** | (developer.chrome.com) | MV3 protects against *compromised*, not *malicious*, extensions ⇒ trust via on-device + auditability + minimal permissions. |

**Gap we fill:** **calibrated safe-action deferral on a small on-device model** (KnowNo=robots, WebGuard=frontier, UQ=benchmark-only); **cross-session stored injection** via a personal RAG index is undefended anywhere; a **CaMeL-style split inside a Chrome MV3 extension** with small local models is untried.

---

## E. Evaluation methodology & venues

| Work / venue | ID / link | Why it matters |
|---|---|---|
| **"An Illusion of Progress?" (WebJudge)** | 2504.01382 (COLM'25) | Prior web-agent benchmarks overstate progress; introduces **WebJudge** + Online-Mind2Web difficulty tiers ⇒ our primary live eval + auto-judge. |
| **LLM Agent Evaluation Survey** | 2507.21504 (2025) | Full metric taxonomy: SR, Step-SR, Progress Rate, Node/Edge-F1, **TTFT/latency/tokens**, **pass@k/pass^k** ⇒ our metric stack. |
| **AGENTREWARDBENCH** | 2504.08942 | Evaluates the **auto-evaluators** ⇒ validate our local WebJudge vs humans (E11). |
| **RAGAS / ALCE / Two-Axes-of-Abstention** | (RAGAS) / 2305.14627 / 2607.08456 | Grounded-QA + citation + **selective-prediction** methodology (abstention AUROC: 0.54–0.67 output-conf vs **0.97–0.99 hidden-state**). |
| **ACL Responsible NLP Checklist / ARR** | aclrollingreview.org | Enforced reproducibility/ethics gate (desk-reject since Dec 2024) ⇒ satisfy from the start. |
| **NeurIPS Datasets & Benchmarks Track** | neurips.cc CFP | Archival home for **Personal-Memory-RGB** (target the reachable **2027** cycle). |
| **IEEE Access** | (JIF ~4.2, rolling) | Guaranteed archival graduation deliverable; correctness-graded, fast OA. |
| **IEEE COMPSAC / Big Data** | ieeecompsac / bigdataieee | System paper / RAG-subsystem paper (check live CFPs for reachable cycles). |
| **SLM-Agents Workshop (NeurIPS'26)** | slmw2026.github.io | Near-exact topical fit but **Aug-29-2026 deadline is unreachable** from now; watch for a 2027 edition. |
| **TrustNLP (ACL'26/'27)** | trustnlpworkshop.github.io | Calibrated-refusal/trustworthy-agent fit; 2026 deadline tight, target 2027. |

**Gap we fill:** no benchmark for **grounded QA + calibrated refusal over a user's own browsing history**; almost no web-agent benchmark reports the **accuracy-vs-cost/latency/energy Pareto for on-device** grounding; a **local** (privacy-preserving) auto-judge is unexplored.

---

## F. The inspiration project (for honest positioning)

- **Second Brain** (repo `secondbrain.md` + PDF): passive local RAG-over-history extension; small model SFT+DPO for grounded QA + calibrated refusal; WXT, transformers.js (all-MiniLM-L6-v2), PGlite+pgvector, SimHash, hybrid retrieval. **We cite it as the memory-subsystem inspiration and differentiate:** Groundwork adds **active agentic control**, a **second fine-tuning track (action grounding)**, the **unified calibrated-grounding** framing, **rigorous evaluation** (citation P/R, risk-coverage curves, DPO ablations, multi-run variance), and a **released benchmark** — none of which a passive hobby project provides.

---

## How to use this file when writing the paper

1. **Related Work grid:** four columns = A (action grounding) · C (grounded-QA refusal) · D (agent safety) · B/E (on-device + eval). Put Groundwork in a row that ticks all four — the visual argument for novelty.
2. **Every product differentiation claim** in [01](01_PRODUCT_PLAN.md) must trace to a row here (keeps marketing honest).
3. **Every baseline** in [03 §6](03_RESEARCH_PAPER_PLAN.md) must be a citation here (keeps the paper honest).
4. **Verify IDs/dates/venues** against primary sources before submission — some were gathered rapidly; a few 2026 dates/deadlines are already past relative to an Aug-2026 start.
