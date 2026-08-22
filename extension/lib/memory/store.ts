/**
 * In-browser vector store: PGlite (WASM Postgres) persisted to IndexedDB.
 * Runs ONLY in the offscreen document (docs/02 §4/§7).
 *
 * v1 stores embeddings as JSON text and does exact cosine search in JS — correct and
 * dependency-light for a personal index of a few thousand chunks. Swapping in pgvector
 * + HNSW (once the extension subpath is available) is a drop-in optimization behind
 * `searchByVector`. Hybrid BM25 + cross-encoder rerank land in a follow-up.
 */
import { PGlite } from '@electric-sql/pglite';
import { cosine } from './rank';

export interface StoredChunk {
  pageId: string;
  chunkId: string;
  url: string;
  title: string;
  readAt: string;
  text: string;
  vec: number[];
  distance: number; // cosine distance from the query (0 = identical)
}

let dbPromise: Promise<PGlite> | null = null;

async function db(): Promise<PGlite> {
  if (!dbPromise) {
    dbPromise = (async () => {
      const pg = await PGlite.create('idb://groundwork-memory');
      await pg.exec(`
        CREATE TABLE IF NOT EXISTS pages (
          page_id TEXT PRIMARY KEY, url TEXT, title TEXT, read_at TEXT, simhash TEXT
        );
        CREATE TABLE IF NOT EXISTS chunks (
          page_id TEXT REFERENCES pages(page_id) ON DELETE CASCADE,
          chunk_id TEXT, text TEXT, embedding TEXT,
          PRIMARY KEY (page_id, chunk_id)
        );
      `);
      return pg;
    })();
  }
  return dbPromise;
}

export interface PageRecord {
  pageId: string;
  url: string;
  title: string;
  readAt: string;
  simhash: string;
  chunks: { chunkId: string; text: string; vec: number[] }[];
}

export async function simhashExists(simhash: string): Promise<boolean> {
  const pg = await db();
  const r = await pg.query<{ n: number }>('SELECT count(*)::int AS n FROM pages WHERE simhash = $1', [simhash]);
  return (r.rows[0]?.n ?? 0) > 0;
}

export async function upsertPage(rec: PageRecord): Promise<void> {
  const pg = await db();
  await pg.query(
    `INSERT INTO pages (page_id, url, title, read_at, simhash) VALUES ($1,$2,$3,$4,$5)
     ON CONFLICT (page_id) DO UPDATE SET url=excluded.url, title=excluded.title, read_at=excluded.read_at, simhash=excluded.simhash`,
    [rec.pageId, rec.url, rec.title, rec.readAt, rec.simhash],
  );
  for (const c of rec.chunks) {
    await pg.query(
      `INSERT INTO chunks (page_id, chunk_id, text, embedding) VALUES ($1,$2,$3,$4)
       ON CONFLICT (page_id, chunk_id) DO UPDATE SET text=excluded.text, embedding=excluded.embedding`,
      [rec.pageId, c.chunkId, c.text, JSON.stringify(c.vec)],
    );
  }
}

interface Row {
  page_id: string;
  chunk_id: string;
  text: string;
  embedding: string;
  url: string;
  title: string;
  read_at: string;
}

/** Exact cosine top-N (JS-side). Vectors are pre-normalized, so cos = dot product. */
export async function searchByVector(queryVec: number[], n: number): Promise<StoredChunk[]> {
  const pg = await db();
  const r = await pg.query<Row>(
    `SELECT c.page_id, c.chunk_id, c.text, c.embedding, p.url, p.title, p.read_at
     FROM chunks c JOIN pages p ON p.page_id = c.page_id`,
  );
  const scored = r.rows.map((row) => {
    const vec = JSON.parse(row.embedding) as number[];
    return {
      pageId: row.page_id,
      chunkId: row.chunk_id,
      url: row.url,
      title: row.title,
      readAt: row.read_at,
      text: row.text,
      vec,
      distance: 1 - cosine(queryVec, vec),
    };
  });
  scored.sort((a, b) => a.distance - b.distance);
  return scored.slice(0, n);
}

export async function wipe(): Promise<void> {
  const pg = await db();
  await pg.exec('DELETE FROM chunks; DELETE FROM pages;');
}
