#!/usr/bin/env python3
"""Build samples/demo_patients.json from the official kit Excels.

Usage (repo root, backend venv active):

  PYTHONPATH=backend python backend/scripts/export_demo_patients.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import openpyxl
except ImportError:
    print("ERROR: openpyxl required. pip install openpyxl")
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "official-kit" / "dataset"
OUT = ROOT / "samples" / "demo_patients.json"
PROCEDURE_FILTER = "Colecistectomía"
MAX_CASES = 12


def _sheet_rows(path: Path) -> list[dict]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    headers = [str(h) for h in next(rows_iter)]
    out = []
    for row in rows_iter:
        out.append({headers[i]: row[i] for i in range(len(headers))})
    wb.close()
    return out


_SLUG_ES = {
    "secrecion_purulenta": "secreción purulenta",
    "eritema_leve": "eritema leve",
    "normal": "normal",
    "limitada_esperada": "limitada (esperada)",
}


def _humanize_slug(value: object) -> str:
    key = str(value or "").strip().lower()
    if key in _SLUG_ES:
        return _SLUG_ES[key]
    return key.replace("_", " ")


def _hint(tray: dict) -> str:
    """Actor-facing Spanish (not LLM context)."""
    parts = []
    if tray.get("dolor_nrs") is not None:
        parts.append(f"dolor {tray['dolor_nrs']}/10")
    if tray.get("fiebre_c") is not None:
        parts.append(f"temperatura {tray['fiebre_c']} °C")
    if tray.get("herida"):
        parts.append(f"herida: {_humanize_slug(tray['herida'])}")
    if tray.get("movilidad"):
        parts.append(f"movilidad: {_humanize_slug(tray['movilidad'])}")
    return "; ".join(parts) if parts else "síntomas según conversación"


def main() -> int:
    clin_path = KIT / "perfiles_clinicos_pacientes_silver_contest.xlsx"
    demo_path = KIT / "perfiles_pacientes_co.xlsx"
    traj_path = KIT / "trayectorias_postop_silver.xlsx"
    dialog_path = KIT / "dataset_final.xlsx"
    for p in (clin_path, demo_path, traj_path, dialog_path):
        if not p.exists():
            print(f"ERROR: missing {p}. Run: make kit-clone")
            return 1

    clin = {r["paciente_id"]: r for r in _sheet_rows(clin_path)}
    demo = {r["paciente_id"]: r for r in _sheet_rows(demo_path)}
    traj_by_id = {r["trayectoria_id"]: r for r in _sheet_rows(traj_path)}

    # Unique cases from capa1 (ground-truth label is constant per caso_id)
    cases: dict[str, dict] = {}
    for r in _sheet_rows(dialog_path):
        capa = str(r.get("capa") or "")
        if "capa1" not in capa:
            continue
        caso_id = r["caso_id"]
        if caso_id in cases:
            continue
        cases[caso_id] = {
            "caso_id": caso_id,
            "paciente_id": r["paciente_id"],
            "dia_postop": int(r["dia_postop"]),
            "label": str(r["label_ground_truth"]).lower(),
        }

    # Filter cholecystectomy patients
    chole_ids = {
        pid
        for pid, row in clin.items()
        if str(row.get("procedimiento") or "") == PROCEDURE_FILTER
    }

    by_label: dict[str, list[dict]] = defaultdict(list)
    for caso in cases.values():
        if caso["paciente_id"] not in chole_ids:
            continue
        by_label[caso["label"]].append(caso)

    # Prefer reds, then yellows, then greens until MAX_CASES
    selected: list[dict] = []
    for label in ("rojo", "amarillo", "verde"):
        for caso in sorted(by_label[label], key=lambda c: (c["dia_postop"], c["caso_id"])):
            if len(selected) >= MAX_CASES:
                break
            selected.append(caso)
        if len(selected) >= MAX_CASES:
            break

    patients = []
    for caso in selected:
        pid = caso["paciente_id"]
        demo_row = demo[pid]
        trayectoria_id = str(caso["caso_id"]).replace("caso_", "", 1)
        tray = traj_by_id.get(trayectoria_id, {})
        nombre = str(demo_row.get("nombre_completo") or f"Paciente {pid}")
        patients.append(
            {
                "id": caso["caso_id"],
                "paciente_id": pid,
                "nombre": nombre,
                "procedimiento": "colecistectomía",
                "dia_postop": caso["dia_postop"],
                "label": caso["label"],
                "demo_hint": _hint(tray),
                "ciudad": demo_row.get("ciudad") or "",
                "eps": demo_row.get("eps") or "",
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(patients, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(patients)} cases → {OUT}")
    labels = defaultdict(int)
    for p in patients:
        labels[p["label"]] += 1
    print("labels:", dict(labels))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
