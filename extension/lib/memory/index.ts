import type { RetrievedChunk } from '../types';
import { ensureOffscreen, callOffscreen } from './offscreen-client';

/**
 * Local RAG memory (M1.4) — SW/page-side PROXY. The real work (embeddings +
 * PGlite/pgvector) runs in the offscreen document (see entrypoints/offscreen/main.ts).
 * See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §4.
 */
export interface PageInput {
  url: string;
  title: string;
  text: string;
  readAt?: string;
}

export interface IndexResult {
  indexed: boolean;
  chunks: number;
  reason?: string;
}

export interface MemoryStore {
  index(page: PageInput): Promise<IndexResult>;
  retrieve(query: string, opts?: { k?: number; asOf?: string }): Promise<RetrievedChunk[]>;
  wipe(): Promise<void>;
}

export function createMemory(): MemoryStore {
  return {
    async index(page) {
      await ensureOffscreen();
      return callOffscreen<IndexResult>({ type: 'INDEX_PAGE', page });
    },
    async retrieve(query, opts) {
      await ensureOffscreen();
      const r = await callOffscreen<{ chunks: RetrievedChunk[] }>({ type: 'RETRIEVE', query, opts });
      return r.chunks ?? [];
    },
    async wipe() {
      await ensureOffscreen();
      await callOffscreen({ type: 'WIPE' });
    },
  };
}
