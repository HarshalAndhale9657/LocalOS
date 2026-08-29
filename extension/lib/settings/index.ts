/**
 * User settings + privacy controls, persisted in chrome.storage.local.
 * Single source of truth for: whether capture is allowed, the sensitive-domain
 * blocklist that gates it, and which local model to use. See docs/01 §5, docs/02 §6.3.
 */

export interface Settings {
  /** Master switch for writing pages into the local memory index. */
  captureEnabled: boolean;
  /** URL substrings that must NEVER be captured (sensitive domains + paths). */
  blocklist: string[];
  /** Ollama model name used for grounded answering and the agent loop. */
  model: string;
}

/** Conservative default blocklist — banking, webmail, health, messaging, password managers. */
export const DEFAULT_BLOCKLIST: string[] = [
  // banking / finance
  'paypal.com', 'chase.com', 'wellsfargo.com', 'bankofamerica.com', 'citi.com', '.bank/',
  // webmail
  'mail.google.com', 'outlook.office', 'outlook.live', 'mail.yahoo.', 'mail.proton',
  // health
  'mychart', '.health/', 'patient',
  // messaging
  'web.whatsapp.com', 'web.telegram.org', 'discord.com/channels', 'messages.google.com',
  // password managers
  'bitwarden.com', '1password.com', 'lastpass.com',
  // sensitive URL paths
  '/login', '/signin', '/sign-in', '/password', '/oauth', '/checkout', '/payment', '/billing', '/admin',
];

export const DEFAULT_MODEL = 'qwen2.5:7b-instruct';

export const DEFAULT_SETTINGS: Settings = {
  captureEnabled: true,
  blocklist: DEFAULT_BLOCKLIST,
  model: DEFAULT_MODEL,
};

const STORAGE_KEY = 'groundwork:settings';

export async function getSettings(): Promise<Settings> {
  const stored = await chrome.storage.local.get(STORAGE_KEY);
  return { ...DEFAULT_SETTINGS, ...(stored[STORAGE_KEY] as Partial<Settings> | undefined) };
}

export async function saveSettings(patch: Partial<Settings>): Promise<Settings> {
  const next = { ...(await getSettings()), ...patch };
  await chrome.storage.local.set({ [STORAGE_KEY]: next });
  return next;
}

/** True if `url` matches any blocklist entry (case-insensitive substring match). */
export function isBlocked(url: string, settings: Settings): boolean {
  const u = url.toLowerCase();
  return settings.blocklist.some((p) => p && u.includes(p.toLowerCase()));
}
