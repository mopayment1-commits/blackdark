"""dashboard.py must not contain NUL bytes (breaks import/compile on some hosts)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "dashboard.py"


def test_dashboard_py_has_no_null_bytes():
    data = DASHBOARD.read_bytes()
    assert b"\x00" not in data, "dashboard.py contains null bytes; strip \\x00 before deploy"


def test_dashboard_py_compiles():
    source = DASHBOARD.read_text(encoding="utf-8")
    compile(source, str(DASHBOARD), "exec")
