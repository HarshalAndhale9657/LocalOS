/**
 * Local embeddings via transformers.js (ONNX/WASM). Runs ONLY in the offscreen
 * document (docs/02 §4/§7). bge-small-en-v1.5 = 384-dim; mean-pooled + normalized.
 * (Matryoshka truncation to 128–256 dims is a future optimization.)
 */
import { pipeline } from '@huggingface/transformers';

export const EMBED_MODEL = 'Xenova/bge-small-en-v1.5';
export const EMBED_DIM = 384;

type Extractor = Awaited<ReturnType<typeof pipeline>>;
let extractorPromise: Promise<Extractor> | null = null;

function getExtractor(): Promise<Extractor> {
  if (!extractorPromise) {
    extractorPromise = pipeline('feature-extraction', EMBED_MODEL);
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
