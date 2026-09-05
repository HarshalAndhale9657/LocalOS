import type { Answer, RetrievedChunk, Observation, Action, Verb } from '../types';
import { guardRetrieved } from '../safety';
import { REFUSAL, qaSystemPrompt, qaUserPrompt, actionSystemPrompt, actionUserPrompt, isRefusal, citedIndices } from './core';

/**
 * Local model client (M1.5). Prompts + parsing come from ./core (shared with the benchmark harness). Talks to an Ollama sidecar over localhost
 * (set OLLAMA_ORIGINS to allow the extension origin). GGUF Q4_K_M models.
 * M1 uses a BASE model (no fine-tuning) to produce the paper's baseline; the
 * fine-tuned QA + action adapters slot in behind this same interface (M2+).
 * See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §5, docs/03 §6.
 */
export const DEFAULT_BASE_MODEL = 'qwen2.5:3b-instruct';
export const OLLAMA_URL = 'http://localhost:11434';

const ACTION_VERBS = new Set([
  'click', 'type', 'select', 'scroll', 'navigate', 'open_tab', 'switch_tab', 'extract', 'wait', 'ask_user', 'done',
]);


function parseAction(text: string): { verb: Verb; index?: number; args?: Record<string, unknown> } {
  const m = text.match(/\{[\s\S]*\}/);
  if (m) {
    try {
      const o = JSON.parse(m[0]);
      const verb = String(o.verb ?? '').toLowerCase();
      if (ACTION_VERBS.has(verb)) {
        const args: Record<string, unknown> = o.args && typeof o.args === 'object' ? o.args : {};
        if (o.reason && args.reason == null) args.reason = o.reason;
        return { verb: verb as Verb, index: typeof o.index === 'number' ? o.index : undefined, args };
      }
    } catch {
      /* fall through to a safe deferral */
    }
  }
  return { verb: 'ask_user', args: { question: 'I could not decide a safe next step from this page.' } };
}

export interface LocalModel {
  isAvailable(): Promise<boolean>;
  answer(question: string, chunks: RetrievedChunk[]): Promise<Answer>;
  /** Decide the next browser action from an observation (Track 1). */
  act(obs: Observation): Promise<Action>;
}

export function createLocalModel(model = DEFAULT_BASE_MODEL, url = OLLAMA_URL): LocalModel {
  async function chat(system: string, user: string): Promise<string> {
    const res = await fetch(`${url}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        stream: false,
        options: { temperature: 0 },
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: user },
        ],
      }),
    });
    if (!res.ok) throw new Error(`Ollama HTTP ${res.status}`);
    const data = await res.json();
    return String(data?.message?.content ?? '').trim();
  }

  return {
    async isAvailable() {
      try {
        const res = await fetch(`${url}/api/tags`);
        return res.ok;
      } catch {
        return false;
      }
    },

    async answer(question, rawChunks) {
      const chunks = guardRetrieved(rawChunks); // retrieved history is untrusted too
      if (!chunks.length) {
        return { decision: 'abstain', text: REFUSAL, citations: [], confidence: 1 };
      }
      const text = await chat(qaSystemPrompt(), qaUserPrompt(question, chunks));
      if (isRefusal(text)) return { decision: 'abstain', text: REFUSAL, citations: [], confidence: 1 };

      const cited = citedIndices(text)
        .map((n) => chunks[n - 1])
        .filter((c): c is RetrievedChunk => !!c);
      const topScore = chunks.reduce((m, c) => Math.max(m, c.score), 0);
      return {
        decision: 'answer',
        text,
        citations: cited.length ? cited : chunks.slice(0, 1),
        confidence: topScore,
      };
    },

    async act(obs) {
      const elements = obs.nodes
        .map((n) => `[${n.index}] ${n.role}${n.name ? ` "${n.name}"` : ''}${n.state && n.state.length ? ` (${n.state.join(',')})` : ''}`)
        .join('\n');
      const recent =
        (obs.recentActions ?? [])
          .slice(-4)
          .map((r) => `${r.action.verb}${r.action.index != null ? ` [${r.action.index}]` : ''} -> ${r.ok ? 'ok' : 'fail'}`)
          .join('\n') || '(none)';
      // element text is page-derived => untrusted; the shared template wraps it in the spotlight markers
      const user = actionUserPrompt({ goal: obs.goal, url: obs.url, elements, recent });
      const text = await chat(actionSystemPrompt(), user);
      const p = parseAction(text);
      return { verb: p.verb, index: p.index, args: p.args, versionId: obs.versionId, risk: 'SAFE', confidence: 1 };
    },
  };
}
