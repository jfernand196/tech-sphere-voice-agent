#!/usr/bin/env python3
"""Download Kokoro int8 model + voices and warm the ONNX session."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402

MODEL_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files-v1.0/kokoro-v1.0.int8.onnx"
)
VOICES_URL = (
    "https://github.com/thewh1teagle/kokoro-onnx/releases/download/"
    "model-files-v1.0/voices-v1.0.bin"
)


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1_000_000:
        print(f"OK exists {dest} ({dest.stat().st_size // (1024 * 1024)} MB)")
        return
    print(f"Downloading {url} → {dest}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(dest)
    print(f"OK {dest} ({dest.stat().st_size // (1024 * 1024)} MB)")


def main() -> int:
    settings = get_settings()
    _download(MODEL_URL, settings.kokoro_model_path)
    _download(VOICES_URL, settings.kokoro_voices_path)
    from app.voice.kokoro_engine import KokoroEngine

    engine = KokoroEngine(settings)
    engine.warmup()
    print(f"warm-kokoro OK voice={settings.kokoro_voice}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
