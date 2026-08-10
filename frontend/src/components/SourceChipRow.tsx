import { displayDocTitle } from "../knowledgeFormat";
import type { SourceCitation } from "../types";
import ChipRow from "./ChipRow";

type Props = {
  sources: SourceCitation[];
  /** Include excerpt in tooltip when present (chat bubbles). */
  withExcerpt?: boolean;
  titleMax?: number;
};

/** One mapping path for source chips in chat + call summary. */
export default function SourceChipRow({
  sources,
  withExcerpt = false,
  titleMax = 42,
}: Props) {
  if (sources.length === 0) return null;
  return (
    <ChipRow
      items={sources.map((s) => ({
        key: s.chunk_id,
        label: displayDocTitle(s.title, titleMax),
        title:
          withExcerpt && s.excerpt
            ? `${s.title}\n\n${s.excerpt}`
            : s.title,
        className: "chip chip--source",
      }))}
    />
  );
}
