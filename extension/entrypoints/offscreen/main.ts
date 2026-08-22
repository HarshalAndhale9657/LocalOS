/**
 * Groundwork offscreen document (M1.4).
 * Hosts the ML that can't run in the service worker: transformers.js embeddings
 * and the PGlite/pgvector store. Created at runtime by the SW via
 * chrome.offscreen.createDocument({ url: 'offscreen.html', reasons: ['WORKERS'] }).
 * See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §4 and §7.
 */
console.log('[groundwork] offscreen ready');

// TODO(M1.4): load embedding model (bge-small / nomic, Matryoshka 128–256),
// init PGlite + pgvector, and expose index()/retrieve() over runtime messages.
export {};
