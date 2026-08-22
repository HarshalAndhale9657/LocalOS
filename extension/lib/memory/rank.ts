/**
 * Ranking helpers: exponential time-decay + MMR diversity (docs/02 §4).
 * Pure functions so they're easy to reason about and unit-test.
 */

/** Exponential decay by age; halfLifeDays sets how fast old reads fade. */
export function timeDecay(readAtIso: string, asOfIso: string, halfLifeDays = 30): number {
  const read = Date.parse(readAtIso);
  const now = Date.parse(asOfIso);
  if (Number.isNaN(read) || Number.isNaN(now)) return 1;
  const ageDays = Math.max(0, (now - read) / 86_400_000);
  return Math.pow(0.5, ageDays / halfLifeDays);
}

export function cosine(a: number[], b: number[]): number {
  let dot = 0;
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) dot += a[i]! * b[i]!; // vectors are pre-normalized
  return dot;
}

export interface Candidate<T> {
  item: T;
  vec: number[];
  score: number; // relevance (already time-decayed)
}

/** Maximal Marginal Relevance: pick k diverse-yet-relevant candidates. */
export function mmr<T>(cands: Candidate<T>[], k: number, lambda = 0.7): T[] {
  const selected: Candidate<T>[] = [];
  const pool = [...cands];
  while (selected.length < k && pool.length) {
    let best = 0;
    let bestScore = -Infinity;
    for (let i = 0; i < pool.length; i++) {
      const cand = pool[i]!;
      const div = selected.length ? Math.max(...selected.map((s) => cosine(cand.vec, s.vec))) : 0;
      const mmrScore = lambda * cand.score - (1 - lambda) * div;
      if (mmrScore > bestScore) {
        bestScore = mmrScore;
        best = i;
      }
    }
    selected.push(pool.splice(best, 1)[0]!);
  }
  return selected.map((c) => c.item);
}
