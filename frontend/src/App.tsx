import { useEffect, useState } from "react";
import { getHealth } from "./api";
import CallPanel from "./components/CallPanel";
import KnowledgeConsole from "./components/KnowledgeConsole";

type Tab = "call" | "knowledge";

export default function App() {
  const [tab, setTab] = useState<Tab>("call");
  const [health, setHealth] = useState<string>("…");

  useEffect(() => {
    void getHealth()
      .then((h) => {
        if (!h?.status || !h.model_id) {
          setHealth("backend incorrecto (¿puerto?)");
          return;
        }
        setHealth(`${h.status} · ${h.llm_provider}/${h.model_id}`);
      })
      .catch(() => setHealth("backend offline"));
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <p className="eyebrow">Tech Sphere 2026</p>
          <h1>Agente de voz post-operatorio</h1>
        </div>
        <div className="health">API: {health}</div>
      </header>

      <nav className="tabs">
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

      <main>{tab === "call" ? <CallPanel /> : <KnowledgeConsole />}</main>
    </div>
  );
}
