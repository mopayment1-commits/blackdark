"""Brand + coverage radical closure — miss feed, provenance, honesty board."""

from __future__ import annotations

import asyncio
from pathlib import Path


def test_provenance_score_honesty():
    from data_provenance_score import attach_provenance, compute_data_provenance_score

    score = compute_data_provenance_score(symbol="BTC", freshness_ms=500, venue_count=8)
    assert score["score"] >= 55
    assert score["band"] in {"decision_grade", "caution", "insufficient"}
    assert "planned" not in score["honesty"].lower() or "never" in score["honesty"].lower()
    payload = attach_provenance({"symbol": "ETH", "freshness_ms": 900})
    assert "data_provenance" in payload
    assert payload["provenance_score"] == payload["data_provenance"]["score"]


def test_coverage_honesty_board():
    from coverage_honesty import build_coverage_honesty_board

    board = asyncio.run(build_coverage_honesty_board())
    assert board["surface"] == "coverage_honesty_board"
    assert board["radical_fix"]["status"] == "honesty_surface_not_product_complete"
    assert "live" in board
    assert "healthy" in board["live"]["label"].lower() or "live_ingestion" in board["live"]["label"].lower()


def test_public_miss_feed_and_emotion_tax():
    from emotion_tax_receipt import build_emotion_tax_receipt
    from public_miss_feed import build_public_miss_feed

    feed = asyncio.run(build_public_miss_feed(limit=10))
    assert feed["surface"] == "public_miss_feed"
    assert feed["page"] == "/miss-feed"
    assert "share_urls" in feed
    tax = build_emotion_tax_receipt(user_key="closure_tester", overrides=3, notional_usd=1000)
    assert tax["estimated_emotion_tax_usd"] > 0
    assert "anon" in tax["share_text"].lower() or tax["user_key_hash"]


def test_brand_coverage_closure_all_done():
    from brand_proof_engine import build_brand_coverage_radical_closure

    closure = asyncio.run(build_brand_coverage_radical_closure())
    assert closure["product_complete"] is False
    assert closure["all_done"] is True
    assert len(closure["problems_closed"]) == 2
    assert all(c["done"] for c in closure["checklist"])


def test_wiring_pages_and_routes():
    heroes = Path("api/routers/heroes.py").read_text(encoding="utf-8")
    dash = Path("dashboard.py").read_text(encoding="utf-8")
    assert "/api/public/miss-feed" in heroes
    assert "/api/public/coverage-honesty" in heroes
    assert "/api/oracle/provenance-score" in heroes
    assert "/api/public/brand-coverage-closure" in heroes
    assert "/miss-feed" in dash
    assert "/coverage-honesty" in dash
    assert "/emotion-tax" in dash
    for p in (
        "templates/miss_feed.html",
        "templates/coverage_honesty.html",
        "templates/emotion_tax.html",
        "public_miss_feed.py",
        "coverage_honesty.py",
        "data_provenance_score.py",
        "brand_proof_engine.py",
        "emotion_tax_receipt.py",
    ):
        assert Path(p).exists()


def test_oracle_freshness_attaches_provenance():
    from data_freshness import attach_oracle_freshness

    out = attach_oracle_freshness({"symbol": "BTC", "freshness_ms": 800})
    assert out["data_freshness"]["state"] in {"fresh", "ok", "stale", "unknown"}
    assert "data_provenance" in out
