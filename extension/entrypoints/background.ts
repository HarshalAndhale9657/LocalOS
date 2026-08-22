/**
 * Groundwork service worker (MV3).
 * M1.1: open the side panel on toolbar click + a message-router stub.
 * Later: RAG pipeline, CDP observe/act orchestration, safety + calibration,
 * local/cloud escalation router. See ../../docs/02_TECHNICAL_ARCHITECTURE.md.
 */
import { createMemory, type MemoryStore } from '../lib/memory';

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

      // TODO(M1.2) OBSERVE — compressed a11y snapshot via CDP
      // TODO(M1.3) ACT — dispatch SAFE actions via CDP
      // TODO(M1.5) ANSWER — grounded QA via local model (Ollama)
      default:
        return false;
    }
  });

  console.log('[groundwork] background ready', { id: browser.runtime.id });
});
