# Safety Changelog

A dedicated log of **safety-, privacy-, and security-relevant** design decisions and
changes for Groundwork — an agent that can see and control a browser. Every entry names the
**threat considered** and the **mitigation / decision**. This complements
[`CHANGELOG.md`](CHANGELOG.md) and the threat model in
[`docs/02_TECHNICAL_ARCHITECTURE.md` §6](docs/02_TECHNICAL_ARCHITECTURE.md).

> **Standing principle:** we treat indirect prompt injection as an *unsolved, industry-wide*
> problem. Groundwork uses defense-in-depth and calibrated deferral as a fail-safe; we do
> **not** claim to eliminate injection. See [`SECURITY.md`](SECURITY.md).

Add an entry here in the same PR as any change that touches: the action space, how untrusted
content is handled, permissions, data storage/egress, or confirmation/deferral behavior.

---

## [Unreleased]

### Architecture & scope decisions
- **Transactions kept out of scope** (checkout / booking / actions on authenticated
  third-party sessions). *Threat:* a successful injection or mis-action causing financial or
  account harm; CFAA/authorization exposure. *Decision:* minimize blast radius by leading
  with research / extraction / recall over the user's own content.
- **Local-first data model.** *Threat:* third-party cloud gaining a durable record of
  everything the user reads. *Decision:* page content, the memory index, and the primary
  models stay on-device; any cloud planner is opt-in and content-blind.

### Untrusted-content handling
- **Spotlighting of page & history text** (`lib/safety/spotlight`). *Threat:* indirect
  prompt injection — page/source text hijacking the agent. *Mitigation:* all page-derived
  text and all retrieved history is wrapped/marked untrusted before reaching a model, plus a
  system-prompt instruction not to obey instructions found inside sources.
- **Retrieved history treated as untrusted.** *Threat:* **cross-session stored injection** —
  malicious text captured yesterday firing when recalled today. *Actual mitigation today:*
  each retrieved chunk is wrapped by `spotlight()` inside the grounded-QA prompt, and the
  system prompt says not to follow instructions in sources. **`guardRetrieved()` is currently
  an identity function** (audit 2026-09-06); segregation of instruction-like retrieved text
  is not implemented. Measured by the stored-injection probe split (docs/07 E7).
- **DOM sanitization hook** (`lib/safety/sanitizeNodes`). *Threat:* hidden / off-screen /
  freshly-injected elements and adversarial pop-ups. **Status: exists but is not called
  anywhere** (audit 2026-09-06); the observation currently carries a `hidden` state flag only.
- **Spotlighting is delimiter-only.** `spotlight()` wraps text in `<<UNTRUSTED_CONTENT>>`
  markers. Microsoft's reported injection reduction (>50% → <2%) was for *datamarking and
  encoding*; delimiting alone was the weakest variant in that study. We do **not** inherit
  that number.

### Action safety
- **Stale-snapshot guard** (`lib/act`). *Threat:* acting on an outdated observation (page
  changed under the agent). *Mitigation:* an action's `versionId` must match the observation
  it was decided on, or execution is refused.
- **Risk classification + confirmation gate** (SAFE / CAUTION / UNSAFE). *Threat:*
  irreversible/state-changing actions taken without consent. *Mitigation:* non-SAFE actions
  return `needsConfirm` and are not executed until the user approves; submit/pay/delete-like
  clicks are flagged UNSAFE.
- **Human-in-the-loop enforced in the agent loop** (`lib/agent`). *Threat:* an autonomous
  loop taking risky actions without oversight. *Mitigation:* the loop pauses on any non-SAFE
  action and streams a confirmation card (Approve/Reject) to the side panel before executing;
  it is step-limited and user-cancelable (Stop). Element text is `spotlight()`-wrapped
  *before* the decision model sees it, so page content cannot steer the agent as instructions.
- **Calibrated grounded refusal** (`lib/model`). *Threat:* confident hallucination over a
  personal memory. *Mitigation:* answer only from cited sources or reply "Not found in your
  history."; degrade to retrieval-only (never fabricate) when the local model is unavailable.

### Privacy
- **Offline embedding model.** *Threat:* leaking browsing content to a model host at
  embedding time. *Mitigation:* the embedding model is bundled locally (`npm run fetch-model`)
  and transformers.js is configured for local-only loading — no Hub call at runtime.
- **Minimal permissions & no remote code.** *Threat:* extension permission creep; remote
  code execution. *Decision:* `activeTab` + narrowable host permissions; CSP forbids remote
  code; model weights are fetched by an explicit step and never committed.

### Privacy controls (implemented)
- **Blocklist-gated capture + master capture toggle** (`lib/settings`, enforced in
  `background.captureActiveTab`). *Threat:* accidentally indexing sensitive pages (banking,
  webmail, health, messaging, password managers), or capturing when the user doesn't want it.
  *Mitigation:* capture is gated **before** anything is written — a conservative default
  domain/path blocklist (user-editable) short-circuits indexing, and a master toggle disables
  capture entirely. Blocked domains are refused even when capture is on.
- **One-click memory wipe** (two-step confirm). *Threat:* no user recourse to purge the local
  index. *Mitigation:* Settings → "Wipe all memory" clears the PGlite store immediately.

### Resolved 2026-09-06 (verified in a real Chrome by `extension/e2e/smoke.mjs`)
- ~~PGlite's use of direct `eval` vs the extension CSP~~ — **works** under
  `script-src 'self' 'wasm-unsafe-eval'`: pages are stored and retrieved in the offscreen document.
- ~~ONNX-runtime WASM offline hosting~~ — **was broken**: onnxruntime-web dynamically imported its
  engine from a CDN (blocked by the CSP → "no available backend found"). *Mitigation:* the engine is
  now copied into `public/ort/` by `npm run fetch-model` and loaded from the extension origin; no
  network request is made at embedding time. *Threat closed:* embedding-time egress.

### Known open risks (tracked, not yet mitigated)
- **Retrieval rejection threshold is uncalibrated.** `NEG_REJECT = 0.25` cosine never fires with
  bge-small (an unrelated query scored 0.47), so "Not found in your history" currently depends
  entirely on the model's prompted refusal. To be calibrated in docs/07 E1/E2.
- Robustness under **adaptive** injection attacks — to be evaluated with AgentDojo / WASP /
  ST-WebAgentBench-style suites (see [`docs/03`](docs/03_RESEARCH_PAPER_PLAN.md), E5/E6).
