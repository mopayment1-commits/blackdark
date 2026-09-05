"""Suspicious Activity Alert Engine tests."""

from __future__ import annotations

import pytest

from suspicious_activity_engine import (
    check_suspicious_activity_production_gate,
    device_fingerprint,
    dispatch_suspicious_alert,
    evaluate_login_context,
    on_mfa_change,
    run_suspicious_activity_e2e,
    suspicious_activity_status,
    whitelist_location,
)


def test_suspicious_activity_status():
    status = suspicious_activity_status()
    assert status["feature"] == "suspicious_activity_engine"
    assert len(status["triggers"]) == 5
    assert status["rule_based_only"] is True


def test_production_gate():
    gate = check_suspicious_activity_production_gate()
    assert gate["ok"] is True
    assert gate["checks"]["five_triggers"] is True


def test_e2e():
    e2e = run_suspicious_activity_e2e()
    assert e2e["all_passed"] is True


def test_device_fingerprint():
    fp1 = device_fingerprint(user_agent="Mozilla/5.0", accept_language="en")
    fp2 = device_fingerprint(user_agent="Mozilla/5.0", accept_language="en")
    fp3 = device_fingerprint(user_agent="curl/8.0")
    assert fp1 == fp2
    assert fp1 != fp3


def test_new_location_triggers_alert(tmp_path, monkeypatch):
    baselines = tmp_path / "baselines.json"
    audit = tmp_path / "audit.jsonl"
    monkeypatch.setattr("suspicious_activity_engine._BASELINES_PATH", baselines)
    monkeypatch.setattr("suspicious_activity_engine._AUDIT_PATH", audit)

    # First login — baseline, no alert
    assert evaluate_login_context(user_id=42, ip="10.0.0.1", user_agent="Mozilla") is None
    # Second login from new IP — alert
    alert = evaluate_login_context(user_id=42, ip="10.0.0.99", user_agent="Mozilla")
    assert alert is not None
    assert alert["trigger"] == "new_ip_geolocation"


def test_whitelist_suppresses_alert(tmp_path, monkeypatch):
    baselines = tmp_path / "baselines.json"
    audit = tmp_path / "audit.jsonl"
    monkeypatch.setattr("suspicious_activity_engine._BASELINES_PATH", baselines)
    monkeypatch.setattr("suspicious_activity_engine._AUDIT_PATH", audit)

    evaluate_login_context(user_id=7, ip="10.0.0.1")
    from suspicious_activity_engine import approximate_location

    loc = approximate_location(ip="10.0.0.99")
    whitelist_location(7, loc)
    assert evaluate_login_context(user_id=7, ip="10.0.0.99") is None


def test_mfa_change_critical(tmp_path, monkeypatch):
    audit = tmp_path / "audit.jsonl"
    monkeypatch.setattr("suspicious_activity_engine._AUDIT_PATH", audit)
    alert = on_mfa_change(1, action="disabled", ip="1.2.3.4")
    assert alert["severity"] == "critical"
    assert alert["trigger"] == "mfa_disable_or_change"
