/**
 * Compress a raw CDP accessibility tree into a compact, on-task node list for the
 * action model (~5–10% of DOM nodes; docs/02 §2). Assigns stable element indices and
 * a change-detecting versionId. Text-first, vision-optional.
 */
import type { AXNode } from '../types';

// Raw shape from Accessibility.getFullAXTree
export interface RawAXNode {
  nodeId: string;
  ignored?: boolean;
  role?: { value?: string };
  name?: { value?: string };
  value?: { value?: unknown };
  properties?: { name: string; value?: { value?: unknown } }[];
  backendDOMNodeId?: number;
}

const INTERACTIVE = new Set([
  'button', 'link', 'textbox', 'searchbox', 'combobox', 'checkbox', 'radio',
  'menuitem', 'menuitemcheckbox', 'menuitemradio', 'tab', 'option', 'switch',
  'slider', 'spinbutton', 'listbox', 'textarea', 'disclosuretriangle',
]);
const CONTEXT = new Set(['heading']);
const STATE_PROPS = new Set([
  'focused', 'disabled', 'checked', 'expanded', 'selected', 'required', 'invalid', 'hidden', 'readonly',
]);

function stateOf(props: RawAXNode['properties']): string[] {
  const out: string[] = [];
  for (const p of props ?? []) {
    if (!STATE_PROPS.has(p.name)) continue;
    const v = p.value?.value;
    if (v === true || v === 'true' || v === 'mixed') out.push(p.name);
    else if (v === 'mixed') out.push(`${p.name}:mixed`);
  }
  return out;
}

export function compressAX(raw: RawAXNode[], cap = 200): AXNode[] {
  const nodes: AXNode[] = [];
  for (const r of raw) {
    if (r.ignored) continue;
    const role = r.role?.value ?? '';
    const name = (r.name?.value ?? '').trim();
    const isInteractive = INTERACTIVE.has(role);
    const isContext = CONTEXT.has(role) && name;
    if (!isInteractive && !isContext) continue;
    // interactive-but-nameless is fine for text inputs; other roles need a name
    if (!name && !['textbox', 'searchbox', 'combobox', 'textarea'].includes(role)) continue;

    const valRaw = r.value?.value;
    nodes.push({
      index: nodes.length,
      role,
      name: name || undefined,
      value: valRaw == null ? undefined : String(valRaw),
      state: stateOf(r.properties),
      backendNodeId: r.backendDOMNodeId,
    });
    if (nodes.length >= cap) break;
  }
  return nodes;
}

/** FNV-1a 32-bit hex over the serialized snapshot — changes iff the observation changes. */
export function computeVersionId(nodes: AXNode[], url: string): string {
  const s = url + '|' + nodes.map((n) => `${n.index}:${n.role}:${n.name ?? ''}:${(n.state ?? []).join(',')}`).join('|');
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(16).padStart(8, '0');
}

/** Strip executor-only fields before the observation is shown to the model. */
export function forModel(nodes: AXNode[]): Omit<AXNode, 'backendNodeId'>[] {
  return nodes.map(({ backendNodeId, ...rest }) => rest);
}
