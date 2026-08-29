import { useEffect, useState } from 'react';
import type { Settings } from '../../lib/settings';

/**
 * Settings & privacy panel (docs/01 §5). Reads/writes settings via the background
 * (chrome.storage), edits the sensitive-domain blocklist, picks the local model, and
 * offers a one-click memory wipe.
 */
export default function SettingsView({ onClose }: { onClose: () => void }) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [blocklistText, setBlocklistText] = useState('');
  const [status, setStatus] = useState<string>('');
  const [wipeArmed, setWipeArmed] = useState(false);

  useEffect(() => {
    chrome.runtime.sendMessage({ type: 'GET_SETTINGS' }).then((r: any) => {
      if (r?.settings) {
        setSettings(r.settings);
        setBlocklistText((r.settings.blocklist ?? []).join('\n'));
      }
    });
  }, []);

  function patch(p: Partial<Settings>) {
    setSettings((s) => (s ? { ...s, ...p } : s));
    setStatus('');
  }

  async function save() {
    if (!settings) return;
    const blocklist = blocklistText
      .split('\n')
      .map((l) => l.trim())
      .filter(Boolean);
    setStatus('Saving…');
    const r: any = await chrome.runtime.sendMessage({ type: 'SAVE_SETTINGS', settings: { ...settings, blocklist } });
    setStatus(r?.error ? `Error: ${r.error}` : 'Saved.');
  }

  async function wipe() {
    if (!wipeArmed) {
      setWipeArmed(true);
      return;
    }
    setStatus('Wiping…');
    const r: any = await chrome.runtime.sendMessage({ type: 'MEMORY_WIPE' });
    setWipeArmed(false);
    setStatus(r?.error ? `Error: ${r.error}` : 'Memory wiped.');
  }

  if (!settings) {
    return (
      <div className="gw-settings">
        <div className="gw-set-loading">Loading settings…</div>
      </div>
    );
  }

  return (
    <div className="gw-settings">
      <div className="gw-set-head">
        <button className="gw-back" onClick={onClose} aria-label="Back">‹ Back</button>
        <span className="gw-set-title">Settings & Privacy</span>
      </div>

      <section className="gw-set-section">
        <label className="gw-set-row">
          <input
            type="checkbox"
            checked={settings.captureEnabled}
            onChange={(e) => patch({ captureEnabled: e.target.checked })}
          />
          <span>Allow capturing pages into memory</span>
        </label>
        <p className="gw-set-hint">When off, "Remember" won't index anything. Blocked domains are never captured regardless.</p>
      </section>

      <section className="gw-set-section">
        <div className="gw-set-label">Local model (Ollama)</div>
        <input
          className="gw-set-input"
          value={settings.model}
          onChange={(e) => patch({ model: e.target.value })}
          placeholder="qwen2.5:7b-instruct"
          spellCheck={false}
        />
        <p className="gw-set-hint">Must be pulled in Ollama (e.g. <code>ollama pull qwen2.5:7b-instruct</code>).</p>
      </section>

      <section className="gw-set-section">
        <div className="gw-set-label">Sensitive-domain blocklist</div>
        <textarea
          className="gw-set-textarea"
          value={blocklistText}
          onChange={(e) => setBlocklistText(e.target.value)}
          rows={8}
          spellCheck={false}
        />
        <p className="gw-set-hint">One URL fragment per line (domain or path). Any page whose URL contains a fragment is never captured.</p>
      </section>

      <div className="gw-set-actions">
        <button className="gw-save" onClick={save}>Save</button>
        {status ? <span className="gw-set-status">{status}</span> : null}
      </div>

      <section className="gw-set-danger">
        <div className="gw-set-label">Danger zone</div>
        <button className={wipeArmed ? 'gw-wipe armed' : 'gw-wipe'} onClick={wipe}>
          {wipeArmed ? 'Click again to confirm — wipe everything' : 'Wipe all memory'}
        </button>
        {wipeArmed ? (
          <button className="gw-wipe-cancel" onClick={() => setWipeArmed(false)}>Cancel</button>
        ) : null}
        <p className="gw-set-hint">Permanently deletes the local index of everything you've captured. Cannot be undone.</p>
      </section>
    </div>
  );
}
