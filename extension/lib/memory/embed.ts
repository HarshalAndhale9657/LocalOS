/**
 * Local embeddings via transformers.js (ONNX/WASM). Runs ONLY in the offscreen
 * document (docs/02 §4/§7). bge-small-en-v1.5 = 384-dim; mean-pooled + normalized.
 * (Matryoshka truncation to 128–256 dims is a future optimization.)
 */
import { pipeline, env } from '@huggingface/transformers';

export const EMBED_MODEL = 'Xenova/bge-small-en-v1.5';
export const EMBED_DIM = 384;

// Fully-local model loading: no Hugging Face Hub call at runtime (privacy/offline).
// Model files are bundled under the packaged extension at /models/<id>/ via
// `node scripts/fetch-model.mjs`. See docs/02 §4.
env.allowRemoteModels = false;
env.allowLocalModels = true;
try {
  // offscreen doc has chrome.runtime — resolve the packaged models dir absolutely
  env.localModelPath = (globalThis as any).chrome?.runtime?.getURL?.('models/') ?? 'models/';
} catch {
  env.localModelPath = 'models/';
}

type Extractor = Awaited<ReturnType<typeof pipeline>>;
let extractorPromise: Promise<Extractor> | null = null;

function getExtractor(): Promise<Extractor> {
  if (!extractorPromise) {
    // dtype 'q8' -> loads onnx/model_quantized.onnx (the file we bundle)
    extractorPromise = pipeline('feature-extraction', EMBED_MODEL, { dtype: 'q8' });
  }
  return extractorPromise;
}

/** Embed a batch of texts -> array of normalized 384-d vectors. */
export async function embed(texts: string[]): Promise<number[][]> {
  if (!texts.length) return [];
  const extractor = await getExtractor();
  const out: any = await (extractor as any)(texts, { pooling: 'mean', normalize: true });
  return out.tolist() as number[][];
}

export async function embedOne(text: string): Promise<number[]> {
  return (await embed([text]))[0] ?? [];
}
