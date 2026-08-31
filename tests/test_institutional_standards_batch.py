"""Tests — Institutional standards + launch center."""

from __future__ import annotations

import pytest

from bd_platform import institutional_standards as istd


def test_standards_status():
    status = istd.institutional_standards_status()
    assert status["unknown_is_not_zero"] is True
    assert len(status["evidence_classes"]) == 4
    assert len(status["user_journeys"]) >= 5


def test_wrap_intelligence_response():
    wrapped = istd.wrap_intelligence_response({"ok": True, "display": "test panel"})
    assert wrapped["evidence_class"] in istd.EVIDENCE_CLASSES
    assert wrapped["compliance_footer"]
    assert wrapped["no_advisory_language"] is True


def test_advisory_scan_catches_banned():
    bad = istd.enforce_no_advisory({"text": "you should buy now"})
    assert bad["no_advisory_language"] is False


def test_missing_value_not_zero():
    assert istd.missing_value(numeric=True) is None
    assert istd.missing_value() == "غير متوفر"


def test_user_journey_map():
    journeys = istd.user_journey_map()
    paths = {j["path"] for j in journeys}
    assert "/intelligence-ledger" in paths
    assert "/launch-center" in paths


def test_launch_center_page():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/launch-center").status_code == 200
    assert "Launch Center" in c.get("/launch-center").text
    assert c.get("/api/institutional-standards/status").status_code == 200


def test_evidence_middleware_on_il_route():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    r = c.get("/api/platform/intelligence-ledger/intelligence-layer/market-conditions/status")
    assert r.status_code == 200
    data = r.json()
    assert "evidence_class" in data
    assert "compliance_footer" in data


@pytest.mark.asyncio
async def test_live_market_strip():
    from bd_platform.live_market_context import build_live_market_strip

    strip = await build_live_market_strip()
    assert strip.get("ok") is True
    assert strip.get("unknown_is_not_zero") is True
