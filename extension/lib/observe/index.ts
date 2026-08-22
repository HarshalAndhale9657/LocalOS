import type { Observation } from '../types';

/**
 * Observation layer (M1.2). Builds a compressed accessibility-tree snapshot of the
 * active tab via CDP (Accessibility.getFullAXTree / DOMSnapshot) + Readability text,
 * assigns stable element indices + a versionId. Text-first, vision-optional.
 * See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §2.
 */
export interface Observer {
  snapshot(tabId: number, goal: string): Promise<Observation>;
}

// TODO(M1.2): implement CDP attach + a11y tree pull + budget-aware compression.
export function createObserver(): Observer {
  throw new Error('not implemented — M1.2');
}
