import type { RetrievedChunk } from '../types';

/**
 * Local RAG memory (M1.4). Runs in the OFFSCREEN document (transformers.js
 * embeddings + PGlite/pgvector). See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §4.
 *
 * Pipeline: capture -> clean(Readability) -> dedup(SimHash) -> chunk(400–512, no overlap)
 *   -> embed(bge-small / nomic, Matryoshka 128–256) -> store(PGlite+pgvector, HNSW)
 * Retrieve: dense + BM25 (RRF) -> rerank(bge-reranker-v2-m3) -> time-decay + MMR
 *   -> low top score ⇒ abstain signal.
 */
export interface MemoryStore {
  index(page: { url: string; title: string; text: string; readAt: string }): Promise<void>;
  retrieve(query: string, opts?: { k?: number; asOf?: string }): Promise<RetrievedChunk[]>;
  wipe(): Promise<void>;
}

// TODO(M1.4): implement against PGlite + pgvector in the offscreen document.
export function createMemoryStore(): MemoryStore {
  throw new Error('not implemented — M1.4');
}
