import { describe, it, expect } from 'vitest';
import vectors from '../../../shared/tests/refusal_cases.json';
import { isRefusal, citedIndices, qaSystemPrompt, qaUserPrompt, REFUSAL } from './core';

describe('shared behaviour vectors (same file as benchmark/tests/test_core.py)', () => {
  it('refusal detection', () => {
    for (const c of vectors.refusal) expect(isRefusal(c.text), JSON.stringify(c.text)).toBe(c.is_refusal);
  });
  it('citation extraction', () => {
    for (const c of vectors.citations) expect(citedIndices(c.text), c.text).toEqual(c.cited);
  });
  it('prompt rendering', () => {
    const sys = qaSystemPrompt();
    expect(sys).toContain(REFUSAL);
    expect(sys).not.toContain('{refusal}');
    const user = qaUserPrompt('What is X?', [
      { title: 'T1', readAt: '2026-07-14T09:12:00Z', text: 'alpha' },
      { url: 'https://u', readAt: '2026-07-15', text: 'beta' },
    ]);
    expect(user).toContain('[1] (T1, read 2026-07-14)');
    expect(user).toContain('[2] (https://u, read 2026-07-15)');
    expect(user).toContain('<<UNTRUSTED_CONTENT>>\nalpha\n<<END_UNTRUSTED_CONTENT>>');
    expect(user.startsWith('Question: What is X?')).toBe(true);
  });
});
