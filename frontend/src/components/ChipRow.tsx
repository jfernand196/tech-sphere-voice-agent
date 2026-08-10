export type ChipItem = {
  key: string;
  label: string;
  title?: string;
  className?: string;
};

/** Shared chip list — one markup path for symptoms, sources, etc. */
export default function ChipRow({ items }: { items: ChipItem[] }) {
  if (items.length === 0) return null;
  return (
    <ul className="chip-row">
      {items.map((item) => (
        <li
          key={item.key}
          className={item.className ?? "chip"}
          title={item.title}
        >
          {item.label}
        </li>
      ))}
    </ul>
  );
}
