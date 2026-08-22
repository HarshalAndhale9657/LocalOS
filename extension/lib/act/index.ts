import type { Action, ActionResult } from '../types';

/**
 * Action executor (M1.3). Executes SAFE actions via trusted CDP input events
 * (Input.dispatchMouseEvent / dispatchKeyEvent). Verifies the observation versionId
 * before acting; CAUTION/UNSAFE actions require confirmation.
 * See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §3.
 */
export interface Executor {
  execute(tabId: number, action: Action): Promise<ActionResult>;
}

/** Coarse risk classifier stub — replaced by the trained risk head in M4. */
export function classifyRisk(action: Action): Action['risk'] {
  if (action.verb === 'navigate' || action.verb === 'scroll' || action.verb === 'extract') return 'SAFE';
  if (action.verb === 'click') return 'CAUTION'; // refine: links = SAFE, submit-like = UNSAFE
  return 'CAUTION';
}

// TODO(M1.3): implement CDP dispatch + version-id guard + action log.
export function createExecutor(): Executor {
  throw new Error('not implemented — M1.3');
}
