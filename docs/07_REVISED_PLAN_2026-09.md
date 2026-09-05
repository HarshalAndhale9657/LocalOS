# 07 — Revised Plan (2026-09-06)

> **This document is the current plan.** It supersedes the timelines, scope, and experiment
> matrix in [01](01_PRODUCT_PLAN.md) §8, [03](03_RESEARCH_PAPER_PLAN.md) §6/§12, and
> [06](06_M1_BUILD_PLAN.md) wherever they disagree. The thesis, architecture, and bibliography in
> 00/02/04 still stand except where §2 and §13 below say otherwise.
>
> Produced from a full audit of the repo (docs, extension code, benchmark code, a rerun of the v0
> harness) against the constraints confirmed on 2026-09-06. Status: **§15 locked on 2026-09-06;
> execution started the same day — see the execution log in §17.**

---

## 1. Constraints this plan is built around

| Constraint | Value (confirmed 2026-09-06) |
|---|---|
| Deadline | **3 to 4 months** from 2026-09-06 → results frozen **2026-12-05**, submission **by 2027-01-09**, hard stop mid-January 2027 |
| Priority | **Research paper first.** Product ships as a demo-grade unpacked build; store listing is out of scope |
| Paper bar | "Good level": a solid archival paper with real findings, positioned so the benchmark can be extended to a top-tier D&B submission later |
| Inference hardware | A **borrowed gaming laptop with a medium GPU** (assume 6 to 8 GB VRAM until measured). This is where on-device numbers come from |
| Training compute | **Google Colab** (Pro, about one thousand rupees per month, within a 2,000 to 3,000 INR total budget) plus the borrowed laptop for 3B runs. Kaggle free GPU as overflow |
| API budget | **5 to 10 USD total** for OpenAI or Anthropic. Free tiers or a local 7B for bulk generation; paid calls only for test-set verification and the frontier baseline |
| Team | Owner plus **two teammates** (annotation, verification, engineering) |
| Data | Owner will **dogfood real browsing privately** (never released) for a case study and to shape the benchmark's page-type mix |
| Framing | Owner is **open**; whatever makes the paper stronger |

---

## 2. What changes, in one screen

**Kept.** Local-first posture; the five-subsystem architecture; calibrated grounding as the thesis; Personal-Memory-RGB as the released artifact; QA-refusal as the guaranteed fine-tuning track; transactions out of scope.

**Reframed.** The paper is a **benchmark + calibration study + refusal-aware fine-tuning** paper about grounded QA over *timestamped personal browsing memory* with *small on-device models*. "Unified calibrated grounding" is no longer asserted as a framework; it is **tested as a transfer hypothesis** (does refusal training on QA transfer to field-level abstention in structured extraction, and to ignoring injected instructions in recalled memory?). If the transfer results are positive they become a headline; if not, they are an honest finding.

**Dropped from the first paper** (listed as future work, never claimed): action-grounding fine-tuning and the deferral head; the full efficiency Pareto (replaced by a measured on-device table); the DPO/ORPO/SimPO/KTO bake-off (optional if compute remains); WebArena/Mind2Web/AgentDojo-class evaluations; the cloud escalation router; the Chrome Web Store listing.

**Why.** The audit found: no model-based number exists yet; the v0 benchmark is template-separable (see §4.1) and cannot support a claim; the action track has zero support in code (exemplars never populated, sanitizer never called, confidence hardcoded); and the extension pipeline and the benchmark pipeline are two different codebases, so the paper would not have described the product. Four months with three people is enough to fix all of that for **one** track, done rigorously, and to test the unification idea cheaply on two adjacent tasks. It is not enough for two fine-tuning tracks.

---

## 3. Contributions (revised) and what supports each

