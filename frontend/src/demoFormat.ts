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
export function humanizeDemoHint(hint: string): string {
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
