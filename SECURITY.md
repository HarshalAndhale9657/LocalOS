# Security Policy

Groundwork is an agent that can **see and control a browser**, so security is a core design
constraint, not an add-on. This document covers how to report vulnerabilities and the
security posture of the project. The full threat model lives in
[`docs/02_TECHNICAL_ARCHITECTURE.md` §6](docs/02_TECHNICAL_ARCHITECTURE.md); safety-relevant
changes are logged in [`SAFETY_CHANGELOG.md`](SAFETY_CHANGELOG.md).

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report privately to **shahjay147@gmail.com** (or via GitHub Security Advisories once the
repo is public). Include:

- a description and impact assessment,
- steps to reproduce / a proof of concept,
- affected component (extension, local model path, benchmark, docs) and version/commit.

We aim to acknowledge within **72 hours** and to provide a remediation timeline after triage.
We support **coordinated disclosure** and will credit reporters who wish to be named.

## Supported versions

The project is pre-release (active development on feature branches). Only the latest `main`
is supported for security fixes until a tagged release exists.

| Version | Supported |
|---|---|
| `main` (latest) | ✅ |
| feature branches | ⚠️ best-effort |

## Scope

In scope: the Chrome MV3 extension (`extension/`), the local-model integration, the memory
subsystem, and the benchmark tooling (`benchmark/`).

Out of scope: third-party dependencies' own vulnerabilities (report upstream; we will bump),
and social-engineering of maintainers.

## Security posture (what we guarantee, and what we don't)

**Guarantees / design intent**
- **Local-first:** page content, the on-device memory index, and the primary models do not
  leave the device. Any cloud planner is opt-in and content-blind.
- **Untrusted-by-default content:** all page-derived text — and all retrieved history — is
  treated as untrusted (spotlighting, DOM sanitization) and must not act as instructions.
- **Human-in-the-loop for risk:** non-SAFE actions (state-changing) require confirmation;
  a stale-snapshot guard prevents acting on an outdated observation.
- **Minimized blast radius:** transactional automation (checkout/booking/auth'd third-party
  actions) is intentionally out of scope.

**We do NOT claim to solve prompt injection.** Indirect prompt injection is an open,
industry-wide problem. Groundwork uses **defense-in-depth** (spotlighting + instruction
hierarchy + quarantined executor + confirmation gates + calibrated deferral as a fail-safe)
and should be evaluated against *adaptive* attacks. Threats explicitly tracked include:
indirect prompt injection, **cross-session stored injection** (injected text in a page read
yesterday firing when recalled today), embedding inversion, and local-index tampering.

## Handling of the local index & models

- The memory index (PGlite/IndexedDB) is origin-scoped to the extension; treat device
  compromise as equivalent to browser-history compromise. A one-click wipe is provided.
- Model weights are fetched by an explicit `npm run fetch-model` step and are **not**
  committed to the repository.