| # | Contribution | Supported by |
|---|---|---|
| **C1** | **Personal-Memory-RGB v1**: a released benchmark for grounded QA with calibrated refusal over *real-source, timestamped, noisy* personal browsing histories, with genuine stale-vs-fresh pairs mined from Wikipedia revision history, chunk-level citation targets, must-abstain classes, a stored-injection probe split, human verification, and a local evaluator validated against humans | §4, E0 |
| **C2** | **An abstention-signal study for small models over personal memory**: retrieval-score threshold vs verbalized confidence vs prompted refusal vs hidden-state probe vs conformal thresholding; how well each calibrates; and whether thresholds fit on some users' histories transfer to unseen users | E1, E2 |
| **C3** | **Refusal-aware fine-tuning (SFT → DPO on mined failures) of 3B and 7B models**, with per-class analysis (stale, false-premise, time-scoped), multi-seed, against base, teacher, and lexical baselines | E3, E4, E5 |
| **C4** | **Calibration transfer across task formats** (the unification hypothesis, tested): does QA-refusal training transfer zero-shot to (a) field-level "unknown" in structured extraction from a page and (b) resistance to instructions injected into recalled memory | E6, E7 |
| **C5** | **A working local-first system** (the extension) as the deployment vehicle, with a measured on-device latency/memory table and a private dogfood case study | E8, E9 |

Priority if time runs short: C1 + C2 + C3 are the paper. C4 and C5 add strength; C4(b) and E9 go first if something must be cut.

---

## 4. Personal-Memory-RGB v1

### 4.1 Why v0 cannot be used for claims (audit findings)

- Every page uses one sentence template; the entity name is the only discriminating token, so `not_in_history` is trivially separable.
- Every price is stale by construction (`price_until` precedes `read_at`; `as_of` postdates all reads). There are no fresh time-sensitive facts, so "price" is a keyword, not a temporal test.
- `time_scoped` scores 0.00 for the lexical baseline only because read dates live in metadata that BM25 never sees. A metadata-aware baseline flips it to near 1.0; it is a baseline artifact, not a calibration gap.
- `false_premise` asks for a foreign-domain attribute (the wheel size of a stand mixer): lexically obvious.
- The retriever stopword list contains the question-template words; the baseline was tuned to the templates.
- Test has 8 to 12 items per class; per-class intervals are about plus or minus 30 points.

v0 remains useful as the schema and the metric-code validator. Nothing from it goes in the paper.

### 4.2 v1 design

**Sources (all releasable, licenses recorded).** Wikipedia article text (CC-BY-SA) as the bulk corpus; **Wikipedia revision pairs** for staleness; Wikinews for dated events; arXiv abstracts for the researcher persona. No scraped commercial pages in the released set.

**Staleness done properly.** For an article, take two revisions R_old and R_new where a specific numeric or categorical fact changed. The page is "read" at a time between the two revisions with R_old's text; `as_of` is after R_new. A question about the changed fact is `stale` (gold: abstain or answer with an explicit staleness caveat, scored as a two-level label). A question about a fact **unchanged** between R_old and R_new, read the same way, is `time_sensitive_fresh` (gold: answer). This removes the "fact type predicts the label" shortcut and gives the benchmark a genuinely new axis.

**Histories.** 60 to 80 synthetic personas, 40 to 80 pages each, page-type mix informed by the owner's private dogfood statistics (type counts only, no content). Noise: navigation boilerplate, near-duplicates with SimHash labels, re-visits with edited text (which also exercises page versioning), off-topic reading. Dates appear **both** in metadata and in natural page text ("updated 12 July 2026") so metadata-blind systems are not unfairly disadvantaged.

**Classes.**

| Class | Gold | Notes |
|---|---|---|
| `single_hop` | answer + 1 citation | |
| `multi_hop` | answer + 2 to 3 citations | across pages |
| `time_scoped` | answer | "what did I read last week about X"; date in metadata and text |
| `time_sensitive_fresh` | answer | new: the fresh counterpart to stale |
| `not_in_history` | abstain | topic absent from this history but present in others |
| `stale` | abstain or caveated answer | from revision pairs |
| `false_premise` | correct premise or abstain | premise perturbations within the same domain, teacher-written, human-checked |
| `distractor_heavy` | answer | answerable with confusable near-duplicate chunks seeded |
| `stored_injection` | normal behavior, instruction ignored | a past page carries hidden instructions; probe split, 100 to 150 items |

