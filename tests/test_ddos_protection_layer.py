"""DDoS Protection Layer (#1047) tests."""

from __future__ import annotations

from ddos_protection_layer import (
    check_ddos_protection_production_gate,
    ddos_protection_status,
    record_ddos_event,
    run_ddos_protection_e2e,
    trigger_ddos_incident,
)


def test_ddos_protection_status():
    status = ddos_protection_status()
    assert status["feature"] == "ddos_protection_layer"
    assert status["standalone_rejected"] is True
    assert status["integrations"]["rate_limiting_ref"] == 1046
    assert status["templates_present"]["nginx"] is True


def test_production_gate():
    gate = check_ddos_protection_production_gate()
    assert gate["feature"] == "ddos_protection_layer"
    assert gate["checks"]["rate_limit_integration"] is True


def test_e2e():
    e2e = run_ddos_protection_e2e()
    assert e2e["all_passed"] is True


def test_record_event_and_incident(tmp_path, monkeypatch):
    audit = tmp_path / "audit.jsonl"
    monkeypatch.setattr("ddos_protection_layer._AUDIT_PATH", audit)
    event = record_ddos_event(
        attack_type="volumetric_udp",
        source_ips=["1.2.3.4"],
        mitigation="cloudflare_absorption",
    )
    assert event["attack_type"] == "volumetric_udp"
    assert audit.is_file()
    incident = trigger_ddos_incident(event)
    assert incident["triggered"] is True
    assert incident["integration_ref"] == 1017
