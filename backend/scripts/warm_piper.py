#!/usr/bin/env python3
"""Download Piper Spanish (MX) voices and warm the ONNX session."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402

VOICES = ("es_MX-ald-medium", "es_MX-claude-high")


def main() -> int:
    settings = get_settings()
    settings.piper_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "piper.download_voices",
        "--download-dir",
        str(settings.piper_dir),
        *VOICES,
    ]
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))

    from app.voice.piper_engine import PiperEngine

    engine = PiperEngine(settings)
    engine.warmup()
    print(f"warm-piper OK voice={settings.piper_voice} dir={settings.piper_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
