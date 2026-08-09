/** Patient-facing clinical labels (shared by chat bubbles and call summary). */

import type { MessageKey } from "./i18n";

type TFn = (key: MessageKey) => string;

const SEVERITY_KEYS: Record<string, MessageKey> = {
  none: "severity.none",
  mild: "severity.mild",
  moderate: "severity.moderate",
  severe: "severity.severe",
};

/** Chip in live chat: hide "none". */
export function severityChip(
  severity: string | undefined | null,
  t: TFn,
): string | null {
  if (!severity || severity === "none") return null;
  const key = SEVERITY_KEYS[severity];
  return key ? t(key) : severity;
}

/** Summary / tables: always show a readable value. */
export function severityText(
  severity: string | undefined | null,
  t: TFn,
): string {
  if (!severity) return "—";
  const key = SEVERITY_KEYS[severity];
  return key ? t(key) : severity;
}
