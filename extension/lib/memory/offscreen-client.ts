/**
 * SW/page-side helper to lazily create the offscreen document and message it.
 * The offscreen doc hosts the ML that can't run in the service worker (docs/02 §7).
 */
let creating: Promise<void> | null = null;

export async function ensureOffscreen(): Promise<void> {
  const contexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'] as any,
  });
  if (contexts.length) return;
  if (!creating) {
    creating = chrome.offscreen
      .createDocument({
        url: 'offscreen.html',
        reasons: ['WORKERS'] as any, // run WASM embeddings + PGlite
        justification: 'Run local embeddings and the on-device vector store.',
      })
      .catch((e) => {
        // a concurrent caller may have created it first — ignore "only one" races
        if (!String(e).includes('Only a single offscreen')) throw e;
      })
      .finally(() => {
        creating = null;
      });
  }
  await creating;
}

export function callOffscreen<T = any>(msg: Record<string, unknown>): Promise<T> {
  return chrome.runtime.sendMessage({ target: 'offscreen', ...msg }) as Promise<T>;
}
