import { useEffect, useState } from "react";
import { deleteDocument, listDocuments, uploadDocument } from "../api";
import type { DocumentInfo } from "../types";

export default function KnowledgeConsole() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const data = await listDocuments();
    setDocs(data);
  }

  useEffect(() => {
    void refresh().catch((e) =>
      setError(e instanceof Error ? e.message : "Error cargando documentos"),
    );
  }, []);

  async function handleUpload() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const doc = await uploadDocument(file, title || file.name);
      setMessage(`Documento indexado: ${doc.title} (${doc.chunk_count} chunks)`);
      setFile(null);
      setTitle("");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al subir");
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(docId: string) {
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await deleteDocument(docId);
      setMessage("Documento eliminado — el agente ya no lo usará.");
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al eliminar");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <h2>Consola de conocimiento</h2>
          <p>Sube un .txt/.md y el agente lo aprende; elimínalo y lo olvida.</p>
        </div>
      </header>

      <div className="form-grid">
        <label>
          Título
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Protocolo herida quirúrgica"
          />
        </label>
        <label>
          Archivo (texto plano recomendado en el scaffold)
          <input
            type="file"
            accept=".txt,.md,.text"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>
        <button type="button" onClick={() => void handleUpload()} disabled={busy || !file}>
          Subir e indexar
        </button>
      </div>

      <table className="docs-table">
        <thead>
          <tr>
            <th>Título</th>
            <th>Archivo</th>
            <th>Chunks</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {docs.map((d) => (
            <tr key={d.doc_id}>
              <td>{d.title}</td>
              <td>
                <code>{d.filename}</code>
              </td>
              <td>{d.chunk_count}</td>
              <td>
                <button
                  type="button"
                  className="danger"
                  onClick={() => void handleDelete(d.doc_id)}
                  disabled={busy}
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
          {docs.length === 0 ? (
            <tr>
              <td colSpan={4}>Sin documentos todavía.</td>
            </tr>
          ) : null}
        </tbody>
      </table>

      {message ? <p className="ok">{message}</p> : null}
      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
