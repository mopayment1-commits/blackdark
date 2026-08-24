"""Tests — Security Controls and Circuit Breakers (#190)."""

from __future__ import annotations

import json
import time

import pytest

from bd_platform import security_circuit_breakers as scb


@pytest.fixture
def isolated_cb_paths(tmp_path, monkeypatch):
    audit = tmp_path / "audit.jsonl"
    state = tmp_path / "state.json"
    alerts = tmp_path / "alerts.jsonl"
    monkeypatch.setattr(scb, "_AUDIT_PATH", audit)
    monkeypatch.setattr(scb, "_STATE_PATH", state)
    monkeypatch.setattr(scb, "_ALERTS_PATH", alerts)
    scb.reset_circuit_breaker(reason="test_setup")
    return audit, state, alerts


def test_circuit_does_not_trip_below_sample_gate(isolated_cb_paths):
    """False-positive guard: need ≥20 samples before trip."""
    for _ in range(10):
        scb.record_request_outcome(success=False)
    result = scb.evaluate_circuit_breaker()
    assert result["tripped"] is False
    assert scb.is_platform_shutdown() is False


def test_circuit_opens_at_50_percent_error_rate(isolated_cb_paths):
    """50% error rate with sufficient samples trips breaker."""
    for i in range(30):
        scb.record_request_outcome(success=(i % 2 == 0))
    result = scb.evaluate_circuit_breaker()
    assert result["tripped"] is True
    assert scb.is_platform_shutdown() is True
    status = scb.circuit_breaker_status()
    assert status["status"] == "open"
    assert status["platform_shutdown"] is True


def test_admin_reset_closes_circuit(isolated_cb_paths):
    for i in range(30):
        scb.record_request_outcome(success=(i % 2 == 0))
    scb.evaluate_circuit_breaker()
    assert scb.is_platform_shutdown() is True

    reset = scb.reset_circuit_breaker(reason="investigation_complete")
    assert reset["ok"] is True
    assert reset["status"] == "closed"
    assert scb.is_platform_shutdown() is False


def test_audit_log_written_on_trip(isolated_cb_paths):
    audit_path, _, _ = isolated_cb_paths
    for _ in range(25):
        scb.record_request_outcome(success=False)
    scb.evaluate_circuit_breaker()
    events = scb.recent_audit_events(limit=10)
    assert any(e["action"] == "circuit_breaker_opened" for e in events)
    assert audit_path.is_file()


def test_should_block_request_when_open(isolated_cb_paths):
    for _ in range(25):
        scb.record_request_outcome(success=False)
    scb.evaluate_circuit_breaker()
    assert scb.should_block_request("/api/oracle/query") is True
    assert scb.should_block_request("/api/health") is False
    assert scb.should_block_request("/api/security/status") is False


def test_suspicious_login_detection(isolated_cb_paths, monkeypatch):
    events = [
        {
            "ts": time.time(),
            "kind": "login_failed",
            "ip": "203.0.113.50",
            "severity": "warning",
        }
        for _ in range(6)
    ]

    def fake_recent(**_kwargs):
        return events

    monkeypatch.setattr("security_events.recent_security_events", fake_recent)
    result = scb.scan_threat_patterns()
    login_alerts = [a for a in result["alerts"] if a["kind"] == "suspicious_login"]
    assert len(login_alerts) >= 1
    assert login_alerts[0]["failure_count"] >= 5


def test_circuit_breaker_status_sla(isolated_cb_paths):
    status = scb.circuit_breaker_status()
    assert status["ok"] is True
    assert status["feature_id"] == 190
    assert status["sla_met"] is True
    assert status["monitoring_24_7"] is True
