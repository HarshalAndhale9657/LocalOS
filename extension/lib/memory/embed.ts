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
const extUrl = (p: string): string => {
  try {
    return (globalThis as any).chrome?.runtime?.getURL?.(p) ?? p;
  } catch {
    return p;
  }
};
// offscreen doc has chrome.runtime — resolve the packaged models dir absolutely
env.localModelPath = extUrl('models/');
// The ONNX runtime's WASM engine must ALSO come from the bundle: by default onnxruntime-web
// dynamically imports it from a CDN, which the extension CSP blocks ("no available backend
// found" — caught by e2e/smoke.mjs on 2026-09-06). `npm run fetch-model` copies the engine
// files into public/ort/. Single-threaded: the offscreen document is not cross-origin
// isolated, so SharedArrayBuffer (needed for threads) is unavailable.
const onnx = (env.backends as any)?.onnx;
if (onnx?.wasm) {
  onnx.wasm.wasmPaths = extUrl('ort/');
  onnx.wasm.numThreads = 1;
  onnx.wasm.proxy = false;
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
