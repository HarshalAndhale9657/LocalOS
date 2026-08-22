/**
 * Groundwork service worker (MV3).
 * M1.1: open the side panel on toolbar click + a message-router stub.
 * Later: RAG pipeline, CDP observe/act orchestration, safety + calibration,
 * local/cloud escalation router. See ../../docs/02_TECHNICAL_ARCHITECTURE.md.
 */
export default defineBackground(() => {
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
      // TODO(M1.2) OBSERVE  — capture compressed a11y snapshot of the active tab
      // TODO(M1.3) ACT      — dispatch a SAFE action via CDP, append to action log
      // TODO(M1.4) MEMORY   — index a page / retrieve chunks
      // TODO(M1.5) ANSWER   — grounded QA with citations or calibrated refusal
      default:
        return false;
    }
  });

  console.log('[groundwork] background ready', { id: browser.runtime.id });
});