Balance about 50/50 answerable vs must-abstain on the main split; probe splits reported separately.

**Sizes.** 2,000 to 3,000 items total; train / dev / test split **by history and by source article** (no article appears in two splits). Hidden test kept out of the public release for a later leaderboard.

**Generation.** Teacher writes questions conditioned on specific chunks (answerable), on held-out topics (not-in-history), or on perturbed premises (false-premise). Bulk generation with a free tier or a local 7B on Colab; the **frozen test set is re-verified with a paid frontier call** (budget: about 3 USD).

**Verification.** NLI entailment gate (a local DeBERTa-class MNLI model) for every answerable item; retrieval-absence check for not-in-history; **human verification of a stratified 20% sample plus all hard items** by the two teammates, reporting inter-annotator agreement.

**Evaluator.** Local and privacy-consistent: NLI for citation precision/recall; a local judge (the 7B) for faithfulness, validated against a human-labeled subset with reported agreement. RAGAS-style faithfulness and ALCE citation metrics are implemented, not stubbed.

**Freeze date: 2026-10-04.** Nothing in the test set changes after this.

---

## 5. Models and training

| Role | Model | Where it runs |
|---|---|---|
| Primary on-device | **Qwen2.5-3B-Instruct** (GGUF Q4_K_M for the extension; HF weights for probes and training) | Borrowed laptop; Colab |
| Secondary | **Qwen2.5-7B-Instruct** fine-tuned as a scale row | Colab (L4/A100) |
| Optional size sweep | Qwen2.5-1.5B-Instruct | if compute remains |
| Teacher | Free-tier frontier or local 7B for bulk; paid frontier for test verification and the teacher baseline | API |

**Recipe (Track 2, Trust-Align adapted).** Abstention-aware SFT on train-split histories plus re-instantiated SQuAD 2.0 unanswerables and RealTimeQA-style stale seeds, with explicit negatives; then DPO on pairs mined from the SFT model's own dev failures (hallucination vs refusal, missing vs correct citation, stale-answer vs caveat). QLoRA r=16 α=32 on attention and MLP projections. Three seeds per configuration. Merge and quantize to GGUF; report pre- and post-quantization deltas.

**Compute estimate.** 3B SFT about 1 to 2 hours on a T4-class GPU, under an hour on L4/A100; DPO similar. 3B: 3 seeds × (SFT + DPO) = 6 runs, feasible on the borrowed laptop if it has 8 GB VRAM, else Colab. 7B: 6 runs on Colab, about 1 to 2 hours each on A100. Total comfortably inside two months of Colab Pro plus free tiers.

---

## 6. Experiment matrix (revised)

