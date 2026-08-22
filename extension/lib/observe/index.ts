import type { Observation } from '../types';
import { ensureAttached, sendCommand, detach } from './cdp';
import { compressAX, computeVersionId, type RawAXNode } from './axtree';

/**
 * Observation layer (M1.2). Builds a compressed accessibility-tree snapshot of a tab
 * via CDP + assigns stable element indices + a change-detecting versionId. Text-first,
 * vision-optional. See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §2.
 */
export interface Observer {
  snapshot(tabId: number, goal: string): Promise<Observation>;
  release(tabId: number): Promise<void>;
}

export function createObserver(): Observer {
  return {
    async snapshot(tabId, goal) {
      await ensureAttached(tabId);
      await sendCommand(tabId, 'Accessibility.enable');
      const { nodes: raw } = await sendCommand<{ nodes: RawAXNode[] }>(tabId, 'Accessibility.getFullAXTree');
      const tab = await chrome.tabs.get(tabId);
      const url = tab.url ?? '';
      const nodes = compressAX(raw ?? []);
      return { goal, url, versionId: computeVersionId(nodes, url), nodes, recentActions: [] };
    },
    release(tabId) {
      return detach(tabId);
    },
  };
}
