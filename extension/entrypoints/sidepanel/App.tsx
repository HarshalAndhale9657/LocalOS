import { useState } from 'react';
import './style.css';

type Cite = { url: string; title: string; readAt: string; text: string; score: number };
type Msg = { role: 'user' | 'agent'; text: string; citations?: Cite[] };

/**
 * Groundwork side panel (M1.4). Wired to the local RAG memory:
 *  - "Remember this page" -> capture (Readability) + index into PGlite/pgvector
 *  - "Ask" -> retrieve grounded chunks from your history
 * Grounded ANSWER generation (a local model composing a cited reply / refusal)
 * lands in M1.5; for now we surface the retrieved evidence directly.
 */
function App() {
  const [messages, setMessages] = useState<Msg[]>([
    { role: 'agent', text: "Remember a few pages, then ask about them. I'll answer only from what you've captured — and say \"not found in your history\" when there's no support. (Cited answer generation: M1.5.)" },
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);

  async function remember() {
    setBusy(true);
    try {
      const r: any = await chrome.runtime.sendMessage({ type: 'CAPTURE_ACTIVE_TAB' });
      const note = r?.error
        ? `Couldn't capture this tab: ${r.error}`
        : r?.indexed
          ? `Remembered "${r.page?.title || r.page?.url}" (${r.chunks} chunks).`
          : `Skipped "${r.page?.title || r.page?.url}" (${r.reason || 'not indexed'}).`;
      setMessages((m) => [...m, { role: 'agent', text: note }]);
    } finally {
      setBusy(false);
    }
  }

  async function ask() {
    const q = input.trim();
    if (!q || busy) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', text: q }]);
    setBusy(true);
    try {
      const r: any = await chrome.runtime.sendMessage({ type: 'ASK', query: q, opts: { k: 4 } });
      if (r?.error) {
        setMessages((m) => [...m, { role: 'agent', text: `Error: ${r.error}` }]);
      } else {
        const a = r?.answer ?? {};
        const cites: Cite[] = a.decision === 'abstain' ? [] : a.citations ?? [];
        setMessages((m) => [...m, { role: 'agent', text: a.text || 'Not found in your history.', citations: cites }]);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="gw-root">
      <header className="gw-header">
        <span className="gw-logo">◆</span>
        <div>
          <div className="gw-title">Groundwork</div>
          <div className="gw-sub">private · local-first · cited</div>
        </div>
        <button className="gw-remember" onClick={remember} disabled={busy} title="Capture & index the active tab">
          + Remember page
        </button>
      </header>

      <main className="gw-thread">
        {messages.map((m, i) => (
          <div key={i} className={`gw-msg gw-${m.role}`}>
            <div className="gw-bubble">{m.text}</div>
            {m.citations?.length ? (
              <div className="gw-cites">
                {m.citations.map((c, j) => (
                  <a key={j} className="gw-cite" href={c.url} target="_blank" title={c.text}>
                    {j + 1}. {c.title || c.url} · {(c.score * 100).toFixed(0)}%
                  </a>
                ))}
              </div>
            ) : null}
          </div>
        ))}
      </main>

      <footer className="gw-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              ask();
            }
          }}
          placeholder="Ask about your captured pages…"
          rows={2}
          disabled={busy}
        />
        <button onClick={ask} disabled={busy}>{busy ? '…' : 'Ask'}</button>
      </footer>
    </div>
  );
}

export default App;
