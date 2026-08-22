/**
 * Core shared types for Groundwork.
 * These encode the architecture in ../../docs/02_TECHNICAL_ARCHITECTURE.md so the
 * observe / act / memory / model / safety modules stay consistent as they're built.
 */

// ---- Observe (M1.2) -------------------------------------------------------
export interface AXNode {
  index: number; // stable element index the action model refers to
  role: string; // button, link, textbox, heading, …
  name?: string; // accessible name
  value?: string;
  state?: string[]; // focused, disabled, hidden, …
  backendNodeId?: number; // CDP handle for the executor (stripped before the model sees it)
}

export interface Observation {
  goal: string;
  url: string;
  versionId: string; // snapshot version; executor verifies before acting
  nodes: AXNode[]; // compressed, on-task subset (~5–10% of the DOM)
  recentActions: ActionResult[];
  retrievedExemplars?: RetrievedChunk[]; // history-RAG-augmented grounding (RQ3)
}

// ---- Act (M1.3) -----------------------------------------------------------
export type Verb =
  | 'click'
  | 'type'
  | 'select'
  | 'scroll'
  | 'navigate'
  | 'open_tab'
  | 'switch_tab'
  | 'extract'
  | 'wait'
  | 'ask_user' // deferral
  | 'done';

export type RiskLabel = 'SAFE' | 'CAUTION' | 'UNSAFE';

export interface Action {
  verb: Verb;
  index?: number; // target element (for click/type/select)
  args?: Record<string, unknown>;
  versionId: string; // must match the observation the action was decided on
  risk: RiskLabel;
  confidence: number; // for calibrated deferral
}

export interface ActionResult {
  action: Action;
  ok: boolean;
  error?: string;
  at: number; // epoch ms
}

// ---- Memory (M1.4) --------------------------------------------------------
export interface RetrievedChunk {
  pageId: string;
  chunkId: string;
  url: string;
  title: string;
  readAt: string; // ISO — powers time-scoped + staleness
  text: string;
  score: number; // post-rerank
}

// ---- Model / answering (M1.5) --------------------------------------------
export interface Answer {
  decision: 'answer' | 'abstain'; // calibrated refusal
  text: string; // answer, or "not found in your history"
  citations: RetrievedChunk[];
  confidence: number;
}
