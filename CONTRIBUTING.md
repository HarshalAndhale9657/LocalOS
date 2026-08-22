# Contributing to Groundwork

Thanks for your interest! Groundwork is a privacy-first, local-first agentic browser
assistant and an active research project. This guide covers how to set up, the standards
we hold code to, and how to propose changes.

## Ground rules (project-specific, non-negotiable)

These come from the project's thesis and threat model — see [`CLAUDE.md`](CLAUDE.md) and
[`docs/02_TECHNICAL_ARCHITECTURE.md`](docs/02_TECHNICAL_ARCHITECTURE.md):

1. **Local-first.** Page content, the memory index, and the primary models must never
   leave the device. Any cloud path must be opt-in and content-blind.
2. **Untrusted content.** All page-derived text — and all *retrieved history* — is
   untrusted. Wrap it with `spotlight()` before it reaches a model; never let source text
   act as instructions.
3. **Calibrated grounding.** Answer only from retrieved sources with citations, else
   abstain. Actions require the stale-snapshot guard; non-SAFE actions require confirmation.
4. **No overstated claims.** In code, docs, and the paper: safety is defense-in-depth, not
   "solved." Report metrics honestly, with caveats.
5. **Transactions stay out of scope** for now (checkout/booking/auth'd third-party actions).

## Development setup

Prereqs: Node 22 (`.nvmrc`), Python 3.12, and (for the model path) [Ollama](https://ollama.com).

```bash
# extension
cd extension && npm install && npm run fetch-model
npm run dev        # dev Chrome + side panel

# benchmark (no third-party deps)
cd ../benchmark && python build_v0.py --histories 20 --seed 7
python -m eval.run_reference --data data/v0
```

## Before you open a PR

- **Extension:** `npm run compile` (typecheck) **and** `npm run build` must pass.
- **Benchmark:** `build_v0.py` + `run_baseline` + `run_reference` must run clean (no broken
  citations, no invariant violations).
- Match the surrounding code style (2-space TS, strict types, `import type` for types).
- Update docs when behavior changes; add a `CHANGELOG.md` entry.
- **If your change touches safety, privacy, permissions, the action space, or how untrusted
  content is handled, add a `SAFETY_CHANGELOG.md` entry** and describe the threat considered.

## Commit & branch conventions

- Branch off `main` (e.g. `feat/hybrid-retrieval`, `fix/cdp-detach`).
- Prefer [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`,
  `docs:`, `refactor:`, `test:`, `chore:`).
- Keep PRs focused; describe what was build-verified vs runtime-verified (some changes can
  only be verified by loading the extension in Chrome — say so).

## Reporting security issues

Do **not** open a public issue for vulnerabilities. See [`SECURITY.md`](SECURITY.md).

## License

By contributing, you agree your contributions are licensed under the [MIT License](LICENSE).
