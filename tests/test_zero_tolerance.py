"""Zero-Tolerance binding — seven trust-destroying defects, zero deferred code."""

from __future__ import annotations

import asyncio
from pathlib import Path

from httpx import ASGITransport, AsyncClient


def test_gates_unit():
    from zero_tolerance import (
        alert_requires_relevance,
        apply_zero_tolerance,
        detect_fake_precision,
        live_label_allowed,
        score_requires_why,
    )

    assert live_label_allowed({"state": "stale", "stale": True})["violated"] is True
    assert live_label_allowed({"state": "fresh", "freshness_ms": 200})["live_label_allowed"] is True
    assert score_requires_why(score=87, why_text=None)["violated"] is True
    assert score_requires_why(score=87, why_text="funding extreme", factors=["a"])["violated"] is False
    assert detect_fake_precision("BTC will reach $124,721 in 17 hours")["violated"] is True
    assert detect_fake_precision("Base case range with invalidation at funding flip")["violated"] is False
    assert alert_requires_relevance(title="x", why_for_you=None)["violated"] is True
    assert alert_requires_relevance(title="x", why_for_you="Your book is long BTC")["violated"] is False

    audited = apply_zero_tolerance(
        {
            "opportunity_score": 70,
            "oqs_why": {"why_text": "why", "top_3_factors": [{"factor": "a"}]},
            "data_freshness": {"state": "fresh", "freshness_ms": 300},
            "data_sources": ["live_book"],
            "live_label": "LIVE",
        }
    )
    assert audited["zero_tolerance"]["pass"] is True
    assert audited["live_claim_allowed"] is True


def test_closure_complete():
    from zero_tolerance import build_zero_tolerance_closure

    # Closure builder is sync (dict-returning); do not wrap with asyncio.run.
    closure = build_zero_tolerance_closure()
    assert closure["defect_count"] == 7
    assert closure["all_done_for_agreed_scope"] is True
    assert closure["deferred_code_count"] == 0
    assert closure["code_complete_zero_deferred"] is True
    assert closure["strict_confirmation"]["percent_complete_agreed_scope"] == 100
    assert closure["strict_confirmation"]["live_requires_freshness"] is True


def test_wiring():
    assert Path("zero_tolerance.py").exists()
    assert Path("docs/ZERO_TOLERANCE_BINDING_AR.md").exists()
    assert Path("templates/zero_tolerance.html").exists()
    heroes = Path("api/routers/heroes.py").read_text(encoding="utf-8")
    dash = Path("dashboard.py").read_text(encoding="utf-8")
    pulse = Path("trust_pulse.py").read_text(encoding="utf-8")
    assert "/api/strategy/zero-tolerance" in heroes
    assert "/api/public/zero-tolerance-closure" in heroes
    assert "apply_zero_tolerance" in dash
    assert "apply_zero_tolerance" in pulse
    assert "ZERO_TOLERANCE_BINDING_AR.md" in Path("docs/CANONICAL_BINDING.md").read_text(encoding="utf-8")
    from public_api_docs import path_is_public

    assert path_is_public("/api/public/zero-tolerance-closure")
    assert path_is_public("/zero-tolerance")


def test_http_surfaces():
    async def _run():
        from dashboard import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.get("/api/public/zero-tolerance-closure")
            assert r.status_code == 200
            body = r.json()
            assert body["all_done_for_agreed_scope"] is True
            assert body["deferred_code_count"] == 0

            m = await client.get("/api/strategy/zero-tolerance")
            assert m.status_code == 200
            assert m.json()["defect_count"] == 7

            p = await client.get("/zero-tolerance")
            assert p.status_code == 200
            assert "Zero-Tolerance" in p.text

            t = await client.get("/api/trust-os")
            assert t.status_code == 200
            assert "zero_tolerance" in t.json()

    asyncio.run(_run())
