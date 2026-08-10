import type { ReactNode } from "react";

type Props = {
  kicker: string;
  title: string;
  children: ReactNode;
  className?: string;
};

/** Shared collapsible panel (voice settings, challenge metrics). */
export default function Disclosure({
  kicker,
  title,
  children,
  className = "",
}: Props) {
  return (
    <details className={["disclosure", className].filter(Boolean).join(" ")}>
      <summary>
        <span className="disclosure__text">
          <span className="disclosure__kicker">{kicker}</span>
          <span className="disclosure__title">{title}</span>
        </span>
        <span className="disclosure__chevron" aria-hidden>
          ▾
        </span>
      </summary>
      {children}
    </details>
  );
}
