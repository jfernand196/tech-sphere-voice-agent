import { useEffect, useState } from "react";
import { getHealth } from "./api";
import CallPanel from "./components/CallPanel";
import KnowledgeConsole from "./components/KnowledgeConsole";

type Tab = "call" | "knowledge";

export default function App() {
  const [tab, setTab] = useState<Tab>("call");
  const [health, setHealth] = useState<{
    label: string;
    tone: "ok" | "warn" | "bad" | "loading";
  }>({ label: "conectando…", tone: "loading" });

  useEffect(() => {
    void getHealth()
      .then((h) => {
        if (!h?.status || !h.model_id) {
          setHealth({ label: "backend incorrecto", tone: "warn" });
          return;
        }
        setHealth({
          label: `${h.llm_provider} · ${h.model_id}`,
          tone: "ok",
        });
      })
      .catch(() => setHealth({ label: "offline", tone: "bad" }));
  }, []);

  return (
    <div className="app-shell">
      <div className="app">
        <header className="topbar">
          <div className="topbar__copy">
            <p className="brand">Tech Sphere 2026</p>
            <h1>Agente de voz post-operatorio</h1>
            <p className="lede">
              Seguimiento clínico por conversación, con conocimiento vivo y criterio de alerta.
            </p>
          </div>
          <div
            className={`status-pill status-pill--${health.tone}`}
            title={`Estado del API: ${health.label}`}
          >
            <span className="status-dot" aria-hidden />
            <span className="status-pill__label">{health.label}</span>
          </div>
        </header>

        <nav className="tabs" aria-label="Secciones">
          <button
            type="button"
            className={tab === "call" ? "active" : ""}
            onClick={() => setTab("call")}
          >
            Llamada
          </button>
          <button
            type="button"
            className={tab === "knowledge" ? "active" : ""}
            onClick={() => setTab("knowledge")}
          >
            Conocimiento
          </button>
        </nav>

        <main className="main-stage" key={tab}>
          {tab === "call" ? <CallPanel /> : <KnowledgeConsole />}
        </main>
      </div>
    </div>
  );
}
