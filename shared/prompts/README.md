# Shared prompts (single source of truth)

These files are loaded **verbatim** by both the extension (`extension/lib/model`, via Vite `?raw`
imports) and the benchmark harness (`benchmark/pmrgb/core.py`). The paper's numbers must describe
the product, so neither side may define its own copy. Placeholders use `{name}` and are substituted
by plain string replacement (no `format()` semantics, so braces in prompt text are safe).

| File | Used for | Placeholders |
|---|---|---|
| `refusal.txt` | the exact calibrated-refusal string | — |
| `grounded_qa.system.txt` | grounded QA system prompt | `{refusal}` |
| `grounded_qa.user.txt` | grounded QA user turn | `{question}`, `{sources}` |
| `source_item.txt` | one numbered, spotlighted source | `{n}`, `{title}`, `{read_at}`, `{text}` |
| `action_decide.system.txt` | next-action decision (agent loop) | — |
| `action_decide.user.txt` | next-action user turn | `{goal}`, `{url}`, `{elements}`, `{recent}` |

Cross-language behaviour tests live in `../tests/refusal_cases.json` and are run by both
`vitest` (extension) and `pytest` (benchmark). Change a prompt → bump `PROMPT_VERSION` in
`version.txt` so every experiment run records which prompt it used.
