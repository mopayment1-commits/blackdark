"""Tests — GDPR Compliance Layer (#1023 Sprint-0 Infrastructure)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import infrastructure_gdpr_compliance_layer as gdpr


@pytest.fixture
def gdpr_seed() -> dict:
    return json.loads(
        Path("data/infrastructure_gdpr_compliance_seed.json").read_text(encoding="utf-8")
    )


@pytest.fixture(autouse=True)
def reset_state():
    gdpr.reset_gdpr_compliance_state()
    yield
    gdpr.reset_gdpr_compliance_state()


def test_1023_status_no_standalone(gdpr_seed):
    status = gdpr.gdpr_compliance_status_1023(seed=gdpr_seed)
    assert status["standalone_rejected"] is True
    assert status["sprint"] == 0
    assert status["integrations"]["retention_ref"] == 949
    assert status["policy"]["soft_delete_grace_days"] == 30


def test_data_residency_mapping(gdpr_seed):
    residency = gdpr.get_data_residency_map_1023(seed=gdpr_seed)
    assert residency["eu_users_eu_storage"] is True
    assert len(residency["datasets"]) >= 3
    assert gdpr.resolve_storage_region(user_region="EU", seed=gdpr_seed) == "eu-west-1"


def test_explicit_consent_no_preticked(gdpr_seed):
    ok = gdpr.record_explicit_consent_1023(
        user_id=1,
        consent_type="sensitive_data",
        granted=True,
        preticked=False,
        seed=gdpr_seed,
    )
    assert ok["ok"] is True
    assert ok["consent"]["immutable"] is True

    bad = gdpr.record_explicit_consent_1023(
        user_id=1,
        consent_type="sensitive_data",
        granted=True,
        preticked=True,
        seed=gdpr_seed,
    )
    assert bad["ok"] is False
    assert bad["error"] == "preticked_consent_forbidden"


@pytest.mark.asyncio
async def test_soft_delete_grace_period(gdpr_seed):
    result = await gdpr.request_account_deletion_1023(
        user_id=42,
        email="delete@example.com",
        user_region="EU",
        seed=gdpr_seed,
    )
    assert result["ok"] is True
    assert result["request"]["status"] == "soft_deleted"
    assert result["request"]["grace_days"] == 30
    assert result["request"]["session_invalidation"]["ok"] is True
    assert result["request"]["stripe_coordination"]["stripe_cleanup_requested"] is True
    assert result["request"]["provenance_propagation"]["lineage_propagated"] is True


@pytest.mark.asyncio
async def test_hard_delete_blocked_during_grace(gdpr_seed):
    await gdpr.request_account_deletion_1023(
        user_id=42,
        email="grace@example.com",
        seed=gdpr_seed,
    )
    blocked = await gdpr.execute_hard_delete_1023(email="grace@example.com", seed=gdpr_seed)
    assert blocked["ok"] is False
    assert blocked["error"] == "grace_period_active"


@pytest.mark.asyncio
async def test_portability_json_and_csv(gdpr_seed):
    json_export = await gdpr.export_portable_data_1023(email="test@example.com", fmt="json", seed=gdpr_seed)
    assert json_export["portability"]["format"] == "json"
    assert json_export["portability"]["data_export_ref"] == 924

    csv_export = await gdpr.export_portable_data_1023(email="test@example.com", fmt="csv", seed=gdpr_seed)
    assert "csv" in csv_export["portability"]
    assert csv_export["portability"]["fee_db"]["fee_db_logged"] is True


def test_breach_notification_playbook(gdpr_seed):
    playbook = gdpr.get_breach_notification_playbook_1023(seed=gdpr_seed)
    assert playbook["supervisory_authority_hours"] == 72
    assert playbook["incident_response_ref"] == 1017
    assert playbook["tested"] is True


def test_dpo_contact(gdpr_seed):
    dpo = gdpr.get_dpo_contact_1023(seed=gdpr_seed)
    assert dpo["visible_in_privacy_policy"] is True
    assert "dpo@" in dpo["dpo_email"]


def test_retention_alignment_949(gdpr_seed):
    retention = gdpr.get_retention_alignment_1023(seed=gdpr_seed)
    assert retention["retention_ref"] == 949
    assert retention["schedules"]["personal_data"] == "account_lifetime_plus_30_days"
    assert retention["schedules"]["logs"] == "2_years"
    assert retention["schedules"]["audit"] == "5_years"


def test_data_minimization(gdpr_seed):
    policy = gdpr.get_data_minimization_policy_1023(seed=gdpr_seed)
    assert "email" in policy["collected"]
    assert policy["kyc_institution_only"] is True


def test_production_gate(gdpr_seed):
    gate = gdpr.check_production_gate_1023(seed=gdpr_seed)
    assert gate["blocks_production"] is True
    assert gate["production_allowed"] is True


@pytest.mark.asyncio
async def test_e2e_all_checks(gdpr_seed):
    e2e = await gdpr.run_gdpr_compliance_e2e_1023(seed=gdpr_seed)
    assert e2e["all_passed"] is True
    failed = [c for c in e2e["checks"] if not c["passed"]]
    assert failed == [], f"Failed: {failed}"
