#!/usr/bin/env python3
"""Evaluate escalate decisions against kit ground-truth labels.

Usage (backend venv):

  PYTHONPATH=. python scripts/eval_escalate.py
  PYTHONPATH=. python scripts/eval_escalate.py --provider mock
  PYTHONPATH=. python scripts/eval_escalate.py --limit-per-label 2

Expectations:
  - rojo     → must escalate (false negative is critical)
  - amarillo → escalate preferred but not required
  - verde    → should not escalate (false positive counted)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

BACKEND = Path(__file__).resolve().parents[1]
REPO = BACKEND.parent
sys.path.insert(0, str(BACKEND))

from app.agent.factory import build_llm_client  # noqa: E402
from app.agent.service import AgentService  # noqa: E402
from app.config import Settings, get_settings  # noqa: E402
from app.eval.kit_cases import load_cholecystectomy_cases  # noqa: E402
from app.rag.service import KnowledgeService  # noqa: E402


@dataclass
class CaseResult:
    caso_id: str
    label: str
    dia_postop: int
    expected_escalate: bool
    predicted_escalate: bool
    correct_hard: bool
    escalate_reason: str | None
    severity: str
    model_id: str
    latency_ms: int | None


def _expected(label: str) -> bool:
    return label == "rojo"


async def _run_case(agent: AgentService, case, model_id: str) -> CaseResult:
    last_error: Exception | None = None
    turn = None
    for attempt in range(4):
        try:
            turn = await agent.respond(
                patient_name=case.patient_name,
                procedure=case.procedure,
                dia_postop=case.dia_postop,
                message=case.patient_utterance,
                history=[],
            )
            break
        except httpx.HTTPStatusError as exc:
            last_error = exc
            if exc.response.status_code != 429 or attempt == 3:
                raise
            time.sleep(2 ** attempt)
    if turn is None:
        raise RuntimeError(last_error)

    expected = _expected(case.label)
    predicted = bool(turn.escalate)
    # Hard score: rojo must escalate; verde must not; amarillo always "soft ok"
    if case.label == "amarillo":
        correct_hard = True
    else:
        correct_hard = predicted == expected
    return CaseResult(
        caso_id=case.caso_id,
        label=case.label,
        dia_postop=case.dia_postop,
        expected_escalate=expected,
        predicted_escalate=predicted,
        correct_hard=correct_hard,
        escalate_reason=turn.escalate_reason,
        severity=turn.patient_state.severity.value,
        model_id=turn.model_id or model_id,
        latency_ms=turn.latency_ms,
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description="Escalate eval vs kit labels")
    parser.add_argument(
        "--provider",
        choices=["", "mock", "groq", "gemini"],
        default="",
        help="Override LLM_PROVIDER for this run",
    )
    parser.add_argument("--limit-per-label", type=int, default=4)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO / "samples" / "eval_escalate_results.json",
    )
    args = parser.parse_args()

    get_settings.cache_clear()
    base = get_settings()
    settings = Settings(
        llm_provider=(args.provider or base.llm_provider),
        model_id=base.model_id,
        groq_api_key=base.groq_api_key,
        gemini_api_key=base.gemini_api_key,
        cors_origins=base.cors_origins,
        data_dir=base.data_dir,
    )

    try:
        cases = load_cholecystectomy_cases(limit_per_label=args.limit_per_label)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 1

    llm = build_llm_client(settings)
    agent = AgentService(knowledge=KnowledgeService(settings), llm=llm)

    print(
        f"Running {len(cases)} cases · provider={settings.llm_provider} · model={settings.model_id}"
    )
    results: list[CaseResult] = []
    for case in cases:
        result = await _run_case(agent, case, settings.model_id)
        results.append(result)
        mark = "OK" if result.correct_hard else "FAIL"
        print(
            f"[{mark}] {result.label:8} día={result.dia_postop} "
            f"pred_escalate={result.predicted_escalate} "
            f"sev={result.severity} · {result.caso_id}"
        )
        if result.escalate_reason:
            print(f"       reason: {result.escalate_reason}")

    reds = [r for r in results if r.label == "rojo"]
    greens = [r for r in results if r.label == "verde"]
    yellows = [r for r in results if r.label == "amarillo"]
    red_hits = sum(1 for r in reds if r.predicted_escalate)
    green_fp = sum(1 for r in greens if r.predicted_escalate)
    yellow_esc = sum(1 for r in yellows if r.predicted_escalate)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": settings.llm_provider,
        "model_id": settings.model_id,
        "n_cases": len(results),
        "label_counts": dict(Counter(r.label for r in results)),
        "rojo_escalated": f"{red_hits}/{len(reds)}",
        "verde_false_positives": f"{green_fp}/{len(greens)}",
        "amarillo_escalated": f"{yellow_esc}/{len(yellows)}",
        "hard_accuracy": round(
            sum(1 for r in results if r.correct_hard) / max(1, len(results)), 3
        ),
        "missed_rojos": [r.caso_id for r in reds if not r.predicted_escalate],
        "results": [asdict(r) for r in results],
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\n=== Summary ===")
    print(f"rojo escalated:     {summary['rojo_escalated']} (target: all)")
    print(f"verde false pos:    {summary['verde_false_positives']} (lower is better)")
    print(f"amarillo escalated: {summary['amarillo_escalated']} (informational)")
    print(f"hard accuracy:      {summary['hard_accuracy']}")
    print(f"wrote {args.out}")

    if summary["missed_rojos"]:
        print("FAIL: missed rojo cases:", ", ".join(summary["missed_rojos"]))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
