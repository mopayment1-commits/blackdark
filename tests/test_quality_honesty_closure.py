"""Quality Honesty Soft Launch closure — zero deferred code, no world-class myth."""

from __future__ import annotations

import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient


def test_quality_honesty_closure_shape():
    from quality_honesty_closure import build_quality_honesty_closure

    closure = asyncio.run(build_quality_honesty_closure())
    assert closure["surface"] == "quality_honesty_soft_launch_closure"
    assert closure["world_class_100_complete"] is False
    assert closure["all_done_for_agreed_scope"] is True
    assert closure["product_complete_for_soft_launch_honesty"] is True
    assert closure["code_complete_zero_deferred"] is True
    assert closure["deferred_code_items"] == []
    assert closure["deferred_code_count"] == 0
    assert closure["total_areas"] == 16
    assert closure["world_class_100_count"] == 0
    assert closure["soft_launch_ready_count"] == 16
    assert all(a["code_complete"] is True and a["deferred_code"] is False for a in closure["areas"])
    white = next(a for a in closure["areas"] if a["id"] == "white_label")
    assert white["tier"] == "out_of_scope_not_deferred"
    assert "white_label" in closure["out_of_scope_not_deferred"]
    assert "soc2_certified" in closure["forbidden_claims"]
    assert "white_label_ready" in closure["forbidden_claims"]
    assert closure["strict_confirmation"]["zero_deferred_code"] is True
    assert closure["strict_confirmation"]["percent_complete_agreed_scope"] == 100
    assert closure["strict_confirmation"]["percent_complete_world_class_myth"] == 0
    assert "/quality-honesty" in closure["pages"]


def test_provenance_block_labels():
    from quality_honesty_closure import provenance_block

    live = provenance_block(
        surface="onchain_overview",
        mode="api",
        live_legs=["exchange_flow_api"],
        proxy_or_mock_legs=[],
        claim_boundary="test",
    )["quality_provenance"]
    assert live["live"] is True
    assert live["world_class_100"] is False

    mixed = provenance_block(
        surface="sentiment_overview",
        mode="mixed",
        live_legs=["rss"],
        proxy_or_mock_legs=["twitter_mock"],
        claim_boundary="test",
    )["quality_provenance"]
    assert mixed["mixed"] is True
    assert mixed["proxy_or_simulated"] is True


def test_portfolio_analyze_attaches_provenance():
    from dashboard import _analyze_portfolio_holdings

    result = asyncio.run(
        _analyze_portfolio_holdings([{"symbol": "BTC", "amount": 0.01, "price": 50000}])
    )
    assert "quality_provenance" in result
    assert result["quality_provenance"]["surface"] == "portfolio_ai"
    assert result["quality_provenance"]["world_class_100"] is False
    assert "btc_beta_heuristic" in result["quality_provenance"]["proxy_or_mock_legs"]


def test_wiring_docs_and_public_surface():
    heroes = Path("api/routers/heroes.py").read_text(encoding="utf-8")
    public = Path("public_api_docs.py").read_text(encoding="utf-8")
    dash = Path("dashboard.py").read_text(encoding="utf-8")
    gtm = Path("api/routers/gtm.py").read_text(encoding="utf-8")
    dash_html = Path("templates/dashboard.html").read_text(encoding="utf-8")
    assert "/api/public/quality-honesty-closure" in heroes
    assert "/api/public/quality-honesty-closure" in public
    assert "quality_honesty" in gtm
    assert "provenance_block" in dash
    assert "/quality-honesty" in dash
    assert "quality_provenance" in dash_html
    assert Path("quality_honesty_closure.py").exists()
    assert Path("templates/quality_honesty.html").exists()
    assert Path("docs/QUALITY_HONESTY_SOFT_LAUNCH_AR.md").exists()
    assert "quality-honesty" in Path("docs/DATA_ROOM.md").read_text(encoding="utf-8")
    assert "Quality Honesty Soft Launch" in Path("templates/utility.html").read_text(encoding="utf-8")


def test_public_api_docs_includes_quality_honesty():
    from public_api_docs import path_is_public

    assert path_is_public("/api/public/quality-honesty-closure") is True
    assert path_is_public("/quality-honesty") is True


def test_risk_status_keeps_honest_scope():
    from risk_manager import risk_status

    status = risk_status()
    assert "honest_scope" in status
    assert "institutional VaR 99% desk" in " ".join(status["honest_scope"]["not_shipped"])


async def _get_json(path: str) -> dict:
    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get(path)
        assert r.status_code == 200, (path, r.status_code, r.text[:300])
        return r.json()


def test_quality_honesty_api_and_overview_provenance():
    closure = asyncio.run(_get_json("/api/public/quality-honesty-closure"))
    assert closure["world_class_100_complete"] is False
    assert closure["all_done_for_agreed_scope"] is True
    assert closure["code_complete_zero_deferred"] is True
    assert closure["deferred_code_count"] == 0

    for path in (
        "/api/sentiment/overview",
        "/api/onchain/overview",
        "/api/macro/overview",
        "/api/research/moat",
    ):
        body = asyncio.run(_get_json(path))
        assert "quality_provenance" in body, path
        assert body["quality_provenance"]["world_class_100"] is False

    # research_lab is tier-gated; assert wiring + builder provenance contract instead.
    assert "provenance_block" in Path("dashboard.py").read_text(encoding="utf-8")
    assert 'surface="research_lab"' in Path("dashboard.py").read_text(encoding="utf-8")

    sec = asyncio.run(_get_json("/api/security/status"))
    assert sec["quality_honesty"]["world_class_100"] is False
    assert sec["quality_honesty"]["api"] == "/api/public/quality-honesty-closure"

    launch = asyncio.run(_get_json("/api/launch/readiness"))
    assert launch["quality_honesty"]["soft_launch_honesty_complete"] is True
    assert launch["quality_honesty"]["world_class_100_complete"] is False


def test_quality_honesty_html_page():
    from dashboard import app

    async def _run():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/quality-honesty")
            assert r.status_code == 200
            assert "Quality Honesty" in r.text
            assert "/api/public/quality-honesty-closure" in r.text

    asyncio.run(_run())
