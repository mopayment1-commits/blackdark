"""CodeQL hygiene ported onto morning-final branch (safe_errors + secret IO helper)."""
from __future__ import annotations

from pathlib import Path


def test_safe_errors_module_present():
    from safe_errors import public_error, public_error_payload

    assert public_error(RuntimeError("boom /workspace/secret"), fallback="Request failed") == "Request failed"
    assert "secret" not in public_error_payload(RuntimeError("token=abc"))["error"]


def test_secret_io_helper_present():
    src = Path("scripts/_secret_io.py").read_text(encoding="utf-8")
    assert "mask_secret" in src
    assert "write_private_text" in src


def test_dashboard_imports_public_error():
    src = Path("dashboard.py").read_text(encoding="utf-8")
    assert "from safe_errors import public_error" in src
    assert "/api/legal/ack-terms" in src
    assert "/system/info" in src
