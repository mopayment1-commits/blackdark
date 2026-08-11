"""Tests — technical due diligence + GDPR DSR."""

from __future__ import annotations

import pytest


def test_gdpr_status():
    from gdpr_service import gdpr_compliance_status

    status = gdpr_compliance_status()
    assert status["ready_for_dd"] is True
    assert "/api/privacy/dsr/export" in status["dsr_export_api"]


@pytest.mark.asyncio
async def test_gdpr_export_unknown_user():
    from gdpr_service import export_user_data

    out = await export_user_data("nonexistent-dd-test@example.com")
    assert out["found"] is False
    assert out["subject_email"] == "nonexistent-dd-test@example.com"


@pytest.mark.asyncio
async def test_gdpr_erase_requires_confirm():
    from gdpr_service import erase_user_data

    out = await erase_user_data("test@example.com", confirmed=False)
    assert out["status"] == "confirmation_required"


@pytest.mark.asyncio
async def test_technical_dd_report_structure():
    from technical_due_diligence import build_technical_due_diligence_report

    report = await build_technical_due_diligence_report(probe_production=False)
    assert report["overall_verdict"] in {"pass", "partial", "fail"}
    assert len(report["requirements"]) == 20
    for req in report["requirements"]:
        assert req["verdict"] in {"PASS", "FAIL", "PARTIALLY PASS", "NOT APPLICABLE"}
        assert req["id"] >= 1
        assert req["id"] <= 20


def test_sanitize_oracle_strips_internal_verdict():
    from security_sanitize import sanitize_oracle_payload

    out = sanitize_oracle_payload(
        {"verdict": "BUY", "oracle": "Buy Now at $100", "opportunity_score": 80, "symbol": "BTC"}
    )
    assert "oracle_internal_verdict" not in out
    assert out.get("is_investment_advice") is False
