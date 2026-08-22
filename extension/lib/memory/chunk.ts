/**
 * Recursive chunker (~400–512 tokens, no overlap) — mirrors the benchmark builder
 * (benchmark/pmrgb/chunk.py) and docs/02 §4. Token count approximated by whitespace.
 */
export interface Chunk {
  chunkId: string;
  text: string;
  offset: [number, number];
}

const ntok = (s: string) => (s.match(/\S+/g)?.length ?? 0);

export function chunkText(text: string, target = 480, hardMax = 512): Chunk[] {
  const paras = text.split('\n').map((p) => p.trim()).filter(Boolean);
  const chunks: Chunk[] = [];
  let buf: string[] = [];
  let bufTok = 0;
  let cursor = 0;

  const flush = () => {
    if (!buf.length) return;
    const body = buf.join('\n');
    let start = text.indexOf(buf[0]!, cursor);
    if (start < 0) start = cursor;
    const end = start + body.length;
    chunks.push({ chunkId: `c_${chunks.length}`, text: body, offset: [start, end] });
    cursor = end;
    buf = [];
    bufTok = 0;
  };

  for (const p of paras) {
    const pt = ntok(p);
    if (bufTok + pt > hardMax && buf.length) flush();
    buf.push(p);
    bufTok += pt;
    if (bufTok >= target) flush();
  }
  flush();
  return chunks.length ? chunks : [{ chunkId: 'c_0', text, offset: [0, text.length] }];
}
