# 08 — Learning Roadmap (owner)

> Goal: be able to **defend** this work, not just describe it. Written 2026-09-06 against the plan
> in [`07`](07_REVISED_PLAN_2026-09.md) (16 weeks, one fine-tuning track, calibrated refusal over
> personal browsing memory).
>
> **Every arXiv ID below was checked against the live arXiv API on 2026-09-06** — titles and years
> are real. Books, courses and blogs are given as **channel + exact title** rather than URLs,
> because a guessed URL is worse than none; search the title and you will land on it. Domains are
> given only where they are stable and I am certain of them.

---

## 0. What "confident" actually means here

You will not be judged on knowing everything. You will be judged on whether you can hold three
lines under pressure:

1. **Why the problem is real.** A personal-memory assistant that answers confidently from a page
   you read two years ago is *worse than useless* — it is confidently wrong about your own life.
   Nobody measures this today.
2. **Why your method is the right one.** Why abstention rather than better retrieval; why a small
   local model; why SFT→DPO; why a benchmark instead of only a system.
3. **What your numbers mean and — louder — what they do not.** The examiner who catches you
   overstating a result will remember only that. The one who watches you volunteer a limitation
   before they find it will trust everything else you said.

Everything below serves those three lines. **If a topic does not serve one of them, skip it.**

---

## 1. The fast path (if you only ever get ~20 hours)

Do these seven things, in this order, and you can already defend the project competently:

| # | Do this | Time |
|---|---|---|
| 1 | Karpathy, **"[1hr Talk] Intro to Large Language Models"** (YouTube) | 1 h |
| 2 | **QLoRA** (2305.14314) + **LoRA** (2106.09685) — read intro, method, and the figures | 3 h |
| 3 | **DPO** (2305.18290) — understand the loss and why no reward model is needed | 3 h |
| 4 | **Know Your Limits: A Survey of Abstention in LLMs** (2407.18418) — your field's map | 4 h |
| 5 | **Trust-Align** (2409.11242) — the closest recipe to what you are doing | 3 h |
| 6 | **ALCE** (2305.14627) + **RAGAS** (2309.15217) — how grounded answers get scored | 3 h |
| 7 | Write the **mock-viva answers in §8** in your own words, out loud | 3 h |

Everything after this section is the full version.

---

## 2. Phase A — Foundations (weeks 1–3, ~15 h)

You need these to not stumble on basics, not to become an expert.

### A1. Transformers and what an LLM actually does
*The exam question: "Explain what your model is doing when it answers."*

- **3Blue1Brown** — "But what is a GPT? Visual intro to transformers" and "Attention in transformers,
  step by step" (YouTube). The best intuition-per-minute on the internet. **~1 h**
- **Jay Alammar — "The Illustrated Transformer"** (blog). Read once. **~1 h**
- **Karpathy — "Let's build GPT: from scratch, in code, spelled out"** (YouTube, part of the
  *Neural Networks: Zero to Hero* playlist). Watch and type along; this is the single highest-value
  4 hours in ML education. **~4 h**
- Reference when stuck: **Jurafsky & Martin, *Speech and Language Processing*, 3rd edition draft**
  (free at `web.stanford.edu/~jurafsky/slp3/`). Chapters on transformers and on RAG. **dip in**

*Skip:* training a model from scratch, tokenizer internals, positional-encoding variants.

### A2. Why small models, and what quantization costs you
*The exam question: "Why 3B? Isn't this just a worse GPT-4?"*

- **Chinchilla** (2203.15556) — read only the scaling-law result. You need the vocabulary of
  compute-optimal training to explain why small models improved so much. **~1 h**
- **Qwen2.5 Technical Report** (2412.15115) — your actual base model. Know its size, context
  window, and training claims. You will be asked "why Qwen?" **~1 h**
- **Maarten Grootendorst — "A Visual Guide to Quantization"** (blog). Explains 4-bit, GGUF,
  and what Q4_K_M means. You ship Q4_K_M; you must be able to say what it does. **~1 h**
- **LIMA** (2305.11206) — evidence that a few thousand good examples beat a mountain of bad ones.
  Your justification for a small, carefully-gated training set. **~1 h**

### A3. Retrieval-augmented generation
*The exam question: "Where does retrieval end and the model begin?"*

- **RAG** (2005.11401) and **REALM** (2002.08909) — the two founding papers. Read RAG properly,
  skim REALM. **~2 h**
- **Sentence-BERT** (1908.10084) — why an embedding is comparable by cosine at all. **~1 h**
- **C-Pack / BGE** (2309.07597) — the family your embedding model comes from. Skim. **~30 m**
- **Matryoshka Representation Learning** (2205.13147) — why you can truncate an embedding to
  128 dims and keep most of the quality. Relevant to your index-size story. **~1 h**
