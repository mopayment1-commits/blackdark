"""Sonar new-code coverage — B2B / fund terminal / evidence surfaces."""

from __future__ import annotations

import asyncio

import pytest
from starlette.testclient import TestClient


def test_evidence_public_summary_body():
    from evidence_public_summary import build_evidence_public_summary, get_cached_evidence_public_summary

    body = build_evidence_public_summary()
    assert "product_thesis" in body
    assert "differentiators" in body
    cached = get_cached_evidence_public_summary()
    assert cached["full_pack"] == "/api/due-diligence/evidence-pack"


@pytest.mark.asyncio
async def test_build_fund_terminal_pack_shape(monkeypatch):
    import emerging_fund_terminal as eft

    monkeypatch.setattr(eft, "_FUND_PACK_CACHE", {})
    monkeypatch.setattr(eft, "_FUND_PACK_CACHE_TTL_SEC", 0.0)
    pack = await eft.build_fund_terminal_pack(fund_name="Sonar Fund")
    assert pack.get("segment")
    assert "dd_export" in pack
    assert "allocator_checklist" in pack


def test_b2b_elite_and_institutional_href_helpers():
    from dashboard import _b2b_elite_cta_href, _b2b_institutional_cta_href
    from starlette.requests import Request

    scope = {"type": "http", "method": "GET", "path": "/b2b", "headers": []}
    req = Request(scope)
    req.state.header_user = None
    assert "login" in _b2b_elite_cta_href(req)
    assert "login" in _b2b_institutional_cta_href(req)
    req.state.header_user = {"email": "u@example.com", "name": "U", "tier": "pro"}
    assert "create-checkout-session" in _b2b_elite_cta_href(req)
    assert "data-room" in _b2b_institutional_cta_href(req)


def test_b2b_page_renders_evidence_controls(monkeypatch):
    monkeypatch.delenv("EXPOSE_B2B_DEMO_KEY", raising=False)
    from dashboard import app

    client = TestClient(app, raise_server_exceptions=False)
    html = client.get("/b2b").text
    assert "loadEvidenceSummary" in html
    assert "ROOT_CAUSE" not in html  # guide is docs-only
    assert "evidenceFullMsg" in html
