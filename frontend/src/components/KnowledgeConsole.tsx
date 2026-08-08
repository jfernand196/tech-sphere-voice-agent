import { useEffect, useRef, useState } from "react";
import { deleteDocument, listDocuments, uploadDocument } from "../api";
import type { DocumentInfo } from "../types";

export default function KnowledgeConsole() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function refresh() {
    const data = await listDocuments();
    setDocs(data);
  }

  useEffect(() => {
    void refresh().catch((e) =>
      setError(e instanceof Error ? e.message : "Error cargando documentos"),
    );
  }, []);

  function takeFile(next: File | null) {
    setFile(next);
    if (next && !title.trim()) {
      setTitle(next.name.replace(/\.(txt|md|text|pdf)$/i, ""));
    }
  }

  async function handleUpload() {
    if (!file) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const doc = await uploadDocument(file, title || file.name);
      setMessage(`Indexado: ${doc.title} · ${doc.chunk_count} fragmentos`);
      setFile(null);
      setTitle("");
      if (inputRef.current) inputRef.current.value = "";
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
      setMessage("Documento eliminado. El agente ya no lo usará en caliente.");
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
          <p>Sube un protocolo y el agente lo aprende al instante. Elimínalo y lo olvida.</p>
        </div>
        <span className="count-pill">{docs.length} docs</span>
      </header>

      <div className="knowledge-layout">
        <div className="upload-card">
          <label>
            Título
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Protocolo herida quirúrgica"
            />
          </label>

          <div
            className={`dropzone ${dragging ? "dropzone--active" : ""} ${file ? "dropzone--filled" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              takeFile(e.dataTransfer.files?.[0] ?? null);
            }}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
            }}
          >
            <strong>{file ? file.name : "Arrastra un .txt, .md o .pdf"}</strong>
            <span>{file ? "Clic para cambiar archivo" : "o haz clic para elegir"}</span>
            <input
              ref={inputRef}
              type="file"
              accept=".txt,.md,.text,.pdf,application/pdf"
              hidden
              onChange={(e) => takeFile(e.target.files?.[0] ?? null)}
            />
          </div>

          <button
            type="button"
            className="btn-block"
            onClick={() => void handleUpload()}
            disabled={busy || !file}
          >
            Subir e indexar
          </button>
        </div>

        <div className="docs-list">
          {docs.length === 0 ? (
            <div className="empty-state">
              <p>Aún no hay documentos. Sube el primero para alimentar el RAG.</p>
            </div>
          ) : (
            docs.map((d) => (
              <article key={d.doc_id} className="doc-card enter">
                <div>
                  <h3>{d.title}</h3>
                  <p>
                    <code>{d.filename}</code> · {d.chunk_count} chunks
                  </p>
                </div>
                <button
                  type="button"
                  className="danger"
                  onClick={() => void handleDelete(d.doc_id)}
                  disabled={busy}
                >
                  Eliminar
                </button>
              </article>
            ))
          )}
        </div>
      </div>

      {message ? <p className="ok banner-ok">{message}</p> : null}
      {error ? <p className="error banner-error">{error}</p> : null}
    </section>
  );
}
