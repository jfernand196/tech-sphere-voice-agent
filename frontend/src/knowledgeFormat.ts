import type { DocumentInfo } from "./types";

export type DocGroup = "uploaded" | "kit" | "seed";

export function docGroup(doc: DocumentInfo): DocGroup {
  const meta = doc.metadata ?? {};
  if (meta.source === "official-kit" || meta.scenario) return "kit";
  if (meta.seed) return "seed";
  return "uploaded";
}

/** Short title for list rows (strip scenario prefix / trim). */
export function displayDocTitle(title: string, max = 72): string {
  let text = title.replace(/^\[[^\]]+\]\s*/, "").trim();
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1).trimEnd()}…`;
}

export function groupLabel(group: DocGroup): string {
  if (group === "kit") return "Corpus del kit";
  if (group === "seed") return "Protocolo base";
  return "Subidos por ti";
}

export function fragmentLabel(count: number): string {
  return count === 1 ? "1 fragmento" : `${count} fragmentos`;
}
