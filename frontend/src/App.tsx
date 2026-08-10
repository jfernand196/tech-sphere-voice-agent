import { useEffect, useState } from "react";
import { getHealth } from "./api";
import CallPanel from "./components/CallPanel";
import KnowledgeConsole from "./components/KnowledgeConsole";
import LocaleToggle from "./components/LocaleToggle";
import { useLocale } from "./i18n/LocaleContext";

type Tab = "call" | "knowledge";

export default function App() {
  const { t, locale } = useLocale();
  const [tab, setTab] = useState<Tab>("call");
  const [health, setHealth] = useState<{
    label: string;
    tone: "ok" | "warn" | "bad" | "loading";
  }>({ label: "", tone: "loading" });

  useEffect(() => {
    setHealth({ label: t("app.healthConnecting"), tone: "loading" });
    void getHealth()
      .then((h) => {
        if (!h?.status || !h.model_id) {
          setHealth({ label: t("app.healthBadBackend"), tone: "warn" });
          return;
        }
        if (h.llm_ready === false) {
          setHealth({
            label: h.llm_detail || t("app.healthMissingKey"),
            tone: "warn",
          });
          return;
        }
        setHealth({
          label: `${h.llm_provider} · ${h.model_id}`,
          tone: "ok",
        });
      })
      .catch(() => setHealth({ label: t("app.healthOffline"), tone: "bad" }));
  }, [t, locale]);

  return (
    <div className="app-shell">
      <div className="app">
        <header className="topbar">
          <div>
            <p className="brand">{t("app.brand")}</p>
            <h1>{t("app.title")}</h1>
            <p className="lede">{t("app.lede")}</p>
            <p className="byline">{t("app.byline")}</p>
            {locale === "en" ? <p className="agent-note">{t("app.agentNote")}</p> : null}
          </div>
          <div className="topbar__aside">
            <LocaleToggle />
            <div
              className={`status-pill status-pill--${health.tone}`}
              title={t("app.healthTitle", { label: health.label })}
            >
              <span className="status-dot" aria-hidden />
              <span className="status-pill__label">{health.label}</span>
            </div>
          </div>
        </header>

        <nav className="tabs" aria-label={t("app.navAria")}>
          <button
            type="button"
            className={tab === "call" ? "active" : ""}
            onClick={() => setTab("call")}
          >
            {t("app.tabCall")}
          </button>
          <button
            type="button"
            className={tab === "knowledge" ? "active" : ""}
            onClick={() => setTab("knowledge")}
          >
            {t("app.tabKnowledge")}
          </button>
        </nav>

        <main className="main-stage" key={tab}>
          {tab === "call" ? <CallPanel /> : <KnowledgeConsole />}
        </main>
      </div>
    </div>
  );
}
