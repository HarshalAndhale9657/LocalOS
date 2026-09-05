/**
 * End-to-end runtime smoke test for Groundwork (no Claude-in-Chrome required).
 *
 * Launches the user's installed Chrome with the PRODUCTION build loaded as an unpacked
 * extension, serves a local fixture article, and sends the side panel's own messages to the
 * service worker. It verifies, in a real MV3 runtime:
 *   1. the service worker + offscreen document start (PGlite WASM under the extension CSP,
 *      ONNX embedding model loading from the bundled asset with no network),
 *   2. CAPTURE_ACTIVE_TAB  -> Readability -> chunk -> embed -> PGlite,
 *   3. MEMORY_RETRIEVE     -> cosine + decay + MMR returns the fixture chunk,
 *   4. ASK                 -> grounded answer with citations via Ollama (or the honest
 *                             retrieval-only degradation if Ollama is down),
 *   5. OBSERVE_ACTIVE_TAB  -> chrome.debugger / CDP accessibility snapshot.
 * All extension-origin console output and exceptions are captured and printed.
 *
 * Usage:  npm run e2e            (after `npm run build`; Ollama optional but recommended)
 * Env:    CHROME_PATH to override the Chrome binary; GW_HEADLESS=1 to try headless mode.
 */
import puppeteer from 'puppeteer-core';
import http from 'node:http';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const EXT_DIR = path.resolve(here, '..', '.output', 'chrome-mv3');
const FIXTURES = path.join(here, 'fixtures');
const CHROME =
  process.env.CHROME_PATH ||
  [
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    path.join(os.homedir(), 'AppData', 'Local', 'Google', 'Chrome', 'Application', 'chrome.exe'),
    '/usr/bin/google-chrome',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ].find((p) => fs.existsSync(p));

if (!CHROME) throw new Error('Chrome not found; set CHROME_PATH');
if (!fs.existsSync(path.join(EXT_DIR, 'manifest.json'))) throw new Error(`No build at ${EXT_DIR}; run npm run build`);

const results = [];
const logs = [];
const step = (name, ok, detail) => {
  results.push({ name, ok, detail });
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${detail ? '  — ' + detail : ''}`);
};
const withTimeout = (p, ms, what) =>
  Promise.race([p, new Promise((_, rej) => setTimeout(() => rej(new Error(`${what} timed out after ${ms} ms`)), ms))]);

// --- 1. static fixture server -------------------------------------------------------------
const server = http.createServer((req, res) => {
  const f = path.join(FIXTURES, req.url === '/' ? 'article.html' : req.url.replace(/^\//, ''));
  if (!fs.existsSync(f)) return void (res.writeHead(404), res.end());
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  fs.createReadStream(f).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const ARTICLE_URL = `http://127.0.0.1:${server.address().port}/article.html`;

// --- 2. launch Chrome with the extension --------------------------------------------------
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'gw-e2e-'));
const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: process.env.GW_HEADLESS ? 'shell' : false,
  userDataDir: profile,
  defaultViewport: { width: 1200, height: 800 },
  // Branded Chrome >= 137 ignores --load-extension; the supported path is the DevTools pipe +
  // --enable-unsafe-extension-debugging, which puppeteer wraps as enableExtensions/installExtension.
  enableExtensions: true,
  args: [
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-features=DialMediaRouteProvider,Translate',
  ],
});

// capture console + exceptions from every extension-origin target (SW, offscreen, side panel)
async function tapTarget(target) {
  if (!target.url().startsWith('chrome-extension://')) return;
  try {
    const s = await target.createCDPSession();
    const tag = target.url().split('/').pop() || target.type();
    await s.send('Runtime.enable');
    s.on('Runtime.consoleAPICalled', (e) => {
      const text = e.args.map((a) => a.value ?? a.description ?? '').join(' ');
      logs.push({ tag, level: e.type, text });
    });
    s.on('Runtime.exceptionThrown', (e) => {
      logs.push({ tag, level: 'exception', text: e.exceptionDetails.exception?.description ?? e.exceptionDetails.text });
    });
  } catch {
    /* some targets can't be attached; ignore */
  }
}
browser.on('targetcreated', tapTarget);
for (const t of browser.targets()) await tapTarget(t);

