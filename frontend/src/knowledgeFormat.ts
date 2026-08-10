import type { MessageKey } from "./i18n";
import { truncateEllipsis } from "./textFormat";
import type { DocumentInfo } from "./types";

export type DocGroup = "uploaded" | "kit" | "seed";

type TFn = (key: MessageKey, vars?: Record<string, string | number>) => string;

export function docGroup(doc: DocumentInfo): DocGroup {
  const meta = doc.metadata ?? {};
  if (meta.source === "official-kit" || meta.scenario) return "kit";
  if (meta.seed) return "seed";
  return "uploaded";
}

/** Short title for list rows (strip scenario prefix / trim). */
export function displayDocTitle(title: string, max = 72): string {
  return truncateEllipsis(title.replace(/^\[[^\]]+\]\s*/, ""), max);
}

export function groupLabel(group: DocGroup, t: TFn): string {
  if (group === "kit") return t("knowledge.groupKit");
  if (group === "seed") return t("knowledge.groupSeed");
  return t("knowledge.groupUploaded");
}

export function fragmentLabel(count: number, t: TFn): string {
  if (count === 1) return t("knowledge.fragmentOne");
  return t("knowledge.fragmentMany", { n: count });
}
