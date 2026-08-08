"""Tests for path / URL / host safety helpers (Sonar hardening)."""

from __future__ import annotations

from pathlib import Path

import pytest

from path_safety import assert_safe_http_url, resolve_under, safe_url_segment


def test_resolve_under_confines_path(tmp_path: Path):
    target = resolve_under(tmp_path, "nested", "file.json")
    assert target.is_relative_to(tmp_path.resolve())


def test_resolve_under_rejects_escape(tmp_path: Path):
    with pytest.raises(ValueError):
        resolve_under(tmp_path, "..", "escape.txt")


def test_safe_url_segment_allowlist():
    assert safe_url_segment("BTC-USDT") == "BTC-USDT"
    with pytest.raises(ValueError):
        safe_url_segment("../etc")


def test_assert_safe_http_url_localhost_only():
    assert assert_safe_http_url("http://127.0.0.1:8080/health").startswith("http")
    with pytest.raises(ValueError):
        assert_safe_http_url("http://evil.example/steal")
