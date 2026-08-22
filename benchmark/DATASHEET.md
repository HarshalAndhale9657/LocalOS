# Datasheet — Personal-Memory-RGB

Following *Datasheets for Datasets* (Gebru et al., 2021). This documents the **v0**
(fully synthetic) release and is the template to complete before any archival publication.
Spec: [`../docs/05_BENCHMARK_Personal_Memory_RGB.md`](../docs/05_BENCHMARK_Personal_Memory_RGB.md).

## Motivation
- **Why created?** No standard benchmark evaluates grounded QA **+ calibrated refusal** over
  a user's *own, timestamped, noisy* browsing memory (with staleness and false-premise
  cases). Personal-Memory-RGB fills that gap and is the evaluation artifact for Groundwork's
  "calibrated grounding" thesis.
- **Who created it?** The Groundwork project (see [`../CITATION.cff`](../CITATION.cff)).

## Composition
- **Instances:** synthetic browsing *histories* (persona + timestamped pages) and *QA items*.
- **Question classes:** answerable (`single_hop`, `multi_hop`, `time_scoped`) and must-abstain
  (`not_in_history`, `stale`, `false_premise`); an action-safety split is planned (M4).
- **v0 scale (reproducible, seed 7):** ~20 histories / ~300 items, balanced ~50/50
  answerable vs must-abstain; splits are **by `history_id`** (train/dev/test, no leakage).
- **Labels:** gold decision (`answer`/`abstain`), gold answer, exact source chunk(s) +
  read-date for answerable items; abstain reason for negatives.
- **Is anything missing / noisy?** Deliberately: histories include boilerplate, near-duplicates
  (SimHash-labeled), and off-topic reading to stress retrieval + refusal.

## Collection process
- **v0 is fully synthetic** — fabricated, self-consistent facts generated deterministically
  (`pmrgb/generate.py`); **no real users, no PII, no scraped copyrighted text.**
- **Future (M2):** teacher-LLM paraphrasing for natural phrasing over public-source content,
  gated by an NLI auto-verify step + human spot-check (target ≥95% agreement).

## Preprocessing / cleaning / labeling
- Chunking (`pmrgb/chunk.py`), SimHash near-dup labeling (`pmrgb/simhash.py`).
- Answerable items are validated so the gold answer is entailed by the cited chunk;
  citation integrity is checked (v0: 74/74 citations resolve, 0 invariant violations).

## Uses
- **Intended:** evaluating grounded-QA quality, citation precision/recall, and calibrated
  refusal (refusal P/R, risk-coverage, abstention AUROC); benchmarking on-device models.
- **Out of scope / discouraged:** training identity/biometric models; treating synthetic
  facts as real-world knowledge.

## Distribution & licensing
- Format: JSONL (items) + JSONL (histories); HuggingFace `datasets`-compatible loader.
- License (intended): CC-BY-4.0 for data, MIT for code. Respect each upstream source's
  license once real-source content is introduced (M2).
- Generated data is **not** committed (`benchmark/data/` is gitignored); regenerate via
  `python build_v0.py`.

## Maintenance
- Versioned with the repo; `seed` + generator version make releases reproducible.
- Contact: shahjay147@gmail.com. Report issues via the repo tracker.

## Ethics
- Fully synthetic in v0 → no privacy risk. Any injected/adversarial content (stored-injection
  cases) will be clearly flagged. The benchmark measures a *safety-relevant* capability
  (knowing when to abstain); results should be reported honestly (no "solved" claims).
