#!/usr/bin/env python3
"""Live smoke of the running API (not unit tests). Requires: make backend."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any, Tuple

BASE = "http://127.0.0.1:8001"


def _req(method: str, path: str, body: dict | None = None) -> Tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        f"{BASE}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            raw = res.read().decode("utf-8")
            return res.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = raw
        return exc.code, payload
    except urllib.error.URLError as exc:
        raise SystemExit(f"FAIL connect {BASE}: {exc.reason}") from exc


def _ok(name: str, cond: bool, detail: str = "") -> None:
    mark = "OK" if cond else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{mark}] {name}{suffix}")
    if not cond:
        raise SystemExit(1)


def main() -> None:
    code, health = _req("GET", "/health")
    _ok("health reachable", code == 200, str(health.get("status") if isinstance(health, dict) else health))
    assert isinstance(health, dict)
    _ok("llm_ready", bool(health.get("llm_ready")), health.get("llm_detail", ""))
    _ok(
        "rag_ok",
        bool(health.get("rag_ok")),
        f"docs={health.get('rag_docs')} chunks={health.get('rag_chunks')}",
    )
    _ok("rag has vectors", int(health.get("rag_chunks") or 0) > 0)

    code, caps = _req("GET", "/voice/capabilities")
    _ok("voice capabilities", code == 200 and isinstance(caps, dict))
    engines = (caps or {}).get("engines") or {}
    _ok("browser TTS engine listed", "browser" in engines)

    code, docs = _req("GET", "/knowledge/documents")
    _ok("list documents", code == 200 and isinstance(docs, list), f"n={len(docs) if isinstance(docs, list) else 0}")

    queries = [
        "me duele la herida y tengo fiebre",
        "temperatura alta y escalofríos",
        "náuseas después de la cirugía",
    ]
    for q in queries:
        code, hits = _req("POST", "/knowledge/query", {"query": q, "top_k": 3})
        n = len(hits) if isinstance(hits, list) else 0
        _ok(f"RAG query: {q!r}", code == 200 and n > 0, f"hits={n}")
        if isinstance(hits, list) and hits:
            top = hits[0]
            print(f"       top: score={top.get('score')} title={str(top.get('title', ''))[:70]}")

    code, patients = _req("GET", "/demo/patients")
    _ok("demo patients", code == 200 and isinstance(patients, list) and len(patients) > 0)

    code, started = _req(
        "POST",
        "/calls/start",
        {
            "patient_name": "Smoke Test",
            "procedure": "colecistectomia",
            "dia_postop": 3,
        },
    )
    _ok("start call", code == 200 and isinstance(started, dict) and started.get("call_id"))
    call_id = started["call_id"]

    code, turn = _req(
        "POST",
        f"/calls/{call_id}/turn",
        {
            "call_id": call_id,
            "message": "Me duele un poco la herida y tengo 38 de fiebre.",
        },
    )
    _ok(
        "agent turn",
        code == 200 and isinstance(turn, dict) and bool(turn.get("reply")),
        f"http={code} escalate={turn.get('escalate') if isinstance(turn, dict) else turn}",
    )
    if isinstance(turn, dict):
        sources = turn.get("sources") or []
        print(f"       sources={len(sources)} latency_ms={turn.get('latency_ms')}")

    code, summary = _req(
        "POST",
        f"/calls/{call_id}/end",
        {"e2e_latency_ms": []},
    )
    _ok("end call", code == 200 and isinstance(summary, dict), f"http={code}")

    # Negative: empty TTS text should 422
    code, _ = _req("POST", "/voice/tts", {"text": ""})
    _ok("tts rejects empty text", code == 422)

    print("\nAll smoke checks passed.")


if __name__ == "__main__":
    main()
