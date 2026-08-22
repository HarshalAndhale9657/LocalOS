import type { AXNode, RetrievedChunk } from '../types';

/**
 * Safety layer (M3/M5). Defense-in-depth against indirect prompt injection.
 * See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §6 and docs/04 §D.
 *  - spotlighting: mark all page-derived text as untrusted before it reaches a model
 *  - DOM sanitizer: down-weight hidden/off-task/freshly-injected elements
 *  - retrieved history is ALSO untrusted (cross-session stored injection)
 */

/** Wrap untrusted page/history text so the model can't confuse it with user instructions. */
export function spotlight(untrusted: string): string {
  // TODO(M5): datamarking/delimiting/encoding per Microsoft spotlighting.
  return `<<UNTRUSTED_CONTENT>>\n${untrusted}\n<<END_UNTRUSTED_CONTENT>>`;
}

/** Flag suspicious nodes (hidden, off-screen, freshly-injected) as deferral triggers. */
export function sanitizeNodes(nodes: AXNode[]): AXNode[] {
  // TODO(M5): score + down-weight; treat unexpected new UI as a deferral trigger.
  return nodes.filter((n) => !n.state?.includes('hidden'));
}

/** Retrieved history can carry text injected on a past visit — treat as untrusted too. */
export function guardRetrieved(chunks: RetrievedChunk[]): RetrievedChunk[] {
  // TODO(M5): re-apply spotlighting to retrieved chunks; segregate instruction-like text.
  return chunks;
}
