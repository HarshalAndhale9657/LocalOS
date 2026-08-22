<!-- Thanks for contributing to Groundwork! Keep PRs focused. -->

## Summary

<!-- What does this change and why? Link any related issue: Closes #___ -->

## Type of change

- [ ] Feature
- [ ] Bug fix
- [ ] Docs / research
- [ ] Refactor / chore
- [ ] Benchmark / evaluation

## Verification

- [ ] `cd extension && npm run compile` passes
- [ ] `cd extension && npm run build` passes
- [ ] Benchmark runs clean (`build_v0.py` + `run_baseline` + `run_reference`), if touched
- [ ] Verified at runtime in Chrome — or explicitly noted as **build-verified only**

Notes on what was runtime- vs build-verified:

<!-- e.g. "CDP observe path is build-verified only; needs a Chrome load." -->

## Safety / privacy checklist

- [ ] Does **not** send page content, the memory index, or model weights off-device (or the cloud path is opt-in + content-blind)
- [ ] Treats page-derived and retrieved text as untrusted (spotlighting) where applicable
- [ ] Non-SAFE actions remain gated behind confirmation; stale-snapshot guard intact
- [ ] If this touches safety/privacy/permissions/action-space/untrusted-content handling, I added a **`SAFETY_CHANGELOG.md`** entry
- [ ] I did not overstate claims (safety = defense-in-depth, not "solved")

## Changelog

- [ ] Added a `CHANGELOG.md` entry (or this change doesn't warrant one)
