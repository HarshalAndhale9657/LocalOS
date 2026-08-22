# References & attributions

Groundwork's extension is **built from scratch** (WXT + React + MV3), but several
architectural patterns are informed by prior open-source work. Documented here for
honest attribution (all Apache-2.0) — see `../docs/04_RELATED_WORK.md` for the full
research bibliography.

- **Nanobrowser** (https://github.com/nanobrowser/nanobrowser) — MV3 + side-panel +
  `chrome.debugger`/CDP observe-and-act, and the Planner/Navigator/Validator multi-agent
  loop and Ollama call path. We reuse the *ideas*, not the code.
- **browser-use** (https://github.com/browser-use/browser-use) — accessibility-tree /
  compressed-DOM observation and element-index action representation.

No third-party extension code is vendored; if any snippet is adapted, it will be marked
inline with its source and license.
