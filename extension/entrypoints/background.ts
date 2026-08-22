/**
 * Groundwork service worker (MV3).
 * M1.1: open the side panel on toolbar click + a message-router stub.
 * Later: RAG pipeline, CDP observe/act orchestration, safety + calibration,
 * local/cloud escalation router. See ../../docs/02_TECHNICAL_ARCHITECTURE.md.
 */
import { createMemory, type MemoryStore } from '../lib/memory';
import { createObserver } from '../lib/observe';
import { forModel } from '../lib/observe/axtree';
import { createLocalModel } from '../lib/model';

async function askMemory(memory: MemoryStore, query: string, k = 5) {
  const model = createLocalModel();
  const chunks = await memory.retrieve(query, { k });
  try {
    const answer = await model.answer(query, chunks);
    return { answer };
  } catch (e: any) {
    // Ollama not running / unreachable -> degrade to retrieval-only, don't hallucinate
    return {
      answer: {
        decision: chunks.length ? 'answer' : 'abstain',
        text: chunks.length
          ? 'Local model unavailable (is Ollama running?). Showing the sources I retrieved from your history:'
          : 'Not found in your history.',
        citations: chunks,
        confidence: 0,
      },
      modelError: String(e?.message ?? e),
    };
  }
}

async function observeActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return { error: 'no active tab' };
  const obs = await createObserver().snapshot(tab.id, '');
  // return a compact summary (executor-only fields stripped) for verification
  return { url: obs.url, versionId: obs.versionId, nodeCount: obs.nodes.length, sample: forModel(obs.nodes).slice(0, 10) };
}

async function captureActiveTab(memory: MemoryStore) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return { error: 'no active tab' };
  const page: any = await chrome.tabs.sendMessage(tab.id, { type: 'CAPTURE_PAGE' });
  if (!page?.text) return { error: 'could not read page' };
  const res = await memory.index(page);
  return { page: { url: page.url, title: page.title }, ...res };
}

export default defineBackground(() => {
  const memory = createMemory();

  // Open the side panel when the toolbar icon is clicked.
  // (chrome.sidePanel isn't in the webextension-polyfill surface, so use chrome.*)
  try {
    chrome.sidePanel?.setPanelBehavior({ openPanelOnActionClick: true });
  } catch (e) {
    console.warn('[groundwork] sidePanel behavior not set', e);
  }

  // Message router stub — the single entry point for panel <-> worker <-> content.
  browser.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    switch (message?.type) {
      case 'PING':
        sendResponse({ ok: true, from: 'background', id: browser.runtime.id });
        return true;

      case 'CAPTURE_ACTIVE_TAB': // read the active tab (Readability) + index into memory
        captureActiveTab(memory)
          .then(sendResponse)
          .catch((e) => sendResponse({ error: String(e?.message ?? e) }));
        return true;

      case 'ASK': // retrieve from memory -> grounded, cited answer (or calibrated refusal)
        askMemory(memory, message.query, message.opts?.k)
          .then(sendResponse)
          .catch((e) => sendResponse({ error: String(e?.message ?? e) }));
        return true;

      case 'MEMORY_RETRIEVE':
        memory
          .retrieve(message.query, message.opts)
          .then((chunks) => sendResponse({ chunks }))
          .catch((e) => sendResponse({ error: String(e?.message ?? e) }));
        return true;

      case 'MEMORY_WIPE':
        memory
          .wipe()
          .then(() => sendResponse({ ok: true }))
          .catch((e) => sendResponse({ error: String(e?.message ?? e) }));
        return true;

      case 'OBSERVE_ACTIVE_TAB': // CDP accessibility-tree snapshot of the active tab
        observeActiveTab()
          .then(sendResponse)
          .catch((e) => sendResponse({ error: String(e?.message ?? e) }));
        return true;

      // TODO(M1.3) ACT — dispatch SAFE actions via CDP (uses observation.backendNodeId)
      // TODO(M1.5) ANSWER — grounded QA via local model (Ollama)
      default:
        return false;
    }
  });

  console.log('[groundwork] background ready', { id: browser.runtime.id });
});
