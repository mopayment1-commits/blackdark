"""Security Rate Limiting Layer (#1046) tests."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from security_rate_limiting import (
    _detect_tier,
    _is_bot_like,
    check_auth_rate_limit,
    check_security_rate_limiting_production_gate,
    run_security_rate_limiting_e2e,
    security_rate_limiting_status,
)


class _FakeRequest:
    def __init__(self, *, path="/api/oracle/quick", headers=None, cookies=None):
        self.url = type("U", (), {"path": path})()
        self.headers = headers or {}
        self.cookies = cookies or {}


def test_security_rate_limiting_status():
    status = security_rate_limiting_status()
    assert status["feature"] == "security_rate_limiting"
    assert status["auth_endpoints"]["attempts_per_ip_per_5min"] == 5
    assert status["integrations"]["pay_per_request_ref"] == 908


def test_production_gate():
    gate = check_security_rate_limiting_production_gate()
    assert gate["ok"] is True
    assert gate["checks"]["auth_ip_limit"] is True
    assert gate["checks"]["pro_api_limit"] is True


def test_e2e():
    e2e = run_security_rate_limiting_e2e()
    assert e2e["all_passed"] is True


def test_auth_rate_limit_blocks(monkeypatch, tmp_path):
    from collections import defaultdict

    monkeypatch.setattr("security_rate_limiting._AUDIT_PATH", tmp_path / "audit.jsonl")
    monkeypatch.setattr("security_rate_limiting._buckets", defaultdict(list))
    for _ in range(5):
        check_auth_rate_limit(ip="1.2.3.4")
    with pytest.raises(HTTPException) as exc:
        check_auth_rate_limit(ip="1.2.3.4")
    assert exc.value.status_code == 429


def test_bot_detection():
    assert _is_bot_like(_FakeRequest(headers={})) is True
    assert _is_bot_like(_FakeRequest(headers={"user-agent": "curl/8.0"})) is True
    assert _is_bot_like(_FakeRequest(headers={"user-agent": "Mozilla/5.0 Chrome"})) is False


def test_tier_detection():
    assert _detect_tier(_FakeRequest()) == "anonymous"
    assert _detect_tier(_FakeRequest(headers={"x-bd-tier": "pro"})) == "pro"
    assert _detect_tier(_FakeRequest(cookies={"bd_token": "x"})) == "free"
