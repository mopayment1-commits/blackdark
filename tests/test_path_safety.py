"""Tests for path / URL / host safety helpers (Sonar hardening)."""

from __future__ import annotations

from pathlib import Path

import pytest

from path_safety import assert_safe_http_url, coerce_json_mapping, resolve_under, safe_url_segment


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
    assert assert_safe_http_url("[REDACTED]/health").startswith("http")
    with pytest.raises(ValueError):
        assert_safe_http_url("http://evil.example/steal")


def test_coerce_json_mapping_rebuilds_nested_document():
    raw = {"closure_status": "PENDING_CLOSURE", "scripts": [{"exit_code": 0}], "count": 3}
    clean = coerce_json_mapping(raw)
    assert clean["closure_status"] == "PENDING_CLOSURE"
    assert clean["scripts"][0]["exit_code"] == 0
    assert clean["count"] == 3
