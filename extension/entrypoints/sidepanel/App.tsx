import { useEffect, useRef, useState } from 'react';
import './style.css';

type Cite = { url: string; title: string; readAt: string; text: string; score: number };
type Msg = { role: 'user' | 'agent'; text: string; citations?: Cite[]; log?: boolean };
type Confirm = {
  id: string;
  action: { verb: string; index?: number; args?: Record<string, unknown>; risk: string };
  target: { role: string; name?: string } | null;
};

/**
 * Groundwork side panel (M1.4 + M1.5). Two modes:
 *  - Ask: grounded QA over your memory (cited answer / "not found in your history")
 *  - Do:  agentic task loop — the model decides browser actions; risky ones need your OK.
 * Grounded answering + actions both run on the local model (Ollama); see docs/02 §3/§5.
 */
function App() {
  const [messages, setMessages] = useState<Msg[]>([
    { role: 'agent', text: 'Remember a few pages, then Ask about them — or switch to Do and give me a task on the current page. Risky actions always ask you first.' },
  ]);
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<'ask' | 'do'>('ask');
  const [busy, setBusy] = useState(false);
  const [taskRunning, setTaskRunning] = useState(false);
  const [confirm, setConfirm] = useState<Confirm | null>(null);
  const threadRef = useRef<HTMLDivElement>(null);

  const append = (m: Msg) => setMessages((prev) => [...prev, m]);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight });
  }, [messages, confirm]);

  // Listen for the agent's streamed events + confirmation requests.
  useEffect(() => {
    const onMsg = (msg: any) => {
      if (msg?.type === 'AGENT_EVENT') {
        const e = msg.event;
        append({ role: 'agent', text: eventToText(e), log: e.kind !== 'done' && e.kind !== 'ask' });
        if (e.kind === 'done' || e.kind === 'error' || e.kind === 'ask') setTaskRunning(false);
      } else if (msg?.type === 'CONFIRM_ACTION') {
        setConfirm({ id: msg.id, action: msg.action, target: msg.target });
      }
    };
    chrome.runtime.onMessage.addListener(onMsg);
    return () => chrome.runtime.onMessage.removeListener(onMsg);
  }, []);

  async function remember() {
    setBusy(true);
    try {
      const r: any = await chrome.runtime.sendMessage({ type: 'CAPTURE_ACTIVE_TAB' });
      append({
        role: 'agent',
        text: r?.error
          ? `Couldn't capture this tab: ${r.error}`
          : r?.indexed
            ? `Remembered "${r.page?.title || r.page?.url}" (${r.chunks} chunks).`
            : `Skipped "${r.page?.title || r.page?.url}" (${r.reason || 'not indexed'}).`,
      });
    } finally {
      setBusy(false);
    }
  }

  async function ask(q: string) {
    setBusy(true);
    try {
      const r: any = await chrome.runtime.sendMessage({ type: 'ASK', query: q, opts: { k: 4 } });
      if (r?.error) append({ role: 'agent', text: `Error: ${r.error}` });
      else {
        const a = r?.answer ?? {};
        const cites: Cite[] = a.decision === 'abstain' ? [] : a.citations ?? [];
        append({ role: 'agent', text: a.text || 'Not found in your history.', citations: cites });
      }
    } finally {
      setBusy(false);
    }
  }

  async function runTask(goal: string) {
    setTaskRunning(true);
    const r: any = await chrome.runtime.sendMessage({ type: 'RUN_TASK', goal });
    if (r?.error) {
      append({ role: 'agent', text: `Couldn't start: ${r.error}` });
      setTaskRunning(false);
    }
  }

  function submit() {
    const q = input.trim();
    if (!q || busy || taskRunning) return;
    setInput('');
    append({ role: 'user', text: q });
    if (mode === 'ask') void ask(q);
    else void runTask(q);
  }

  function decide(approved: boolean) {
    if (!confirm) return;
    void chrome.runtime.sendMessage({ type: 'CONFIRM_RESULT', id: confirm.id, approved });
    setConfirm(null);
  }

  function cancel() {
    void chrome.runtime.sendMessage({ type: 'CANCEL_TASK' });
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
          + Remember
        </button>
      </header>

      <div className="gw-modes">
        <button className={mode === 'ask' ? 'gw-mode active' : 'gw-mode'} onClick={() => setMode('ask')} disabled={taskRunning}>
          Ask
        </button>
        <button className={mode === 'do' ? 'gw-mode active' : 'gw-mode'} onClick={() => setMode('do')} disabled={taskRunning}>
          Do
        </button>
      </div>

      <main className="gw-thread" ref={threadRef}>
        {messages.map((m, i) => (
          <div key={i} className={`gw-msg gw-${m.role}${m.log ? ' gw-logline' : ''}`}>
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

      {confirm ? (
        <div className="gw-confirm">
          <div className="gw-confirm-title">
            Approve this <span className={`gw-risk gw-risk-${confirm.action.risk.toLowerCase()}`}>{confirm.action.risk}</span> action?
          </div>
          <div className="gw-confirm-body">
            <b>{confirm.action.verb}</b>
            {confirm.action.index != null ? ` [${confirm.action.index}]` : ''}
            {confirm.target?.name ? ` → "${confirm.target.name}"` : confirm.target ? ` → ${confirm.target.role}` : ''}
            {typeof confirm.action.args?.text === 'string' ? ` — "${confirm.action.args.text}"` : ''}
          </div>
          <div className="gw-confirm-actions">
            <button className="gw-approve" onClick={() => decide(true)}>Approve</button>
            <button className="gw-reject" onClick={() => decide(false)}>Reject</button>
          </div>
        </div>
      ) : null}

      <footer className="gw-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder={mode === 'ask' ? 'Ask about your captured pages…' : 'Give me a task on this page…'}
          rows={2}
          disabled={busy || taskRunning}
        />
        {taskRunning ? (
          <button className="gw-cancel" onClick={cancel}>Stop</button>
        ) : (
          <button onClick={submit} disabled={busy}>{busy ? '…' : mode === 'ask' ? 'Ask' : 'Run'}</button>
        )}
      </footer>
    </div>
  );
}

function eventToText(e: any): string {
  switch (e.kind) {
    case 'plan':
      return "On it — I'll work step by step.";
    case 'observe':
      return `· step ${e.step}: read the page (${e.nodeCount} elements)`;
    case 'action':
      return `→ ${e.verb}${e.index != null ? ` [${e.index}]` : ''}${e.reason ? ` — ${e.reason}` : ''}`;
    case 'result':
      return `${e.ok ? '✓' : '✗'} ${e.verb}${e.note ? ` — ${e.note}` : ''}`;
    case 'ask':
      return `❓ ${e.question}`;
    case 'done':
      return `✅ ${e.text}`;
    case 'error':
      return `⚠️ ${e.error}`;
    default:
      return JSON.stringify(e);
  }
}

export default App;
