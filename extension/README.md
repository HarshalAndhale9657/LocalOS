# WXT + React

This template should help get you started developing with React in WXT.


## Runtime smoke test (real Chrome, no manual clicking)

```bash
npm run build && npm run e2e
```
`e2e/smoke.mjs` launches your installed Chrome over the DevTools pipe, installs `.output/chrome-mv3`,
serves `e2e/fixtures/article.html`, and sends the side panel's own messages to the service worker:
capture → embed → store, dedup, retrieve, ASK (grounded answer via Ollama, or honest degradation if
Ollama is down), and the CDP observation. Console output from the service worker, offscreen document
and side panel is captured; results land in `e2e/last-run.json`. Requires `npm run fetch-model` once.
