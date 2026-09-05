/**
 * Shared core (TypeScript side): prompt loading/rendering + refusal/citation parsing.
 * Mirrors benchmark/pmrgb/core.py exactly; both are checked against the same behaviour
 * vectors in shared/tests/refusal_cases.json so the paper measures the product's prompt and
 * parser (docs/07 §10.1). Prompts are bundled verbatim from ../../../shared/prompts via `?raw`.
 */
import refusalRaw from '../../../shared/prompts/refusal.txt?raw';
import qaSystemRaw from '../../../shared/prompts/grounded_qa.system.txt?raw';
import qaUserRaw from '../../../shared/prompts/grounded_qa.user.txt?raw';
import sourceItemRaw from '../../../shared/prompts/source_item.txt?raw';
import actionSystemRaw from '../../../shared/prompts/action_decide.system.txt?raw';
import actionUserRaw from '../../../shared/prompts/action_decide.user.txt?raw';
import versionRaw from '../../../shared/prompts/version.txt?raw';

export const REFUSAL = refusalRaw.trim();
export const PROMPT_VERSION = versionRaw.trim();

/** Plain `{name}` substitution; no format semantics so braces in prompts are safe. */
export function render(template: string, vars: Record<string, string>): string {
  let out = template;
  for (const [k, v] of Object.entries(vars)) out = out.split(`{${k}}`).join(v);
  return out;
}

export function qaSystemPrompt(): string {
  return render(qaSystemRaw, { refusal: REFUSAL }).trim();
}

export interface SourceLike {
  title?: string;
  url?: string;
  readAt: string;
  text: string;
}

/** Sources in citation order; numbered 1-based in the prompt. */
export function qaUserPrompt(question: string, sources: SourceLike[]): string {
  const itemT = sourceItemRaw.replace(/\n+$/, '');
  const items = sources.map((s, i) =>
    render(itemT, { n: String(i + 1), title: s.title || s.url || '', read_at: s.readAt.slice(0, 10), text: s.text }),
  );
  return render(qaUserRaw, { question, sources: items.join('\n\n') }).trim();
}

export function actionSystemPrompt(): string {
  return actionSystemRaw.trim();
}

export function actionUserPrompt(vars: { goal: string; url: string; elements: string; recent: string }): string {
  return render(actionUserRaw, vars).trim();
}

const escapeRe = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const REFUSAL_RE = new RegExp(escapeRe(REFUSAL.replace(/\.$/, '')) + '\\.?', 'i');

/**
 * Strict rule (shared vectors): the refusal string, period optional, case-insensitive, with at
 * most 7 extra characters of padding/quotes. Refusal-then-content is NOT a refusal.
 */
export function isRefusal(text: string): boolean {
  const t = text.trim();
  return REFUSAL_RE.test(t) && t.length < REFUSAL.length + 8;
}

/** Distinct 1-based citation numbers in first-appearance order. */
export function citedIndices(text: string): number[] {
  const seen: number[] = [];
  for (const m of text.matchAll(/\[(\d+)\]/g)) {
    const n = Number(m[1]);
    if (!seen.includes(n)) seen.push(n);
  }
  return seen;
}