- **Self-RAG** (2310.11511) — a model deciding *when* to retrieve and critiquing its own output.
  Closest neighbour to "the model decides whether it can answer". **~2 h**

---

## 3. Phase B — Your actual contribution: abstention and calibration (weeks 3–7, ~30 h)

**This is the part you must know better than your examiners.** Everything else you can be merely
competent at. Budget the most time here.

### B1. Selective prediction — the framing
*The exam question: "What exactly is the quantity you are optimising?"*

- **Selective Classification for Deep Neural Networks** (1705.08500) — the risk–coverage
  formulation your curves come from. Read the setup carefully; this is the mathematical spine of
  your whole thesis. **~3 h**
- **Know Your Limits: A Survey of Abstention in LLMs** (2407.18418) — read *twice*, and build your
  related-work grid from its taxonomy. This single paper positions your work. **~5 h**
- **AbstentionBench** (2506.09038) — the current benchmark landscape for unanswerable questions;
  your "why another benchmark?" answer must engage with it. **~2 h**

### B2. Calibration — the measurement
*The exam question: "AUROC of 0.8 — of what, against what, and is that good?"*

- **On Calibration of Modern Neural Networks** (1706.04599) — ECE, reliability diagrams, why
  modern networks are overconfident. Short and foundational. **~2 h**
- **Teaching Models to Express Their Uncertainty in Words** (2205.14334) — verbalised confidence,
  one of the signals in your study. **~2 h**
- **Just Ask for Calibration** (2305.14975) — practical elicitation of calibrated confidence from
  an LLM; directly informs your prompt-based signal. **~2 h**
- **Semantic Entropy Probes** (2406.15927) — the cheap single-pass hidden-state signal. This is
  your hidden-state probe baseline; know how it is trained and why it beats output confidence.
  **~3 h**
- **SelfCheckGPT** (2303.08896) — sampling-based hallucination detection; the expensive
  alternative you are *not* using, and you should be able to say why (latency on-device). **~2 h**

### B3. Conformal prediction — the guarantee
*The exam question: "You say 'guarantee'. Guaranteed under what assumption?"*

The honest answer is **exchangeability**, and an examiner who knows the area will ask. Know that
your calibration and test data must be exchangeable, and that per-user deployment probably
violates it — which is exactly why your cross-history transfer experiment matters.

- **A Gentle Introduction to Conformal Prediction** (2107.07511, Angelopoulos & Bates) — read
  chapters 1–3. There is also an excellent companion video by the authors; search
  "Angelopoulos conformal prediction tutorial". **~4 h**
- **Conformal Language Modeling** (2306.10193) and **Language Models with Conformal Factuality
  Guarantees** (2402.10978) — conformal applied to generation. **~3 h**
- **KnowNo: Robots That Ask For Help** (2307.01928) — conformal "when to ask" in an agent setting;
  the paper your deferred action track was built on, and still worth citing. **~2 h**
- GitHub: **"Awesome Conformal Prediction"** — a curated index for when you need more. *(reference)*

### B4. Refusal-aware training — the method you are implementing
*The exam question: "How is your fine-tuning different from just prompting 'say I don't know'?"*

- **R-Tuning: Instructing LLMs to Say 'I Don't Know'** (2311.09677) — the direct ancestor of your
  SFT stage. **~3 h**
- **Trust-Align** (2409.11242) — read this one closely; you are adapting its recipe to a new
  domain, and your method section will be compared to it line by line. Know its Trust-Score
  definition exactly. **~4 h**
- **SQuAD 2.0** (1806.03822) — where "unanswerable" as a training signal comes from; you reuse it
  as seed data. **~1 h**

### B5. Staleness and time — your novel axis
*The exam question: "Isn't stale just a special case of unanswerable?"*

Your answer: no — the evidence *is* in the index, it is well-retrieved, and it is confidently
wrong. Retrieval-score abstention cannot catch it by construction. That is the gap.

- **FreshLLMs / FreshQA** (2310.03214) — the closest prior work on time-sensitive QA. **You must
  cite and differentiate this**: FreshQA is about a model's world knowledge going stale against
  live search; yours is about *a specific document the user read* going stale in their own memory.
  **~2 h**
- **RealTime QA** (2207.13332) — time-sensitive QA with a moving answer key. **~1 h**
- **LoCoMo** (2402.17753) and **LongMemEval** (2410.10813) — the two nearest personal-memory
  benchmarks. Know their task taxonomies well enough to state, in one sentence each, what yours
  does that they do not. **~3 h**

---

## 4. Phase C — Fine-tuning craft (weeks 6–10, ~25 h)

### C1. Parameter-efficient fine-tuning
- **LoRA** (2106.09685) — understand the rank decomposition and *why* it works. Be ready to
  explain your r and α choices. **~2 h**