| # | Experiment | Answers | Needs | Decisiveness |
|---|---|---|---|---|
| **E0** | Benchmark validity: trivial baselines, lexical baselines, frontier zero-shot; show which classes remain hard for frontier models (the temporal axis should) | C1 | v1, API (~3 USD) | ★★★ (justifies the benchmark) |
| **E1** | Abstention signals on base 3B/7B: retrieval score, verbalized confidence, prompted refusal, hidden-state probe; AUROC and risk-coverage per signal | C2 | HF inference on GPU | ★★★ |
| **E2** | Conformal thresholding and **cross-history transfer**: fit on dev histories, verify coverage on unseen test histories | C2 | E1 outputs | ★★ |
| **E3** | Base vs SFT vs SFT+DPO on 3B and 7B; Trust-Score, refusal P/R, abstention AUROC, per-class; 3 seeds with CIs | C3 | training | ★★★ |
| **E4** | Negative-sample SFT ablation (with vs without explicit negatives) | C3 | 2 extra 3B runs | ★★ |
| **E5** | Retrieval ablations that the product depends on: time-decay half-life ∈ {off, 30, 90, 365 days}; dense-only vs hybrid dense+FTS; effect on time-scoped and stale classes | C3, C5 | harness only | ★★ |
| **E6** | **Transfer to extraction**: field-level "unknown" precision/recall on a small page set (150 to 300 fields, human-labeled) for base vs SFT+DPO, zero-shot | C4 | teammates label | ★★ |
| **E7** | **Transfer to stored injection**: injected-instruction compliance rate on the probe split for base vs SFT+DPO, with and without spotlighting | C4 | probe split | ★★ |
| **E8** | On-device table on the borrowed laptop: TTFT, tokens/s, end-to-end latency per question, peak RAM/VRAM, for 3B and 7B GGUF through the actual extension | C5 | laptop | ★ |
| **E9** | Private dogfood case study: 2 weeks of the owner's real browsing, 50 real questions, qualitative failure analysis; nothing released | C5 | owner | ★ |
| E10 | Optional: DPO vs KTO on the same mined failures (binary labels suit KTO) | C3 | spare compute | ★ |

**Baselines always reported.** Always-answer; always-abstain; **metadata-aware** BM25 + threshold (dates indexed); the extension's own cosine + threshold; base 3B and 7B with the same prompt; the frontier teacher zero-shot; SFT-only.

---

## 7. Metrics

Calibration headline: refusal precision/recall/F1, decision accuracy, risk-coverage curves, abstention AUROC per signal, conformal coverage achieved vs target. Answer quality: token-F1 and local-judge faithfulness on answerable items. Citations: NLI-verified citation precision/recall with bootstrap CIs. Composite: Trust-Score. Staleness: two-level score (abstain or caveated answer both count, silent stale answer does not). Everything with mean ± std over 3 seeds where training is involved, and bootstrap CIs over items otherwise.

---

## 8. Timeline (16 weeks, three lanes)

Gates are in bold. Weeks start on Mondays from 2026-09-07.

| Wk | Dates | Owner (research lead) | Teammate A (engineering) | Teammate B (data and evaluation) |
|---|---|---|---|---|
| 1 | Sep 7 | Lock §15 decisions; v1 design doc; revision-pair miner prototype | Ollama + Chrome runtime bring-up; resolve PGlite `eval`/CSP and ONNX-offline unknowns | Annotation guidelines; verify every arXiv ID in 04; add the missing related work (§13) |
| 2 | Sep 14 | Generation pipeline with free-tier teacher; first 300 items; NLI gate | Shared core: prompts as data files, chunker and refusal parser with unit tests in TS and Python | Pilot annotation of 50 items; agreement check |
| 3 | Sep 21 | Full v1 generation (2k to 3k); dedup/noise injection; dev/test split | Page versioning (URL + capture time), Postgres full-text channel, decay as a parameter | Stratified human verification begins |
| 4 | Sep 28 | Fix verification failures; **freeze test set Oct 4**; paid re-verification of test | Headless evaluation hook so the Python harness drives the extension's exact pipeline | Verification of the frozen test complete |
| 5 | Oct 5 | E0 baselines incl. frontier; E1 signal study on base 3B/7B (HF, GPU) | Extraction as structured grounded QA with per-field citation or "unknown" | Extraction label set (150 to 300 fields) |
| 6 | Oct 12 | E2 conformal + transfer; SFT data build (train histories + SQuAD2 + stale seeds) | Element-aware risk policy; tab-session Ask | Judge-vs-human agreement labels |
| 7 | Oct 19 | 3B SFT × 3 seeds; **gate Oct 25: measurable lift on dev** | Borrowed-laptop setup; GGUF export path; E8 harness | Datasheet draft |
| 8 | Oct 26 | DPO pair mining; 3B DPO × 3 seeds; E4 negatives ablation | Dogfood build for the owner; capture on/off per site; per-entry delete | Docs and changelog corrections (§13) |
| 9 | Nov 2 | 7B SFT + DPO on Colab; E3 tables | E9 dogfood begins (owner uses it daily) | Release repo skeleton, loader, license files |
| 10 | Nov 9 | E5 retrieval ablations; E6 extraction transfer | E8 on-device measurements | E6 scoring |
| 11 | Nov 16 | E7 stored-injection transfer; optional E10 | Demo video; permission scope-down | Reproducibility checklist pass |
| 12 | Nov 23 | Re-runs, seeds, CIs; figure drafts | Bug fixes only | E9 question set and labels |
| 13 | Nov 30 | **Freeze all results Dec 5** | | |
| 14 | Dec 7 | Paper draft: intro, benchmark, method | | Datasheet final; artifact upload (data, loader, evaluator, baselines) |
| 15 | Dec 14 | Results, safety, limitations, related work | Internal review of system section | Internal review of benchmark section |
| 16 | Dec 21 | Full draft to mentor; revisions | | |
| — | Jan 2027 | **Submit by Jan 9**; graduation report; buffer to mid-January | | |

