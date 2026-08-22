/**
 * 64-bit SimHash + Hamming distance for near-duplicate detection (docs/02 §4).
 * Uses BigInt; token hash = 64-bit FNV-1a. Mirrors benchmark/pmrgb/simhash.py.
 */
const MASK = (1n << 64n) - 1n;
const FNV_OFFSET = 1469598103934665603n;
const FNV_PRIME = 1099511628211n;

function fnv1a64(token: string): bigint {
  let h = FNV_OFFSET;
  for (let i = 0; i < token.length; i++) {
    h ^= BigInt(token.charCodeAt(i) & 0xff);
    h = (h * FNV_PRIME) & MASK;
  }
  return h;
}

export function simhash64(text: string): bigint {
  const tokens = text.toLowerCase().match(/[a-z0-9]+/g) ?? [];
  if (!tokens.length) return 0n;
  const v = new Array<number>(64).fill(0);
  for (const tok of tokens) {
    const hv = fnv1a64(tok);
    for (let i = 0; i < 64; i++) v[i] = v[i]! + ((hv >> BigInt(i)) & 1n ? 1 : -1);
  }
  let out = 0n;
  for (let i = 0; i < 64; i++) if (v[i]! > 0) out |= 1n << BigInt(i);
  return out;
}

export function hamming(a: bigint, b: bigint): number {
  let x = a ^ b;
  let c = 0;
  while (x) {
    x &= x - 1n;
    c++;
  }
  return c;
}

export const isNearDup = (a: string, b: string, threshold = 3) =>
  hamming(simhash64(a), simhash64(b)) <= threshold;

export const simhashHex = (text: string) => '0x' + simhash64(text).toString(16).padStart(16, '0');
