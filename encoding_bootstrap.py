"""Windows + web UTF-8 bootstrap for Arabic text."""

from __future__ import annotations

import os
import sys


def configure_stdio_utf8() -> None:
    """Force UTF-8 for console output on Windows (Arabic in Terminal/scripts)."""
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


# Auto-configure on import for web + scripts
configure_stdio_utf8()