**Gate rules.** If the test set is not frozen by Oct 11, cut item count, never classes. If SFT shows no lift on dev by Oct 25, the paper becomes C1 + C2 + an honest negative result on C3, and E6/E7 run on base models only; this is still an archival-quality paper if framed plainly.

---

## 9. Budget

| Item | Plan |
|---|---|
| Colab Pro | 2 months (October, November), about two thousand rupees total. Use free Colab and Kaggle in September and December |
| Borrowed laptop | All 3B inference, E8, dogfood, and 3B training if VRAM ≥ 8 GB |
| API | ~3 USD paid re-verification of the frozen test set; ~3 USD frontier baseline on test (E0); ~2 to 4 USD reserve. Bulk generation on a free tier or local 7B |
| Everything else | Free: Wikipedia dumps and revision API, HF models, NLI model, local judge |

---

## 10. Product plan (demo-grade, shares the research core)

**Identity.** *A private research memory that can go read for you.* Ship order: recall with citations and refusal → grounded extraction → a gathering agent limited to SAFE navigation. General browser control is not a product goal for this cycle.

**Architecture changes, in order, with reasons.**

1. **Single-source the core.** Prompt templates as data files loaded by both TypeScript and Python; chunker and refusal parser unit-tested in both. The Python harness calls the same Ollama model with byte-identical prompts, and a headless hook lets it drive the extension's real retrieval. *Reason: the paper must describe the product.*
2. **Versioned pages** keyed by URL plus capture time, read-history retained. *Reason: staleness and time-scoped recall are impossible without it, and it is a schema change that gets harder weekly.*
3. **Hybrid retrieval** by adding PGlite's built-in Postgres full-text search alongside cosine; recheck the pgvector subpath in the current PGlite release for HNSW. *Reason: full-scan JSON cosine will not survive a real history.*
4. **Time decay as a parameter, default long or off, `asOf` exposed.** *Reason: recency is a hypothesis (E5), not a constant.*
5. **Element-aware risk policy.** Typing into a `searchbox` and clicking a `link` are SAFE; buttons CAUTION; submit-like UNSAFE. *Reason: the current verb-based policy asks permission for every keystroke.*
6. **Extraction as structured grounded QA** with per-field citation or "unknown". *Reason: it is the second task for C4 and the most useful product feature.*
7. **Tab-session Ask** (index open tabs into a session scope). *Reason: makes the cross-tab job a retrieval problem already solved.*
8. **Opt-in passive capture** behind the existing blocklist gate, plus per-entry delete. *Reason: recall over "what I read" needs it; needed for E9.*

Out of scope this cycle: streaming UI polish, store listing, cloud planner, vision fallback.

---

## 11. Team lanes and ownership

