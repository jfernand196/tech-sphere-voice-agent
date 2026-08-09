"""Demo patient cases from the official kit (selector for the call UI)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException

from app.schemas import DemoPatient

router = APIRouter(prefix="/demo", tags=["demo"])

# backend/app/api/demo.py → repo root
_DEMO_PATIENTS_PATH = Path(__file__).resolve().parents[3] / "samples" / "demo_patients.json"


@lru_cache
def _load_patients() -> tuple[DemoPatient, ...]:
    if not _DEMO_PATIENTS_PATH.exists():
        return tuple()
    raw = json.loads(_DEMO_PATIENTS_PATH.read_text(encoding="utf-8"))
    return tuple(DemoPatient(**item) for item in raw)


@router.get("/patients", response_model=List[DemoPatient])
def list_demo_patients():
    patients = _load_patients()
    if not patients:
        raise HTTPException(
            status_code=404,
            detail="samples/demo_patients.json missing. Run: make export-demo",
        )
    return list(patients)
