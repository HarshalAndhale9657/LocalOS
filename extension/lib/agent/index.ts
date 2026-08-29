/**
 * Agentic task loop (M1.5 action half). Ties together observe -> decide -> confirm ->
 * act -> re-observe. Runs in the service worker; streams AGENT_EVENT messages to the side
 * panel and pauses for human confirmation on non-SAFE actions.
 * See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §3, docs/01 §5.
 */
import { createObserver } from '../observe';
import { createExecutor, classifyRisk } from '../act';
import { createLocalModel } from '../model';
import type { Action, ActionResult, Observation } from '../types';

export type AgentEvent =
  | { kind: 'plan'; goal: string }
  | { kind: 'observe'; url: string; nodeCount: number; step: number }
  | { kind: 'action'; verb: string; index?: number; risk: string; reason?: string }
  | { kind: 'result'; verb: string; ok: boolean; note?: string }
  | { kind: 'ask'; question: string }
  | { kind: 'done'; text: string }
  | { kind: 'error'; error: string };

function broadcast(msg: Record<string, unknown>) {
  try {
    void chrome.runtime.sendMessage(msg).catch(() => {}); // fire-and-forget to the panel
  } catch {
    /* no receiver — ignore */
  }
}
const emit = (event: AgentEvent) => broadcast({ type: 'AGENT_EVENT', event });

const pendingConfirms = new Map<string, (approved: boolean) => void>();
let confirmCounter = 0;
let canceled = false;
let running = false;

export function isRunning() {
  return running;
}
export function cancelTask() {
  canceled = true;
}
export function resolveConfirm(id: string, approved: boolean) {
  const r = pendingConfirms.get(id);
  if (r) {
    pendingConfirms.delete(id);
    r(approved);
  }
}

function requestConfirm(action: Action, obs: Observation): Promise<boolean> {
  const id = `cfm_${++confirmCounter}`;
  const node = obs.nodes.find((n) => n.index === action.index);
  broadcast({
    type: 'CONFIRM_ACTION',
    id,
    action: { verb: action.verb, index: action.index, args: action.args, risk: action.risk },
    target: node ? { role: node.role, name: node.name } : null,
  });
  return new Promise((resolve) => pendingConfirms.set(id, resolve));
}

export async function runTask(goal: string, tabId: number, modelName?: string, maxSteps = 8): Promise<void> {
  if (running) {
    emit({ kind: 'error', error: 'A task is already running.' });
    return;
  }
  running = true;
  canceled = false;
  const observer = createObserver();
  const executor = createExecutor();
  const model = createLocalModel(modelName);
  const recent: ActionResult[] = [];

  emit({ kind: 'plan', goal });
  try {
    for (let step = 0; step < maxSteps; step++) {
      if (canceled) {
        emit({ kind: 'done', text: 'Task canceled.' });
        return;
      }

      const obs = await observer.snapshot(tabId, goal);
      obs.recentActions = recent;
      emit({ kind: 'observe', url: obs.url, nodeCount: obs.nodes.length, step: step + 1 });

      const action = await model.act(obs);
      action.risk = classifyRisk(action, obs);
      const reason = typeof action.args?.reason === 'string' ? action.args.reason : undefined;
      emit({ kind: 'action', verb: action.verb, index: action.index, risk: action.risk, reason });

      if (action.verb === 'done') {
        emit({ kind: 'done', text: String(action.args?.answer ?? 'Done.') });
        return;
      }
      if (action.verb === 'ask_user') {
        emit({ kind: 'ask', question: String(action.args?.question ?? 'I need your guidance to continue.') });
        return;
      }
      if (action.risk !== 'SAFE') {
        const approved = await requestConfirm(action, obs);
        if (!approved) {
          emit({ kind: 'result', verb: action.verb, ok: false, note: 'declined' });
          return;
        }
      }

      const res = await executor.execute(tabId, action, obs, { confirmed: true });
      recent.push(res);
      emit({ kind: 'result', verb: action.verb, ok: res.ok, note: res.error });
      // on a stale snapshot, just loop and re-observe
    }
    emit({ kind: 'done', text: 'Reached the step limit — stopping.' });
  } catch (e: any) {
    emit({ kind: 'error', error: String(e?.message ?? e) });
  } finally {
    running = false;
  }
}
