/**
 * Groundwork offscreen document (M1.4) — the on-device ML host.
 * Owns transformers.js embeddings + the PGlite/pgvector store, and answers
 * INDEX_PAGE / RETRIEVE / WIPE messages. See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §4.
 */
import { chunkText } from '../../lib/memory/chunk';
import { simhashHex } from '../../lib/memory/simhash';
import { embed, embedOne } from '../../lib/memory/embed';
import { upsertPage, searchByVector, simhashExists, wipe } from '../../lib/memory/store';
import { timeDecay, mmr, type Candidate } from '../../lib/memory/rank';
import type { RetrievedChunk } from '../../lib/types';

const NEG_REJECT = 0.25; // drop weak matches -> supports "not found in your history"

async function indexPage(page: { url: string; title?: string; text?: string; readAt?: string }) {
  const text = (page.text ?? '').trim();
  if (!text) return { indexed: false, chunks: 0, reason: 'empty' };
  const sh = simhashHex(text);
  if (await simhashExists(sh)) return { indexed: false, chunks: 0, reason: 'near-duplicate' };
  const chunks = chunkText(text);
  const vecs = await embed(chunks.map((c) => c.text));
  await upsertPage({
    pageId: page.url,
    url: page.url,
    title: page.title ?? '',
    readAt: page.readAt ?? new Date().toISOString(),
    simhash: sh,
    chunks: chunks.map((c, i) => ({ chunkId: c.chunkId, text: c.text, vec: vecs[i] ?? [] })),
  });
  return { indexed: true, chunks: chunks.length };
}

async function retrieve(query: string, opts?: { k?: number; asOf?: string }): Promise<RetrievedChunk[]> {
  const k = opts?.k ?? 5;
  const asOf = opts?.asOf ?? new Date().toISOString();
  const qv = await embedOne(query);
  const raw = await searchByVector(qv, Math.max(k * 4, 20));
  const cands: Candidate<RetrievedChunk>[] = raw
    .filter((r) => 1 - r.distance >= NEG_REJECT)
    .map((r) => ({
      item: {
        pageId: r.pageId,
        chunkId: r.chunkId,
        url: r.url,
        title: r.title,
        readAt: r.readAt,
        text: r.text,
        score: 1 - r.distance,
      },
      vec: r.vec,
      score: (1 - r.distance) * timeDecay(r.readAt, asOf),
    }));
  return mmr(cands, k);
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.target !== 'offscreen') return false;
  (async () => {
    try {
      if (msg.type === 'INDEX_PAGE') sendResponse(await indexPage(msg.page));
      else if (msg.type === 'RETRIEVE') sendResponse({ chunks: await retrieve(msg.query, msg.opts) });
      else if (msg.type === 'WIPE') {
        await wipe();
        sendResponse({ ok: true });
      } else sendResponse({ error: `unknown type ${msg.type}` });
    } catch (e: any) {
      sendResponse({ error: String(e?.message ?? e) });
    }
  })();
  return true; // async response
});

console.log('[groundwork] offscreen ready');
