import type { Answer, RetrievedChunk, Observation, Action } from '../types';

/**
 * Local model client (M1.5). Talks to an Ollama sidecar over localhost
 * (set OLLAMA_ORIGINS to allow the extension origin). GGUF Q4_K_M models.
 * M1 uses a BASE model (no fine-tuning) to produce the paper's baseline.
 * See ../../../docs/02_TECHNICAL_ARCHITECTURE.md §5 and docs/03 §6.
 */
export interface LocalModel {
  /** Grounded QA with inline citations, or a calibrated "not found in your history". */
  answer(question: string, chunks: RetrievedChunk[]): Promise<Answer>;
  /** Next browser action from an observation (Track 1 — wired in M4). */
  act?(obs: Observation): Promise<Action>;
}

export const DEFAULT_BASE_MODEL = 'qwen2.5:7b-instruct';
export const OLLAMA_URL = 'http://localhost:11434';

// TODO(M1.5): implement the Ollama chat call + citation/refusal prompt template.
export function createLocalModel(_model = DEFAULT_BASE_MODEL): LocalModel {
  throw new Error('not implemented — M1.5');
}
