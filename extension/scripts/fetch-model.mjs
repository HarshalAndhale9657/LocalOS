/**
 * Fetch the embedding model into public/models/ so Groundwork embeds fully offline
 * (no Hugging Face Hub call at runtime — the local-first/privacy guarantee, docs/02 §4).
 * Model files are gitignored; run this once after `npm install`:
 *
 *   node scripts/fetch-model.mjs
 */
import { mkdir, writeFile, stat } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const MODEL = 'Xenova/bge-small-en-v1.5';
const BASE = `https://huggingface.co/${MODEL}/resolve/main/`;
const FILES = [
  'config.json',
  'tokenizer.json',
  'tokenizer_config.json',
  'special_tokens_map.json',
  'vocab.txt',
  'onnx/model_quantized.onnx',
];

const here = dirname(fileURLToPath(import.meta.url));
const outRoot = join(here, '..', 'public', 'models', MODEL);

async function exists(p) {
  try {
    await stat(p);
    return true;
  } catch {
    return false;
  }
}

async function fetchFile(rel) {
  const dest = join(outRoot, rel);
  if (await exists(dest)) {
    console.log(`  skip  ${rel} (already present)`);
    return;
  }
  await mkdir(dirname(dest), { recursive: true });
  const res = await fetch(BASE + rel);
  if (!res.ok) throw new Error(`${rel}: HTTP ${res.status}`);
  const buf = Buffer.from(await res.arrayBuffer());
  await writeFile(dest, buf);
  console.log(`  ok    ${rel}  (${(buf.length / 1024).toFixed(0)} KB)`);
}

console.log(`Fetching ${MODEL} -> public/models/`);
for (const f of FILES) await fetchFile(f);
console.log('Done. The model is now bundled for offline embedding.');
