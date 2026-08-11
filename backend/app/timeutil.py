"""Shared UTC clock (one place — avoid duplicate `_utcnow` helpers)."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
