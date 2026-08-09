"""Load curated cholecystectomy cases from the official kit for offline eval."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[3]
KIT = REPO_ROOT / "official-kit" / "dataset"
PROCEDURE = "Colecistectomía"

_SLUG_ES = {
    "secrecion_purulenta": "secreción purulenta",
    "eritema_leve": "eritema leve",
    "normal": "normal",
    "limitada_esperada": "limitada (esperada)",
    "muy_disminuido": "muy disminuido",
    "muy_alterado": "muy alterado",
}


@dataclass(frozen=True)
class EvalCase:
    caso_id: str
    paciente_id: str
    patient_name: str
    procedure: str
    dia_postop: int
    label: str
    patient_utterance: str
    demo_hint: str


def _rows(path: Path) -> List[dict]:
    if openpyxl is None:
        raise RuntimeError("openpyxl is required. pip install openpyxl")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    it = ws.iter_rows(values_only=True)
    headers = [str(h) for h in next(it)]
    out = [{headers[i]: row[i] for i in range(len(headers))} for row in it]
    wb.close()
    return out


def _humanize(value: object) -> str:
    key = str(value or "").strip().lower()
    return _SLUG_ES.get(key, key.replace("_", " "))


def utterance_from_trajectory(tray: dict, dia: int) -> str:
    """Compact patient message built from clinical ground truth (actor script)."""
    parts = [
        f"Me operaron hace {dia} días de la vesícula.",
        f"El dolor lo pondría en {tray.get('dolor_nrs')}/10.",
        f"He tenido temperatura como de {tray.get('fiebre_c')} grados.",
        f"La herida la veo con {_humanize(tray.get('herida'))}.",
        f"Para caminar me siento con movilidad {_humanize(tray.get('movilidad'))}.",
        f"El apetito está {_humanize(tray.get('apetito'))} y duermo {_humanize(tray.get('sueno'))}.",
    ]
    return " ".join(parts)


def load_cholecystectomy_cases(
    *,
    labels: Optional[Iterable[str]] = None,
    limit_per_label: int = 4,
) -> List[EvalCase]:
    """Prefer capa2 labels; utterance from trayectoria (stable clinical signal)."""
    clin_path = KIT / "perfiles_clinicos_pacientes_silver_contest.xlsx"
    demo_path = KIT / "perfiles_pacientes_co.xlsx"
    traj_path = KIT / "trayectorias_postop_silver.xlsx"
    dialog_path = KIT / "dataset_final.xlsx"
    for p in (clin_path, demo_path, traj_path, dialog_path):
        if not p.exists():
            raise FileNotFoundError(f"Missing {p}. Run: make kit-clone")

    clin = {r["paciente_id"]: r for r in _rows(clin_path)}
    demo = {r["paciente_id"]: r for r in _rows(demo_path)}
    traj = {r["trayectoria_id"]: r for r in _rows(traj_path)}
    chole_ids = {
        pid
        for pid, row in clin.items()
        if str(row.get("procedimiento") or "") == PROCEDURE
    }

    wanted = {x.lower() for x in (labels or ("rojo", "amarillo", "verde"))}
    by_label: Dict[str, List[EvalCase]] = {k: [] for k in wanted}

    seen = set()
    for r in _rows(dialog_path):
        capa = str(r.get("capa") or "")
        if "capa1" not in capa:
            continue
        caso_id = str(r["caso_id"])
        if caso_id in seen:
            continue
        seen.add(caso_id)
        pid = r["paciente_id"]
        if pid not in chole_ids:
            continue
        label = str(r["label_ground_truth"]).lower()
        if label not in wanted:
            continue
        tray_id = caso_id.replace("caso_", "", 1)
        tray = traj.get(tray_id)
        if not tray:
            continue
        dia = int(r["dia_postop"])
        name = str(demo.get(pid, {}).get("nombre_completo") or f"Paciente {pid}")
        hint = (
            f"dolor {tray.get('dolor_nrs')}/10; "
            f"temperatura {tray.get('fiebre_c')} °C; "
            f"herida: {_humanize(tray.get('herida'))}"
        )
        case = EvalCase(
            caso_id=caso_id,
            paciente_id=str(pid),
            patient_name=name,
            procedure="colecistectomía",
            dia_postop=dia,
            label=label,
            patient_utterance=utterance_from_trajectory(tray, dia),
            demo_hint=hint,
        )
        by_label[label].append(case)

    selected: List[EvalCase] = []
    for label in ("rojo", "amarillo", "verde"):
        if label not in by_label:
            continue
        chunk = sorted(by_label[label], key=lambda c: (c.dia_postop, c.caso_id))
        selected.extend(chunk[:limit_per_label])
    return selected