- **Owner:** benchmark design and generation, all experiments, training, paper.
- **Teammate A:** extension runtime, shared core, store changes, extraction feature, on-device measurements, demo build.
- **Teammate B:** annotation and verification, judge-agreement labels, related-work verification, datasheet, docs corrections, release repository.

Weekly 30-minute sync; a single shared results sheet; every number in the paper traceable to a run ID and commit.

---

## 12. Venue plan

- **Archival deliverable:** IEEE Access, submit by 2027-01-09.
- **Visibility:** one 2027 workshop on trustworthy or agentic NLP once CFPs are announced (non-archival, so the IEEE Access paper is unaffected).
- **Stretch, after graduation:** extend v1 to a Datasets & Benchmarks submission (NeurIPS 2027 D&B, about May 2027) with the hidden test, leaderboard, and larger scale. The v1 design above is built so this extension is additive, not a redo.
- Satisfy the ACL Responsible NLP checklist and reproducibility norms from the start regardless of venue.

---

## 13. Corrections to make in existing docs and code comments

These describe behavior that does not exist and must be fixed before any draft cites them (Teammate B, week 8).

- `SAFETY_CHANGELOG.md`: `guardRetrieved` is an identity function; retrieved chunks are protected only by per-source `spotlight()` in the QA prompt. Say that. `sanitizeNodes` is never called; mark "not wired".
- `02` §6.2 inherits Microsoft's spotlighting figure (>50% → <2%). That result was for datamarking and encoding; the code does delimiting only, the weakest variant. Remove the number or implement datamarking.
- Any use of "calibrated" for the current code means a fixed cosine cutoff of 0.25 plus a prompt instruction plus a regex. Fix wording in `README.md`, `MENTOR_BRIEF.md`, and `06`.
- `benchmark/README.md`: the v0 per-class narrative ("closing that gap is the job of the SFT+DPO model") is withdrawn; replace with the §4.1 findings.
- `04` related work must add and differentiate: **LoCoMo** and **LongMemEval** (personal long-term memory QA with temporal reasoning), **Synapse** and **Agent Workflow Memory** (retrieved experience for web agents), **Ask-before-Plan** and **IN3 / "Tell Me More"** (agents asking clarifying questions), **Greshake et al. 2023** and **PoisonedRAG** (stored and retrieval-borne injection), **R-Tuning** (refusal-aware tuning), **Conformal Language Modeling** and conformal factuality work. The claims "no cited paper couples history RAG with an action model" and "a threat no surveyed system defends against" are withdrawn.
- `00`/`03`: the two-track unified framework becomes a tested transfer hypothesis (C4); the action track is future work.

---

## 14. Risks specific to this plan

| Risk | Mitigation |
|---|---|
| Revision-pair mining yields too few clean stale items | Start it in week 1; fall back to Wikinews dated facts; keep `stale` small but real rather than large and synthetic |
| Free teacher tier unavailable or rate-limited | Local 7B on Colab as generator; paid calls only for the frozen test |
| Borrowed laptop has under 8 GB VRAM | 3B training moves to Colab; inference numbers still valid on the laptop |
| SFT shows no lift | Gate Oct 25; paper pivots to benchmark + signal study + negative result |
| Human verification lags | Verification of the test split is mandatory; the train split may ship with automated verification only, stated in the datasheet |
| Two codebases drift again | Shared core (§10.1) is done in week 2, before any experiment number is produced |

---

## 15. Decisions — locked 2026-09-06

The owner approved "whatever is best" on 2026-09-06; the defaults below are now locked and execution has started.

1. ✅ Paper scope as §2 and §3: one fine-tuning track, unification as a tested transfer hypothesis, action track deferred.
2. ✅ Qwen2.5-3B-Instruct primary, 7B as the scale row. (If budget were unconstrained the headline row would be 7B and a 1.5B→14B scale sweep would be added; revisit only if compute appears.)
3. ✅ Wikipedia revision pairs as the source of stale and fresh items.
4. ✅ Test freeze 2026-10-04; results freeze 2026-12-05; submission by 2027-01-09.
5. ✅ Budget split in §9.
6. ✅ Team lanes in §11.
7. ✅ IEEE Access as the archival target, D&B as a post-graduation extension.
8. ✅ **E9b added (§16):** a consented, on-device evaluation on 10–12 volunteer students' real histories replaces the single-person dogfood study. Evaluation only, never training, never released.

