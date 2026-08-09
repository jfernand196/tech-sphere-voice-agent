import { en } from "./en";
import { es, type MessageKey } from "./es";

export type Locale = "es" | "en";
export type { MessageKey };

export const LOCALE_STORAGE_KEY = "tsva.locale";

const catalogs: Record<Locale, Record<MessageKey, string>> = { es, en };

export function detectLocale(): Locale {
  try {
    const saved = localStorage.getItem(LOCALE_STORAGE_KEY);
    if (saved === "es" || saved === "en") return saved;
  } catch {
    /* ignore */
  }
  const nav = typeof navigator !== "undefined" ? navigator.language : "es";
  return nav.toLowerCase().startsWith("es") ? "es" : "en";
}

export function translate(
  locale: Locale,
  key: MessageKey,
  vars?: Record<string, string | number>,
): string {
  let text = catalogs[locale][key] ?? catalogs.es[key] ?? key;
  if (vars) {
    for (const [name, value] of Object.entries(vars)) {
      text = text.replaceAll(`{${name}}`, String(value));
    }
  }
  return text;
}
