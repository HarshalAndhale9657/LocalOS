import { Readability } from '@mozilla/readability';

/**
 * Content script (M1.4 capture): extracts readable article text on demand.
 * (M1.2 will add the CDP accessibility-tree snapshot for the action model.)
 */
export default defineContentScript({
  matches: ['<all_urls>'],
  main() {
    browser.runtime.onMessage.addListener((msg: any, _sender, sendResponse) => {
      if (msg?.type !== 'CAPTURE_PAGE') return false;
      try {
        const clone = document.cloneNode(true) as Document;
        const article = new Readability(clone).parse();
        const text = (article?.textContent ?? document.body?.innerText ?? '').trim();
        sendResponse({ url: location.href, title: document.title, text });
      } catch (e: any) {
        sendResponse({
          url: location.href,
          title: document.title,
          text: (document.body?.innerText ?? '').trim(),
          error: String(e?.message ?? e),
        });
      }
      return true;
    });
  },
});
