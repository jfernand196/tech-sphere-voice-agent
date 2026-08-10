/** Display helpers for official-kit demo cases (UI only; never sent to the LLM). */

import type { MessageKey } from "./i18n";

type TFn = (key: MessageKey) => string;

const LABEL_KEYS: Record<string, MessageKey> = {
  rojo: "label.rojoDetail",
  amarillo: "label.amarilloDetail",
  verde: "label.verdeDetail",
};

const SLUG_COPY: Record<string, string> = {
  secrecion_purulenta: "secreción purulenta",
  eritema_leve: "eritema leve",
  normal: "normal",
  limitada_esperada: "limitada (esperada)",
};

export function formatCaseLabel(label: string, t: TFn): string {
  const key = LABEL_KEYS[label];
  return key ? t(key) : label;
}

function humanizeSlug(value: string): string {
  const key = value.trim().toLowerCase();
  if (SLUG_COPY[key]) return SLUG_COPY[key];
  return value.replace(/_/g, " ");
}

/** Turn dataset-style hints into short clinical Spanish for the actor. */
function humanizeDemoHint(hint: string): string {
  if (!hint.trim()) return hint;

  let text = hint;
  text = text.replace(/dolor\s+NRS\s+(\d+(?:\.\d+)?)/gi, "dolor $1/10");
  text = text.replace(/temp(?:eratura)?\s+(\d+(?:\.\d+)?)°?\s*C/gi, "temperatura $1 °C");
  text = text.replace(/herida:\s*([a-z0-9_]+)/gi, (_, slug: string) => {
    return `herida: ${humanizeSlug(slug)}`;
  });
  text = text.replace(/movilidad:\s*([a-z0-9_]+)/gi, (_, slug: string) => {
    return `movilidad: ${humanizeSlug(slug)}`;
  });
  text = text.replace(/_/g, " ");
  return text;
}

const PRIORITY_HINT = [
  /^dolor\b/i,
  /^temp/i,
  /^herida\b/i,
  /^movilidad\b/i,
];

function hintPriority(item: string): number {
  const idx = PRIORITY_HINT.findIndex((re) => re.test(item));
  return idx === -1 ? PRIORITY_HINT.length : idx;
}

/**
 * Top clinical bullets for the jury actor card (pain / fever / wound…).
 * Accepts `·` or `;` separators (kit export uses `;`).
 */
export function demoHintBullets(hint: string, max = 3): string[] {
  const humanized = humanizeDemoHint(hint);
  if (!humanized.trim()) return [];

  const parts = humanized
    .split(/\s*[·;|]\s*/)
    .map((p) => p.trim())
    .filter(Boolean);

  const clinical = parts.filter((p) => {
    const lower = p.toLowerCase();
    if (/eps\b/.test(lower)) return false;
    if (/bogot|medell|cali|barranq|cartagen|ciudad/.test(lower)) return false;
    return true;
  });

  const pool = clinical.length ? clinical : parts;
  return [...pool].sort((a, b) => hintPriority(a) - hintPriority(b)).slice(0, max);
}
