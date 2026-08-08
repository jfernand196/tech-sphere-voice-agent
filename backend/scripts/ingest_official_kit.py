#!/usr/bin/env python3
"""Ingest clinical PDFs from the official Tech Sphere kit into the local RAG store.

Usage (from repo root, with backend venv active):

  python backend/scripts/ingest_official_kit.py
  python backend/scripts/ingest_official_kit.py --scenario cholecystitis --limit 5

Expects the kit at ./official-kit (see STATUS.md / Makefile target kit-clone).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.config import get_settings  # noqa: E402
from app.rag.extract import extract_text  # noqa: E402
from app.rag.service import KnowledgeService  # noqa: E402

DEFAULT_KIT = ROOT / "official-kit" / "dataset" / "textos"
SCENARIOS = [
    "Appendicitis",
    "breast_cancer",
    "cholecystitis",
    "colorectal cancer",
    "total joint replacement",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest official kit clinical PDFs")
    parser.add_argument(
        "--kit-textos",
        type=Path,
        default=DEFAULT_KIT,
        help="Path to dataset/textos",
    )
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS + ["all"],
        default="all",
        help="Which scenario folder to ingest",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max PDFs per scenario (0 = all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files without ingesting",
    )
    args = parser.parse_args()

    textos = args.kit_textos
    if not textos.is_dir():
        print(f"ERROR: kit textos not found at {textos}")
        print("Run: make kit-clone")
        return 1

    scenarios = SCENARIOS if args.scenario == "all" else [args.scenario]
    settings = get_settings()
    ks = KnowledgeService(settings)

    total = 0
    skipped = 0
    for scenario in scenarios:
        folder = textos / scenario
        if not folder.is_dir():
            print(f"WARN: missing {folder}")
            continue
        pdfs = sorted(folder.glob("*.pdf"))
        if args.limit:
            pdfs = pdfs[: args.limit]
        print(f"\n=== {scenario}: {len(pdfs)} PDF(s) ===")
        for pdf in pdfs:
            title = f"[{scenario}] {pdf.stem}"
            if args.dry_run:
                print(f"  would ingest: {pdf.name}")
                total += 1
                continue
            content = pdf.read_bytes()
            text = extract_text(pdf.name, content)
            if len(text.strip()) < 40:
                print(f"  SKIP (empty extract): {pdf.name}")
                skipped += 1
                continue
            doc = ks.ingest_text(
                title=title,
                filename=pdf.name,
                text=text,
                metadata={
                    "scenario": scenario,
                    "source": "official-kit",
                    "path": str(pdf),
                },
            )
            print(f"  OK {doc.doc_id[:8]}… chunks={doc.chunk_count} — {pdf.name[:60]}")
            total += 1

    print(f"\nDone. ingested={total} skipped={skipped} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