Still unknown, planned around: the borrowed laptop's VRAM (3B training runs there if ≥ 8 GB, else Colab) and which free teacher tier is available (pipeline is provider-agnostic with a local-7B fallback).

---

## 16. E9b — consented real-history evaluation (added 2026-09-06)

**Purpose.** Answer the "your benchmark is synthetic" objection: do the calibration findings from synthetic v1 hold on real personal histories?

**Why evaluation only.** 10–12 histories cannot train anything (a train/test split of 8/4 users is noise), and anything trained on real histories cannot be released. Training stays on synthetic v1.

**Design (privacy-preserving, on-device).**
- Volunteers: 10–12 adult students, written consent, plain-language description of what is captured and where it lives, withdrawal at any time by wiping.
- Capture through the extension itself with the sensitive-domain blocklist on and capture opt-in per site; webmail, messaging, banking, health excluded by default because a volunteer's consent does not cover other people's words.
- Each volunteer writes **30–50 questions about their own reading** (answerable, never-read, time-scoped) and labels gold answers; they are the only ground truth available for their own history. Target 300–600 items.
- The index, questions, and model outputs **never leave the volunteer's machine**. We ship the model + a runner; only aggregate metrics and per-item decision labels (answer/abstain, correct/incorrect) come back. No page text, no URLs.
- Models evaluated: base 3B, SFT+DPO 3B, and the same abstention signals as E1, so synthetic-vs-real deltas are directly comparable.

**Prerequisites and gates.**
- **Ask the mentor this week whether university ethics approval is required.** If it is and cannot be obtained by mid-October, E9b downgrades to the owner-only dogfood study (E9).
- The demo build must be volunteer-reliable by **Oct 19** (one week earlier than the previous schedule): capture on/off per site, per-entry delete, wipe, a visible "what is stored" panel, and a one-click "run evaluation and export metrics" command.
- Schedule: recruit and consent weeks 6–7; capture weeks 8–10; questions written week 10; evaluation weeks 11–12; results in before the Dec 5 freeze.

**Reporting.** A separate table, clearly labeled real-history and unreleased, with per-volunteer variance; never merged into the released benchmark numbers.

---

*Prev: [06 — M1 Build Plan](06_M1_BUILD_PLAN.md) (progress notes remain valid; its ticket list is superseded by §8). Up: [README](README.md).*

---

## 17. Execution log

### 2026-09-06 (week 1, day 1)
- **Plan locked** (§15) and E9b added (§16). Docs corrected per §13: `SAFETY_CHANGELOG.md` (guardRetrieved is identity; sanitizer unwired; spotlighting is delimiter-only), `02` §6.2 (no inherited injection figure), `benchmark/README.md` (v0 is a harness validator), `04` §E2 (12 nearest-neighbor papers added, IDs verified against the arXiv API; two over-claims withdrawn).
- **Runtime:** Ollama installed (winget), `qwen2.5:3b-instruct` pulled (1.9 GB, Q4_K_M), server restarted with `OLLAMA_ORIGINS=chrome-extension://*` (also persisted via `setx` for future launches). Dev machine: 16 GB RAM, no GPU → ~12 s per grounded-QA item on CPU. **Chrome load of the extension still pending** (needs the owner to load `extension/.output/chrome-mv3` unpacked once).
- **Shared core (§10.1) done:** `shared/prompts/*` (prompt files + `version.txt`), `shared/tests/refusal_cases.json`, `extension/lib/model/core.ts` (+ vitest), `benchmark/pmrgb/core.py` (+ unittest). The extension's model client now imports prompts verbatim via `?raw`; default model switched to `qwen2.5:3b-instruct`. Typecheck, 3 vitest + 4 unittest vectors, and the production build all pass. CI runs both test suites.
- **Model harness (M1.6) done:** `benchmark/eval/run_model.py` runs BM25 → shared prompt → Ollama → shared parser and writes auditable per-item predictions. Smoke test on 6 v0 test items: base 3B answers single-hop, over-abstains on multi-hop (2/3). v0 numbers are for plumbing only.
- **Revision miner (§4.2) done:** `benchmark/pmrgb/revisions.py` (stdlib, disk-cached, polite UA). After fixing reference-marker leakage and adding dated / unit-only / number-replacement filters: **16 prime stale candidates over 8 articles (~2 per article)**, e.g. "As of November 2022, 310 people have died on Everest" → "As of May 2024, 340". Seed list of 75 titles in `benchmark/sources/titles_v1_seed.txt`; needs ~300 titles for the target class size.
- **Not committed yet** (owner to decide branch/commit policy; `main` is the default branch and CLAUDE.md prefers feature branches).