let exitCode = 1;
try {
  // --- 3. install the unpacked build, then wait for its service worker -----------------------
  const install = async () => {
    if (typeof browser.installExtension === 'function') return browser.installExtension(EXT_DIR);
    // raw CDP fallback (same mechanism puppeteer wraps): Extensions.loadUnpacked on the browser target
    const cdp = await browser.target().createCDPSession();
    const { id } = await cdp.send('Extensions.loadUnpacked', { path: EXT_DIR });
    return id;
  };
  const extId = await withTimeout(install(), 30_000, 'installExtension');
  step('extension installed', typeof extId === 'string' && extId.length === 32, extId);
  await withTimeout(
    browser.waitForTarget((t) => t.type() === 'service_worker' && t.url().includes(extId)),
    30_000,
    'service worker start',
  );
  step('service worker started', true);

  // --- 4. open the side panel page as a tab (our message-sending context) -------------------
  const panel = await browser.newPage();
  await panel.goto(`chrome-extension://${extId}/sidepanel.html`, { waitUntil: 'load' });
  const ping = await panel.evaluate(() => chrome.runtime.sendMessage({ type: 'PING' }));
  step('panel <-> background round-trip', ping?.ok === true, JSON.stringify(ping));

  // --- 5. open the fixture article and make it the active tab --------------------------------
  const article = await browser.newPage();
  await article.goto(ARTICLE_URL, { waitUntil: 'load' });
  await article.bringToFront();
  await new Promise((r) => setTimeout(r, 800)); // let the content script settle

  // --- 6. capture -> embed -> store (first call loads the ONNX model from the bundle) --------
  const t0 = Date.now();
  const cap = await withTimeout(
    panel.evaluate(() => chrome.runtime.sendMessage({ type: 'CAPTURE_ACTIVE_TAB' })),
    180_000,
    'CAPTURE_ACTIVE_TAB',
  );
  step('capture + embed + store', cap?.indexed === true && cap.chunks > 0, `${JSON.stringify(cap)} in ${Date.now() - t0} ms`);

  // dedup: the same page again must be rejected as a near-duplicate
  const cap2 = await withTimeout(panel.evaluate(() => chrome.runtime.sendMessage({ type: 'CAPTURE_ACTIVE_TAB' })), 60_000, 'dedup');
  step('SimHash near-duplicate rejection', cap2?.indexed === false && /dup/i.test(cap2.reason ?? ''), JSON.stringify(cap2));

  // --- 7. retrieve ---------------------------------------------------------------------------
  const ret = await withTimeout(
    panel.evaluate(() => chrome.runtime.sendMessage({ type: 'MEMORY_RETRIEVE', query: 'What is the aperture of the Kestrel Lantern telescope?', opts: { k: 3 } })),
    60_000,
    'MEMORY_RETRIEVE',
  );
  const hit = ret?.chunks?.find((c) => /203 millimeters/.test(c.text));
  step('retrieval returns the fixture chunk', !!hit, `top=${ret?.chunks?.[0]?.score?.toFixed(3)} n=${ret?.chunks?.length}`);

  // negative: unrelated query should retrieve nothing above the rejection threshold (or low)
  const neg = await withTimeout(
    panel.evaluate(() => chrome.runtime.sendMessage({ type: 'MEMORY_RETRIEVE', query: 'quarterly revenue of a European airline', opts: { k: 3 } })),
    60_000,
    'MEMORY_RETRIEVE (negative)',
  );
  step('negative query yields weak/no matches', !neg?.chunks?.length || neg.chunks[0].score < (hit?.score ?? 1), `top=${neg?.chunks?.[0]?.score?.toFixed(3) ?? 'none'}`);

  // --- 8. grounded answer via Ollama (or honest degradation) --------------------------------
  const t1 = Date.now();
  const ask = await withTimeout(
    panel.evaluate(() => chrome.runtime.sendMessage({ type: 'ASK', query: 'What is the aperture of the Kestrel Lantern telescope?', opts: { k: 4 } })),
    240_000,
    'ASK',
  );
  const a = ask?.answer;
  if (ask?.modelError) {
    step('ASK degraded honestly (Ollama unreachable)', a?.decision && a.confidence === 0, `${ask.modelError}`);
  } else {
    const grounded = a?.decision === 'answer' && /203/.test(a.text) && a.citations?.length > 0;
    step('ASK grounded answer with citation', grounded, `${JSON.stringify(a?.text).slice(0, 120)} cites=${a?.citations?.length} in ${Date.now() - t1} ms`);
    const askNeg = await withTimeout(
      panel.evaluate(() => chrome.runtime.sendMessage({ type: 'ASK', query: 'What was the closing price of Tesla stock yesterday?', opts: { k: 4 } })),
      240_000,
      'ASK (must-abstain)',
    );
    step('ASK abstains on an unread topic', askNeg?.answer?.decision === 'abstain', JSON.stringify(askNeg?.answer?.text).slice(0, 100));
  }

  // --- 9. CDP accessibility snapshot of the active tab --------------------------------------
  const obs = await withTimeout(panel.evaluate(() => chrome.runtime.sendMessage({ type: 'OBSERVE_ACTIVE_TAB' })), 60_000, 'OBSERVE_ACTIVE_TAB');
  step('CDP a11y observation', !obs?.error && obs?.nodeCount > 0 && !!obs.versionId, obs?.error ?? `nodes=${obs?.nodeCount} v=${obs?.versionId}`);

  exitCode = results.every((r) => r.ok) ? 0 : 1;
} catch (e) {
  step('unexpected failure', false, String(e?.message ?? e));
} finally {
  // --- report ------------------------------------------------------------------------------
  const errs = logs.filter((l) => l.level === 'error' || l.level === 'exception');
  console.log(`\nextension console: ${logs.length} messages, ${errs.length} errors/exceptions`);
  for (const l of logs.slice(0, 60)) console.log(`  [${l.tag}] ${l.level}: ${l.text.slice(0, 200)}`);
  fs.writeFileSync(path.join(here, 'last-run.json'), JSON.stringify({ when: new Date().toISOString(), results, logs }, null, 2));
  await browser.close().catch(() => {});
  server.close();
  fs.rmSync(profile, { recursive: true, force: true });
  console.log(`\n${results.filter((r) => r.ok).length}/${results.length} checks passed -> e2e/last-run.json`);
  process.exit(exitCode);
}
