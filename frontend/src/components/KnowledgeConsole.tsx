import { useEffect, useMemo, useRef, useState } from "react";
import { deleteDocument, listDocuments, uploadDocument } from "../api";
import { errMessage } from "../errors";
import { useLocale } from "../i18n/LocaleContext";
import {
  displayDocTitle,
  docGroup,
  fragmentLabel,
  groupLabel,
  type DocGroup,
} from "../knowledgeFormat";
import type { DocumentInfo } from "../types";

const GROUP_ORDER: DocGroup[] = ["uploaded", "kit", "seed"];

export default function KnowledgeConsole() {
  const { t } = useLocale();
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [query, setQuery] = useState("");
  const [kitOpen, setKitOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function refresh() {
    const data = await listDocuments();
    setDocs(data);
  }

  useEffect(() => {
    void refresh().catch((e) => setError(errMessage(e, t("knowledge.errorLoad"))));
  }, [t]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return docs;
    return docs.filter((d) => {
      const hay = `${d.title} ${d.filename} ${String(d.metadata?.scenario ?? "")}`.toLowerCase();
      return hay.includes(q);
    });
  }, [docs, query]);

  const grouped = useMemo(() => {
    const map: Record<DocGroup, DocumentInfo[]> = {
      uploaded: [],
      kit: [],
      seed: [],
    };
    for (const d of filtered) {
      map[docGroup(d)].push(d);
    }
    return map;
  }, [filtered]);

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
      setMessage(
        t("knowledge.indexed", {
          title: displayDocTitle(doc.title, 48),
          fragments: fragmentLabel(doc.chunk_count, t),
        }),
      );
      setFile(null);
      setTitle("");
      if (inputRef.current) inputRef.current.value = "";
      await refresh();
    } catch (e) {
      setError(errMessage(e, t("knowledge.errorUpload")));
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete(doc: DocumentInfo) {
    const short = displayDocTitle(doc.title, 40);
    if (!window.confirm(t("knowledge.confirmDelete", { title: short }))) {
      return;
    }
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await deleteDocument(doc.doc_id);
      setMessage(t("knowledge.deleted"));
      await refresh();
    } catch (e) {
      setError(errMessage(e, t("knowledge.errorDelete")));
    } finally {
      setBusy(false);
    }
  }

  function renderDoc(d: DocumentInfo) {
    const group = docGroup(d);
    const scenario =
      typeof d.metadata?.scenario === "string" ? d.metadata.scenario : null;
    return (
      <article key={d.doc_id} className="doc-card">
        <div className="doc-card__body">
          <h3 title={d.title}>{displayDocTitle(d.title)}</h3>
          <p>
            {scenario ? <span className="doc-tag">{scenario}</span> : null}
            {group === "seed" ? (
              <span className="doc-tag">{t("knowledge.tagBase")}</span>
            ) : null}
            <span>
              {fragmentLabel(d.chunk_count, t)} · <code>{d.filename}</code>
            </span>
          </p>
        </div>
        <button
          type="button"
          className="danger"
          onClick={() => void handleDelete(d)}
          disabled={busy}
        >
          {t("knowledge.delete")}
        </button>
      </article>
    );
  }

  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <h2>{t("knowledge.title")}</h2>
          <p>{t("knowledge.lede")}</p>
        </div>
        <span className="count-pill">{t("knowledge.docsCount", { n: docs.length })}</span>
      </header>

      <div className="knowledge-layout">
        <div className="upload-card">
          <p className="upload-card__lead">{t("knowledge.juryTip")}</p>
          <label>
            {t("knowledge.docTitle")}
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t("knowledge.titlePlaceholder")}
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
            <strong>{file ? file.name : t("knowledge.dropEmpty")}</strong>
            <span>{file ? t("knowledge.dropChange") : t("knowledge.dropHint")}</span>
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
            {t("knowledge.upload")}
          </button>
        </div>

        <div className="docs-panel">
          <label className="docs-search">
            <span className="sr-only">{t("knowledge.searchAria")}</span>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("knowledge.searchPlaceholder")}
            />
          </label>

          <div className="docs-list">
            {filtered.length === 0 ? (
              <div className="empty-state">
                <p>{docs.length === 0 ? t("knowledge.empty") : t("knowledge.noMatch")}</p>
              </div>
            ) : (
              GROUP_ORDER.map((group) => {
                const items = grouped[group];
                if (!items.length) return null;

                if (group === "kit") {
                  return (
                    <details
                      key={group}
                      className="doc-group"
                      open={kitOpen || Boolean(query.trim())}
                      onToggle={(e) => setKitOpen((e.target as HTMLDetailsElement).open)}
                    >
                      <summary>
                        {groupLabel(group, t)}
                        <span className="doc-group__count">{items.length}</span>
                      </summary>
                      <div className="doc-group__list">{items.map(renderDoc)}</div>
                    </details>
                  );
                }

                return (
                  <section key={group} className="doc-group doc-group--static">
                    <header className="doc-group__header">
                      <h3>{groupLabel(group, t)}</h3>
                      <span className="doc-group__count">{items.length}</span>
                    </header>
                    <div className="doc-group__list">{items.map(renderDoc)}</div>
                  </section>
                );
              })
            )}
          </div>
        </div>
      </div>

      {message ? <p className="ok banner-ok">{message}</p> : null}
      {error ? <p className="error banner-error">{error}</p> : null}
    </section>
  );
}
