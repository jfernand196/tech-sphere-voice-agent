/** Patient-facing clinical labels (shared by chat bubbles and call summary). */

const SEVERITY_ES: Record<string, string> = {
  none: "Sin síntomas",
  mild: "Leve",
  moderate: "Moderada",
  severe: "Severa",
};

/** Chip in live chat: hide "none". */
export function severityChip(severity: string | undefined | null): string | null {
  if (!severity || severity === "none") return null;
  return SEVERITY_ES[severity] ?? severity;
}

/** Summary / tables: always show a readable value. */
export function severityText(severity: string | undefined | null): string {
  if (!severity) return "—";
  return SEVERITY_ES[severity] ?? severity;
}