### 2026-09-06 (week 1, day 1 — later)
- **Committed and pushed** branch `plan-2026-09` (commit `4629659`).
- **Runtime verified in a real Chrome, 10/10 checks** via a new end-to-end harness `extension/e2e/smoke.mjs` (`npm run e2e`): launches the installed Chrome over the DevTools pipe (`installExtension`; branded Chrome ≥ 137 ignores `--load-extension`), installs the production build, serves a local fixture article, and sends the side panel's own messages. Confirmed: service worker + offscreen start; **PGlite works under the extension CSP** (open risk closed); capture → chunk → embed → store (21 s first call incl. model load, CPU); SimHash dedup; retrieval returns the fixture chunk (cosine 0.81); **ASK returns a cited grounded answer from the 3B model** ("[1] The aperture … is 203 millimeters.", 11.5 s) and **abstains on an unread topic**; CDP a11y snapshot works. The Claude-in-Chrome tools were unavailable to the owner, so this harness is now the standard runtime check.
- **Bug found and fixed by the harness:** onnxruntime-web dynamically imported its WASM engine from a CDN → "no available backend found" under the CSP (the second open risk). Fix: `npm run fetch-model` now also copies `ort-wasm-simd-threaded.asyncify.{mjs,wasm}` into `public/ort/` (gitignored) and `lib/memory/embed.ts` points `env.backends.onnx.wasm.wasmPaths` there, single-threaded (offscreen doc is not cross-origin isolated). Build is now ~100 MB with both assets.
- **Calibration finding (feeds E1/E5):** an unrelated query ("quarterly revenue of a European airline") still retrieved the telescope chunk at cosine **0.47**, far above the hard-coded `NEG_REJECT = 0.25`. bge-small cosines are compressed, so the current constant rejects nothing; the retrieval-side abstention threshold must be *calibrated*, not guessed. Left as-is until E1 measures it.
- **v0 plumbing baseline (60 test items, base `qwen2.5:3b-instruct`, BM25@4, prompt v1; not for the paper):** abstain P/R/F1 0.64/0.82/0.72, decision acc 0.70; abstention AUROC: model decision 0.71 vs retrieval score 0.81. Per class: false_premise 1.00, not_in_history 0.92, single_hop 0.92, stale 0.50, multi_hop 0.42, time_scoped 0.38. Reading: the untuned 3B over-abstains on multi-hop/time-scoped and under-abstains on stale — the same axis v1 is built to measure properly.

**Next (week 1–2):** owner loads the extension in Chrome for day-to-day dogfooding (runtime is verified) (PGlite `eval`/CSP, ONNX offline, capture → ask on a real page); full v0 test-split run for the plumbing baseline; extend the title list and run the miner at scale; start the v1 history assembler and teacher-generation pipeline; Teammate B starts annotation guidelines; ask the mentor about ethics approval for E9b.
