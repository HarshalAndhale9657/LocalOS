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

## Reproducible v0 result (seed 7, 20 histories / 300 items; 60/20/20 split by history)

Trivial systems frame the axis (oracle 1.0; always-answer & always-abstain both fail).
The **reference system** (BM25 retrieval + score-threshold abstention, **τ fit on dev,
reported on held-out test**) reaches abstain-F1 ≈ **0.81** / decision-acc ≈ **0.78** /
**abstention-AUROC ≈ 0.81** — but its per-type breakdown on test is the point:

| class | lexical-threshold decision acc (test) |
|---|---|
| not_in_history | 1.00 |
| stale | 1.00 |
| multi_hop | 0.92 |
| false_premise | 0.88 |
| single_hop | 0.75 |
| **time_scoped** | **0.00** |

> **⚠️ v0 is a harness validator, not a claims-grade dataset (audit 2026-09-06).** The per-class
> pattern above is explained by the generator, not by calibration: `time_scoped` scores 0.00 only
> because read dates live in metadata that BM25 never sees (a date-aware baseline flips it to ≈1.0);
> every price is stale by construction so "price" is a keyword, not a temporal test;
> `not_in_history` is separable because all pages share one sentence template; `false_premise`
> asks for a foreign-domain attribute; the retriever stopword list contains the question-template
> words; and the test split has 8–12 items per class (±~30-point intervals). **No number from v0
> goes in the paper.** v1 (real-source content, Wikipedia-revision stale/fresh pairs, dates in text
> and metadata, 2–3k items, human-verified test) replaces it — see
> [docs/07 §4](../docs/07_REVISED_PLAN_2026-09.md).
*(Numbers move slightly with `--histories`/`--seed`; split is by `history_id` so no history leaks across dev/test.)*

## Question classes (v0)
Answerable: `single_hop`, `multi_hop`, `time_scoped`.
Must-abstain: `not_in_history`, `stale`, `false_premise`.
Target balance ≈ 50/50 so trivial always-answer / always-abstain baselines both score poorly —
calibration is the discriminator.

## Model-based harness (M1.6) — uses the product's own prompt

`eval/run_model.py` runs a local model through Ollama using the **shared** prompt and parser
(`../shared/prompts`, `pmrgb/core.py`, mirrored by `../extension/lib/model/core.ts` and checked
against the same vectors in `../shared/tests/refusal_cases.json`). Numbers therefore describe the
extension, not a re-implementation.

```bash
python -m eval.run_model --data data/v0 --model qwen2.5:3b-instruct --split test   # ~12 s/item on CPU
python -m eval.run_model --data data/v0 --limit 6                                   # smoke test
```
Per-item predictions (raw model text, citations, retrieval score, prompt version) are written next
to the data for auditing.

## Wikipedia revision miner (v1 stale/fresh source)

`pmrgb/revisions.py` mines **real** stale-vs-fresh fact pairs from two revisions of an article
(docs/07 §4.2): sentences whose numbers changed are `stale` candidates; identical sentences are
`time_sensitive_fresh` candidates. Responses are cached under `data/cache/wiki/`.

```bash
python -m pmrgb.revisions --title "Mount Everest" --since 2024-01-01 --until 2026-09-01
python -m pmrgb.revisions --titles-file sources/titles_v1_seed.txt --out data/revisions
```
The summary line `PRIME stale candidates` counts pairs that are explicitly dated ("As of May 2024"),
not a unit re-rounding, and where a number was actually replaced. First run (8 articles):
16 prime candidates, i.e. about 2 per article; the 75-title seed list should yield ~150 before
the NLI/human gate, and the list will be extended to ~300 titles.
