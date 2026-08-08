"""Extract plain text from uploaded clinical documents (.txt/.md/.pdf)."""

from __future__ import annotations

from pathlib import Path


def extract_text(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(content)
    # Default: treat as UTF-8 text (txt, md, etc.)
    return content.decode("utf-8", errors="ignore")


def _extract_pdf(content: bytes) -> str:
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(content))
    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            pages.append(text)
    return "\n\n".join(pages).strip()
