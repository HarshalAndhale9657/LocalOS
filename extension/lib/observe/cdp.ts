/**
 * Thin Chrome DevTools Protocol (CDP) wrapper over chrome.debugger.
 * Callback-wrapped Promises so it works regardless of @types/chrome promise support.
 * Attaching keeps the MV3 service worker alive during agent loops (docs/02 §7).
 */
const attached = new Set<number>();
let detachListenerAdded = false;

function ensureDetachListener() {
  if (detachListenerAdded) return;
  detachListenerAdded = true;
  chrome.debugger.onDetach.addListener((src) => {
    if (src.tabId != null) attached.delete(src.tabId);
  });
}

export function ensureAttached(tabId: number): Promise<void> {
  ensureDetachListener();
  if (attached.has(tabId)) return Promise.resolve();
  return new Promise((resolve, reject) => {
    chrome.debugger.attach({ tabId }, '1.3', () => {
      const err = chrome.runtime.lastError;
      if (err && !/already attached/i.test(err.message ?? '')) return reject(new Error(err.message));
      attached.add(tabId);
      resolve();
    });
  });
}

export function detach(tabId: number): Promise<void> {
  if (!attached.has(tabId)) return Promise.resolve();
  return new Promise((resolve) => {
    chrome.debugger.detach({ tabId }, () => {
      attached.delete(tabId);
      void chrome.runtime.lastError; // ignore
      resolve();
    });
  });
}

export function sendCommand<T = any>(tabId: number, method: string, params?: Record<string, unknown>): Promise<T> {
  return new Promise((resolve, reject) => {
    chrome.debugger.sendCommand({ tabId }, method, params, (result) => {
      const err = chrome.runtime.lastError;
      if (err) return reject(new Error(err.message));
      resolve(result as T);
    });
  });
}

export const isAttached = (tabId: number) => attached.has(tabId);
