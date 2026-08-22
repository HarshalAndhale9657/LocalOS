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
python -m eval.run_baseline --data data/v0      # prints a metrics table
```

## Question classes (v0)
Answerable: `single_hop`, `multi_hop`, `time_scoped`.
Must-abstain: `not_in_history`, `stale`, `false_premise`.
Target balance ≈ 50/50 so trivial always-answer / always-abstain baselines both score poorly —
calibration is the discriminator.
