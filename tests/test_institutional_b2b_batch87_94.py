"""Tests — Institutional B2B (#87–#94)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import institutional_b2b_layer as inst


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset(seed):
    inst.reset_institutional_b2b_state()
    yield
    inst.reset_institutional_b2b_state()


def test_87_ic_report(seed):
    report = inst.build_ic_report_87(asset="ETH", verdict="Risk", risk_score=7.5, seed=seed)
    assert report["ok"] is True
    assert report["report"]["disclaimer"]["every_page"] is True
    assert "html" in report["formats"]


def test_88_rbac_matrix(seed):
    status = inst.team_rbac_status_88(seed=seed)
    assert status["permission_matrix"]["viewer"]["export"] is False
    assert status["permission_matrix"]["analyst"]["export"] is True


def test_88_rbac_check(seed):
    allowed = inst.check_team_permission_88(role="analyst", action="export", user_email="u@test.com")
    assert allowed["allowed"] is True
    denied = inst.check_team_permission_88(role="viewer", action="export")
    assert denied["allowed"] is False


def test_89_sla_deferred(seed):
    assert inst.sla_status_89(seed=seed)["status"] == "deferred"


def test_90_white_label_deferred(seed):
    assert inst.white_label_status_90(seed=seed)["status"] == "deferred"


def test_91_vwap(seed):
    vwap = inst.compute_vwap_deviation_91(seed=seed)
    assert vwap["vwap"] > 0
    assert "formula" in vwap


def test_92_counterparty(seed):
    ex = inst.build_exchange_health_with_counterparty_92(seed=seed)
    assert "counterparty_risk" in ex
    assert ex["merged_features"] == [80, 92]


def test_93_calibration(seed):
    cal = inst.compute_confidence_calibration_93(
        declared_confidence_pct=90,
        journal_entries=[{"outcome": "missed"}, {"outcome": "missed"}],
        seed=seed,
    )
    assert cal["calibration_score"] > 0
    assert cal["behavioral_learning_only"] is True


def test_94_audit_export(seed):
    assert inst.audit_export_status_94(seed=seed)["status"] == "deferred"
    inst.check_team_permission_88(role="admin", action="view")
    export = inst.export_rbac_audit_94()
    assert len(export["checksum_sha256"]) == 64


def test_institutional_b2b_e2e(seed):
    assert inst.run_institutional_b2b_e2e_87_94(seed=seed)["all_passed"] is True
