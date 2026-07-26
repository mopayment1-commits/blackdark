"""Alias — استخدم connect_platform_keys.py للعملية الكاملة."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONNECT = Path(__file__).resolve().parent / "connect_platform_keys.py"

spec = importlib.util.spec_from_file_location("connect_platform_keys", CONNECT)
if spec is None or spec.loader is None:
    raise SystemExit(f"Cannot load {CONNECT}")
mod = importlib.util.module_from_spec(spec)
sys.modules["connect_platform_keys"] = mod
spec.loader.exec_module(mod)

if __name__ == "__main__":
    raise SystemExit(mod.main())
