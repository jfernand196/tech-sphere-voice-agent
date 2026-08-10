/** Shared string display helpers (DRY across knowledge / chat / summary). */

export function truncateEllipsis(text: string, max: number): string {
  const trimmed = text.trim();
  if (trimmed.length <= max) return trimmed;
  if (max <= 1) return "…";
  return `${trimmed.slice(0, max - 1).trimEnd()}…`;
}