- **QLoRA** (2305.14314) — 4-bit NF4, double quantization, paged optimizers. This is how you fit
  training into Colab; expect a question on what precision is actually being trained. **~3 h**
- **Hugging Face PEFT documentation** and the **Unsloth** repo + its Colab notebooks
  (`github.com/unslothai/unsloth`). Run one notebook end-to-end before you touch your own data.
  **~4 h**

### C2. Preference optimisation
- **InstructGPT** (2203.02155) — the RLHF baseline everything is measured against. Read the
  three-stage figure and the results. **~2 h**
- **DPO** (2305.18290) — the core. Derive, or at least follow, why the reward model collapses into
  the policy. Expect "why not PPO?" **~4 h**
- **KTO** (2402.01306) — unpaired binary labels, which is the natural shape of your data
  (an answer is grounded or it is not). Strong candidate for your ablation. **~2 h**
- **ORPO** (2403.07691) and **SimPO** (2405.14734) — skim; know that reference-free variants exist
  and cost less memory. **~1 h**
- **Nathan Lambert — the RLHF Book** (`rlhfbook.com`) — the best single explainer of this whole
  family. Read the DPO and evaluation chapters. **~4 h**
- **Hugging Face TRL documentation** + the **alignment-handbook** repo — the code you will
  actually run. **~3 h**

### C3. Practical training
- **Sebastian Raschka** — blog (`magazine.sebastianraschka.com`) and the book *Build a Large
  Language Model (From Scratch)*. His LoRA/DPO articles are the clearest applied writing available.
  **~ongoing**
- Learn to read a **loss curve** and to spot overfitting on a 1k-example set. You have three seeds
  and a small dataset; you will see variance and must not over-read it.

---

## 5. Phase D — Evaluation, statistics and writing (weeks 10–16, ~25 h)

### D1. Grounded-answer metrics
- **ALCE** (2305.14627) — citation precision and recall via entailment. You implement this. **~3 h**
- **RAGAS** (2309.15217) + the RAGAS documentation (`docs.ragas.io`) — faithfulness, answer
  relevancy, context precision/recall. **~3 h**
- **RGB** (2309.01431) and **CRAG** (2406.04744) — the RAG benchmarks whose "negative rejection"
  idea you are extending to personal memory. **~3 h**

### D2. Statistics you will be challenged on
*The exam question: "Is that difference significant with n=60?"*

- Bootstrap confidence intervals — learn to compute and to plot them. Non-negotiable: every
  headline number in your paper needs one.
- Mean ± standard deviation over **three seeds**, never a single run.
- **Dror et al., "The Hitchhiker's Guide to Testing Statistical Significance in NLP"** (ACL 2018) —
  search the title. Read it once; it will stop you making the two or three classic errors.
