import type { Action, ActionResult, Observation, RiskLabel } from '../types';
import { ensureAttached, sendCommand } from '../observe/cdp';

/**
 * Action executor (M1.3). Executes actions via CDP against the tab, mapping the
 * model's element INDEX -> the observation's backendNodeId -> a real interaction.
 * Guards: (1) the action's versionId must match the observation it was decided on
 * (no acting on a stale snapshot); (2) non-SAFE actions require explicit confirmation.
 * See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §3.
 */
export interface ExecuteOptions {
  confirmed?: boolean; // caller (UI) has approved a CAUTION/UNSAFE action
}
export type ExecuteResult = ActionResult & { needsConfirm?: boolean; risk: RiskLabel };

export interface Executor {
  execute(tabId: number, action: Action, obs: Observation, opts?: ExecuteOptions): Promise<ExecuteResult>;
}

/** Coarse risk classifier — replaced by the trained SAFE/CAUTION/UNSAFE head in M4. */
export function classifyRisk(action: Action, obs?: Observation): RiskLabel {
  switch (action.verb) {
    case 'navigate':
    case 'scroll':
    case 'extract':
    case 'wait':
    case 'ask_user':
    case 'done':
      return 'SAFE';
    case 'type':
    case 'select':
      return 'CAUTION';
    case 'click': {
      const node = obs?.nodes.find((n) => n.index === action.index);
      const name = (node?.name ?? '').toLowerCase();
      // submit-like / destructive clicks are the risky ones
      if (/\b(submit|buy|pay|delete|remove|confirm|send|checkout|place order)\b/.test(name)) return 'UNSAFE';
      return 'CAUTION';
    }
    default:
      return 'CAUTION';
  }
}

async function centerOf(tabId: number, backendNodeId: number): Promise<{ x: number; y: number } | null> {
  try {
    const { model } = await sendCommand<{ model: { content: number[] } }>(tabId, 'DOM.getBoxModel', {
      backendNodeId,
    });
    const q = model?.content;
    if (!q || q.length < 6) return null;
    return { x: (q[0]! + q[4]!) / 2, y: (q[1]! + q[5]!) / 2 };
  } catch {
    return null;
  }
}

async function clickAt(tabId: number, x: number, y: number) {
  await sendCommand(tabId, 'Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
  await sendCommand(tabId, 'Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await sendCommand(tabId, 'Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
}

export function createExecutor(): Executor {
  return {
    async execute(tabId, action, obs, opts) {
      const at = Date.now();
      const risk = classifyRisk(action, obs);
      const fail = (error: string, needsConfirm = false): ExecuteResult => ({ action, ok: false, error, at, risk, needsConfirm });

      // Guard 1: stale-snapshot protection
      if (action.versionId !== obs.versionId) return fail('stale snapshot: re-observe before acting');
      // Guard 2: confirmation for non-SAFE actions
      if (risk !== 'SAFE' && !opts?.confirmed) return fail(`${risk} action needs confirmation`, true);

      await ensureAttached(tabId);
      await sendCommand(tabId, 'DOM.enable');

      const node = action.index != null ? obs.nodes.find((n) => n.index === action.index) : undefined;

      try {
        switch (action.verb) {
          case 'navigate': {
            const url = action.args?.url as string | undefined;
            if (url) await chrome.tabs.update(tabId, { url });
            else await sendCommand(tabId, 'Runtime.evaluate', { expression: `history.${action.args?.dir === 'forward' ? 'forward' : 'back'}()` });
            break;
          }
          case 'scroll': {
            const dy = (action.args?.dy as number) ?? 600;
            await sendCommand(tabId, 'Runtime.evaluate', { expression: `window.scrollBy(0, ${dy})` });
            break;
          }
          case 'click': {
            if (!node?.backendNodeId) return fail('unknown element');
            const c = await centerOf(tabId, node.backendNodeId);
            if (!c) return fail('element has no box (hidden/offscreen?)');
            await clickAt(tabId, c.x, c.y);
            break;
          }
          case 'type': {
            if (!node?.backendNodeId) return fail('unknown element');
            await sendCommand(tabId, 'DOM.focus', { backendNodeId: node.backendNodeId }).catch(() => {});
            await sendCommand(tabId, 'Input.insertText', { text: String(action.args?.text ?? '') });
            break;
          }
          case 'wait':
          case 'ask_user':
          case 'done':
          case 'extract':
            // no-op at the executor level (handled by the agent loop / UI)
            break;
          default:
            return fail(`unsupported verb: ${action.verb}`);
        }
        return { action, ok: true, at, risk };
      } catch (e: any) {
        return fail(String(e?.message ?? e));
      }
    },
  };
}
