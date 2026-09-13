"""Regression: CodeQL py/stack-trace-exposure sinks stay closed."""

from __future__ import annotations

from pathlib import Path


def test_scale_readiness_artifact_error_is_type_only():
    src = Path("scale_readiness.py").read_text(encoding="utf-8")
    assert 'payload["artifact_error"] = str(exc)' not in src
    assert 'payload["artifact_error"] = type(exc).__name__' in src


def test_vendor_rate_limit_status_never_returns_str_exc():
    src = Path("ops/vendor_rate_limit_watchdog.py").read_text(encoding="utf-8")
    assert '"error": str(exc)' not in src
    assert '"error": type(exc).__name__' in src


def test_build_info_cap646_error_is_type_only():
    src = Path("dashboard.py").read_text(encoding="utf-8")
    assert "cap646_import_error = str(exc)" not in src
    assert "cap646_import_error = type(exc).__name__" in src


def test_runtime_verification_no_detail_str_exc():
    src = Path("runtime_verification.py").read_text(encoding="utf-8")
    assert '"detail": str(exc)' not in src
