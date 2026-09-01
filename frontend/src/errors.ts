/** Normalize unknown catch values into a user-facing message. */
export function errMessage(error: unknown, fallback: string): string {
  if (!(error instanceof Error)) return fallback;
  return error.message || fallback;
}

/** FastAPI `{ "detail": "..." }` bodies should surface the detail, not raw JSON. */
export function httpErrorMessage(text: string, fallback: string): string {
  const raw = text.trim();
  if (!raw) return fallback;
  try {
    const parsed = JSON.parse(raw) as { detail?: unknown };
    if (typeof parsed.detail === "string" && parsed.detail.trim()) {
      return parsed.detail;
    }
  } catch {
    /* not JSON */
  }
  return raw;
}
