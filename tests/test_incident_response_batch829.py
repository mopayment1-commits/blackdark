"""Tests — Batch: #829 Incident Response & Security Operations (SEC-009 Sprint-0)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import infrastructure_incident_response_security_ops as ir


@pytest.fixture
def ir_seed() -> dict:
    return json.loads(
        Path("data/infrastructure_incident_response_seed.json").read_text(encoding="utf-8")
    )


@pytest.fixture(autouse=True)
def reset_state():
    ir.reset_incident_response_state()
    yield
    ir.reset_incident_response_state()


def test_829_status_policy(ir_seed):
    status = ir.incident_response_status_829(seed=ir_seed)
    assert status["standalone_rejected"] is True
    assert status["legacy_ref"] == 1017
    assert status["control_ref"] == "SEC-009"
    assert status["sprint"] == 0
    policy = status["policy"]
    assert len(policy["scenarios"]) == 5
    assert policy["no_guaranteed_uptime"] is True
    assert policy["audit_retention_years"] == 5
    assert policy["audit_immutable"] is True


def test_829_roles_documented(ir_seed):
    roles = ir.incident_response_status_829(seed=ir_seed)["policy"]["roles"]
    for role in ("incident_commander", "communications_lead", "technical_lead", "legal_advisor"):
        assert role in roles
        assert roles[role]["accessible_24_7"] is True


def test_829_escalation_sla(ir_seed):
    esc = ir.get_escalation_policy_829(seed=ir_seed)
    assert esc["oncall_ack_minutes"] == 5
    assert esc["commander_notify_minutes"] == 15
    assert esc["legal_on_data_leak"] is True


def test_829_all_runbook_scenarios(ir_seed):
    for scenario in ("breach", "data_leak", "service_outage", "ddos", "key_compromise"):
        rb = ir.get_runbook_scenario_829(scenario, seed=ir_seed)
        assert rb["ok"] is True
        assert rb["documented"] is True
        assert len(rb["steps"]) >= 5


def test_829_isolation_playbooks(ir_seed):
    iso = ir.get_isolation_playbooks_829(seed=ir_seed)
    for action in ("api_kill_switch", "firewall_rules", "db_read_only", "tenant_isolation_trigger"):
        assert action in iso["playbooks"]
    assert iso["test_interval_days"] == 90


def test_829_notification_template_no_guarantee(ir_seed):
    tmpl = ir.get_notification_template_829("critical_investigating", seed=ir_seed)
    assert tmpl["no_guaranteed_uptime"] is True
    assert tmpl["forbidden_phrases_absent"] is True
    assert tmpl["sla_hours"] == 1


def test_829_record_incident_triggers_dr(ir_seed):
    inc = ir.record_incident_829(scenario="service_outage", severity="critical", seed=ir_seed)
    assert inc["incident"]["audit_logged"] is True
    assert inc["dr_playbook_triggered"] is True
    assert inc["incident"]["append_only"] is True


def test_829_tenant_containment(ir_seed):
    inc = ir.record_incident_829(scenario="data_leak", tenant_id="tenant_x", seed=ir_seed)
    assert inc["incident"]["tenant_contained"] is True


def test_829_escalation_within_sla(ir_seed):
    inc = ir.record_incident_829(scenario="breach", seed=ir_seed)
    esc = ir.record_escalation_829(
        incident_id=inc["incident"]["incident_id"],
        level="oncall",
        notified_role="oncall_engineer",
        minutes_elapsed=4,
        seed=ir_seed,
    )
    assert esc["escalation"]["sla_met"] is True


def test_829_isolation_drill(ir_seed):
    drill = ir.record_isolation_drill_829(result="passed", seed=ir_seed)
    assert drill["ok"] is True
    assert drill["drill"]["no_cross_tenant_leak"] is True


def test_829_user_notification(ir_seed):
    inc = ir.record_incident_829(scenario="service_outage", seed=ir_seed)
    notify = ir.record_user_notification_829(
        incident_id=inc["incident"]["incident_id"],
        seed=ir_seed,
    )
    assert notify["ok"] is True
    assert notify["notification"]["no_guaranteed_uptime"] is True


def test_829_reject_guaranteed_uptime_language(ir_seed):
    inc = ir.record_incident_829(scenario="service_outage", seed=ir_seed)
    bad = ir.record_user_notification_829(
        incident_id=inc["incident"]["incident_id"],
        message="We guarantee immediate restore of all services.",
        seed=ir_seed,
    )
    assert bad["ok"] is False


def test_829_provenance_check(ir_seed):
    prov = ir.run_post_incident_provenance_check_829(seed=ir_seed)
    assert prov["provenance_ref"] == 945
    assert prov["lineage_integrity_passed"] is True


def test_829_billing_integrity(ir_seed):
    billing = ir.run_billing_integrity_check_829(seed=ir_seed)
    assert billing["billing_ref"] == 908
    assert billing["idempotency_replay_protection_tested"] is True


def test_829_audit_trail(ir_seed):
    ir.record_incident_829(scenario="ddos", seed=ir_seed)
    trail = ir.get_incident_audit_trail_829(seed=ir_seed)
    assert trail["entry_count"] >= 2
    assert trail["audit_retention_years"] == 5
    assert trail["immutable"] is True


def test_829_institutional_bridge(ir_seed):
    status = ir.institutional_ir_status_829(seed=ir_seed)
    assert status["control_ref"] == "SEC-009"
    assert status["no_guaranteed_uptime"] is True
    assert len(status["scenarios"]) == 5


def test_829_e2e(ir_seed):
    e2e = ir.run_incident_response_e2e_829(seed=ir_seed)
    assert e2e["all_passed"] is True
    assert len(e2e["checks"]) >= 25


def test_institutional_assurance_delegates_ir():
    from institutional_assurance import ir_program, record_tabletop

    program = ir_program()
    assert program["control_ref"] == "SEC-009"
    drill = record_tabletop(title="api_kill_switch", outcome="success", participants=["ops"])
    assert drill.get("result") == "passed" or drill.get("playbook") == "api_kill_switch"
