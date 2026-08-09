/** Normalize unknown catch values into a user-facing message. */
export function errMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}
