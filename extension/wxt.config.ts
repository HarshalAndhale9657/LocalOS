import { defineConfig } from 'wxt';

// Groundwork — privacy-first, local-first agentic browser assistant.
// See ../docs/02_TECHNICAL_ARCHITECTURE.md for the manifest/permission rationale.
export default defineConfig({
  modules: ['@wxt-dev/module-react'],
  manifest: {
    name: 'Groundwork',
    description:
      'Private, local-first research agent: sees and controls your browser, remembers what you read, and cites its sources — nothing leaves your device.',
    // Minimal-but-sufficient for M1. Narrow host_permissions before Web Store release.
    permissions: [
      'sidePanel',
      'tabs',
      'scripting',
      'storage',
      'activeTab',
      'debugger', // CDP observe/act channel (keeps the SW alive during agent loops)
      'offscreen', // hosts transformers.js embeddings + PGlite
    ],
    host_permissions: ['<all_urls>'], // DEV ONLY — scope down to the user's research sites before release
    side_panel: { default_path: 'sidepanel.html' },
    action: { default_title: 'Open Groundwork' },
    content_security_policy: {
      // wasm-unsafe-eval is required for transformers.js / PGlite WASM
      extension_pages: "script-src 'self' 'wasm-unsafe-eval'; object-src 'self';",
    },
  },
});
