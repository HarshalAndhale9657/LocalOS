import { useState } from 'react';
import './style.css';

type Msg = { role: 'user' | 'agent'; text: string; citations?: string[] };

/**
 * Groundwork side-panel chat shell (M1.1).
 * This is UI scaffolding only — wiring to the RAG memory + local model
 * lands in M1.4 / M1.5 (see ../../docs/06_M1_BUILD_PLAN.md).
 */
function App() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: 'agent',
      text:
        "Groundwork is set up. I'll answer from your own tabs and reading history and cite my sources — and I'll say \"not found in your history\" rather than guess. (Memory + model wiring: M1.4–M1.5.)",
    },
  ]);
  const [input, setInput] = useState('');

  function send() {
    const q = input.trim();
    if (!q) return;
    setMessages((m) => [
      ...m,
      { role: 'user', text: q },
      { role: 'agent', text: '(stub) grounded answering is wired in M1.5.' },
    ]);
    setInput('');
  }

  return (
    <div className="gw-root">
      <header className="gw-header">
        <span className="gw-logo">◆</span>
        <div>
          <div className="gw-title">Groundwork</div>
          <div className="gw-sub">private · local-first · cited</div>
        </div>
      </header>

      <main className="gw-thread">
        {messages.map((m, i) => (
          <div key={i} className={`gw-msg gw-${m.role}`}>
            <div className="gw-bubble">{m.text}</div>
            {m.citations?.length ? (
              <div className="gw-cites">
                {m.citations.map((c, j) => (
                  <a key={j} className="gw-cite" href={c} target="_blank">
                    source {j + 1}
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
              send();
            }
          }}
          placeholder="Ask about your tabs or reading history…"
          rows={2}
        />
        <button onClick={send}>Ask</button>
      </footer>
    </div>
  );
}

export default App;