- Inter-annotator agreement (Cohen's κ) for your human verification pass.

### D3. Artifact and research hygiene
- **Datasheets for Datasets** (1803.09010) — you are writing one; read the original. **~2 h**
- **Model Cards for Model Reporting** (1810.03993) — skim. **~1 h**
- **Keshav, "How to Read a Paper"** (the three-pass method, one page) — search the title. Use it
  for every paper above; it will halve your reading time. **~15 m, highest ROI on this page**
- Tools: **Semantic Scholar** and **Connected Papers** for finding what cites what;
  **Zotero** for references. Set up Zotero in week 1 and never lose a citation again.

### D4. Writing the paper
- **Eugene Yan's blog** and **Chip Huyen's blog** — clear applied-ML writing to imitate.
- Read three recent Datasets & Benchmarks papers end-to-end purely for *structure*, not content.
  Notice how much space goes to construction and validation versus results.

---

## 6. Phase E — Context you should be conversant in (spread thin, ~10 h)

You are unlikely to be examined deeply here, but blank looks are costly.

- **Prompt injection.** **Greshake et al.** (2302.12173) — the paper that named indirect prompt
  injection, including the persistence-through-retrieval case your stored-injection probe tests.
  **PoisonedRAG** (2402.07867) for attacks on the index. **CaMeL** (2503.18813) and **AgentDojo**
  (2406.13352) for defence and evaluation. **Simon Willison's blog** is the best running commentary
  on this topic; read his prompt-injection tag. **~4 h**
- **Hallucination.** **Lilian Weng — "Extrinsic Hallucinations in LLMs"** (`lilianweng.github.io`).
  A superb survey-in-a-blog-post. **~2 h**
- **Agent memory.** **MemGPT** (2310.08560) — memory hierarchies for LLMs. **~1 h**
- **Browser extension platform.** Chrome for Developers documentation on Manifest V3, service
  workers, offscreen documents, and `chrome.debugger`. You built on these; be able to explain why
  the ML runs in an offscreen document and not the service worker. **~2 h**

---

## 7. What to deliberately NOT learn

Saying "that is out of scope, and here is why" is a *strength* in a viva. Skip:

- Reinforcement learning theory (PPO internals, GAE). Know only that DPO removes the need for it.
- Pretraining, distributed training, DeepSpeed/FSDP. You fine-tune 3B on one GPU.
- Vision-language models and GUI grounding — the action track is deferred; one sentence of future
  work is enough.
- Vector-database engineering (HNSW internals, sharding). Your index is a few thousand chunks.
- Agent frameworks (LangChain, LlamaIndex, AutoGen). You deliberately wrote your own thin layer;
  be ready to say so and why.
- Mechanistic interpretability. Fascinating, irrelevant here.

---

## 8. Mock viva — the questions you will actually get

Rehearse these **out loud**, timed to about 90 seconds each. Write your answers down first; if you
cannot write it, you cannot say it under pressure.

**On motivation**
1. In one sentence, what problem does this solve that a search box does not?
2. Why would anyone want this locally instead of using ChatGPT?
3. Who is the user? Give me a concrete person and a concrete moment.

**On the benchmark (expect the most questions here — it is your main contribution)**
4. Why build a new benchmark instead of using LoCoMo, LongMemEval, or AbstentionBench?
5. How do you know a "stale" item is genuinely stale and not Wikipedia fixing an error?
   *(This is your time-anchor rule. Own it: the sentence's own date reference must move forward.
   Corrections keep the anchor fixed; date fixes move it backward. Show the Tesla example.)*
6. Your data is synthetic personas over real pages. Why should I believe results transfer to real
   users? *(Answer: the consented student evaluation — and be honest that it is small.)*
7. What stops a model from scoring well by exploiting a template artifact?
   *(Answer: this is exactly why v0 was discarded. Tell that story — it demonstrates rigor.)*
8. How large is your test set, and what is the confidence interval on your headline number?

**On method**
9. Why fine-tune at all? Show me the prompted baseline first.
10. Why DPO rather than PPO, or rather than more SFT?
11. Where do your preference pairs come from, and why is mining the model's own failures better
    than sampling randomly?
12. What is the actual training signal that teaches abstention? Why does it not collapse into
    refusing everything? *(Your answer: the answerable classes and the fresh control class, plus
    refusal precision — not just recall — in the metrics.)*

**On results**
13. Your abstention AUROC is X. What does that number mean operationally to a user?
14. Retrieval score was a *better* abstention signal than the model's own decision in your early
    baseline. Doesn't that undermine the case for fine-tuning?
    *(Be ready. Honest answer: on the untuned model, yes — and it motivates the work. Show the
    stale class, where retrieval score cannot help by construction.)*
15. What happens on a user whose reading looks nothing like your personas?

**On limitations — volunteer these before you are asked**
16. What is the weakest part of this work? *(Have a real answer ready. Suggested: the benchmark's
    questions are machine-generated and only a sample is human-verified.)*
17. What would you do with six more months and a real GPU?
18. Does this solve prompt injection? *(No. Never claim otherwise. Defense-in-depth, measured, not
    solved.)*

---

## 9. Weekly cadence that actually works

- **Two study blocks a week**, 3 hours each, protected from build work. Building expands to fill
  all available time; reading does not survive unless scheduled.
- **One paper per block, three-pass method.** Pass one is five minutes. Most papers stop there.
- **Keep a single `notes/` file per paper** with three lines: what they did, what I take, what I
  reject. At the end you will have your related-work section already written.
- **Teach it.** Explain each week's paper to a teammate for ten minutes. The moment you stumble is
  the exact thing an examiner will find.
- **Update the related-work grid in [`04`](04_RELATED_WORK.md) as you read**, not at the end.

---

## 10. Order of attack, mapped to the build plan

| Weeks | Build (docs/07 §8) | Study |
|---|---|---|
| 1–3 | Benchmark v1 generation | A1, A3, B5 — *you are designing the staleness axis now, so read FreshQA, LoCoMo, LongMemEval first* |
| 3–5 | Freeze test set, baselines | B1, B2 — you cannot interpret your own baselines without these |
| 5–7 | Abstention-signal study | B2, B3 — conformal before you run E2 |
| 6–10 | SFT then DPO | C1, C2, B4 |
| 10–13 | Transfer + on-device | D1, D2, E |
| 13–16 | Writing | D3, D4, and §8 rehearsal twice |

**Do not read ahead of the build.** A paper read three weeks before you need it is a paper you
will read twice.

---

*Prev: [07 — Revised plan](07_REVISED_PLAN_2026-09.md). Bibliography: [04](04_RELATED_WORK.md).*
