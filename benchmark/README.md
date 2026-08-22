# Personal-Memory-RGB — builder & evaluator

Reference implementation of the benchmark spec in
[`../docs/05_BENCHMARK_Personal_Memory_RGB.md`](../docs/05_BENCHMARK_Personal_Memory_RGB.md).

**v0 is fully synthetic and dependency-free (Python stdlib only).** It generates
self-consistent *fabricated* facts, so gold answers are unambiguous and the data is
freely releasable (no copyright, no PII). Later milestones enrich phrasing with a
teacher LLM (M2) and add the action-safety split (M4).

## Layout
```
benchmark/
├─ pmrgb/           # library: schema, generators
│  ├─ schema.py     # Page / History / QAItem dataclasses + (de)serialization
│  ├─ simhash.py    # 64-bit SimHash + Hamming distance (near-dup labeling)
│  ├─ chunk.py      # recursive chunker (~400–512 tokens, no overlap)
│  └─ generate.py   # deterministic synthetic history + QA generator
├─ eval/
│  ├─ metrics.py    # refusal precision/recall/F1, decision accuracy, risk-coverage
│  └─ run_baseline.py  # trivial systems to validate the harness end-to-end
├─ build_v0.py      # CLI: generate the v0 dataset into data/v0/
└─ data/            # generated output (gitignored until release)
```

## Run
```bash
cd benchmark
python build_v0.py --histories 12 --seed 7      # -> data/v0/{histories,items}.jsonl
python -m eval.run_baseline --data data/v0      # trivial systems (validates the harness)
python -m eval.run_reference --data data/v0     # BM25 + score-threshold abstention (a real baseline)
```

## Reproducible v0 result (seed 7, 12 histories / 180 items)

Trivial systems frame the axis (oracle 1.0; always-answer & always-abstain both fail).
The **reference system** (BM25 retrieval + score-threshold abstention) reaches
abstain-F1 ≈ 0.80 / decision-acc ≈ 0.78 / **abstention-AUROC ≈ 0.77** — but its per-type
breakdown is the point:

| class | lexical-threshold decision acc |
|---|---|
| not_in_history | 1.00 |
| stale | 1.00 |
| multi_hop | 0.97 |
| false_premise | 0.79 |
| single_hop | 0.72 |
| **time_scoped** | **0.00** |

A single global retrieval-score cutoff cannot separate *answerable-but-low-lexical-overlap*
questions (time-scoped / recency) from *must-abstain* ones. Closing that gap with a **learned**
abstention signal (SFT+DPO calibrated model) is the paper's core claim ([docs/03](../docs/03_RESEARCH_PAPER_PLAN.md)).
*(Caveat: the reference threshold is currently fit on the eval set — an optimistic upper bound;
a dev/test split lands in M2.)*

## Question classes (v0)
Answerable: `single_hop`, `multi_hop`, `time_scoped`.
Must-abstain: `not_in_history`, `stale`, `false_premise`.
Target balance ≈ 50/50 so trivial always-answer / always-abstain baselines both score poorly —
calibration is the discriminator.
