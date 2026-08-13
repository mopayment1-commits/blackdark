"""Data Trust Law — classify existing sources; never fake L2; canonical consensus."""

from __future__ import annotations

from pathlib import Path

from live_book_hub import _books, _last_update_ms, get_live_books_if_fresh, update_top_of_book


def test_binding_doc_and_manifest():
    from canonical_market_state import build_data_trust_law_manifest

    text = Path("docs/DATA_TRUST_LAW_BINDING.md").read_text(encoding="utf-8")
    assert "لا يُنفَّذ الآن" in text or "not building" in text.lower() or "لا يُنفَّذ" in text
    assert "CoinGecko" in text
    manifest = build_data_trust_law_manifest()
    assert manifest["status"] == "binding"
    assert "ingest_100_new_apis" in manifest["explicitly_not_building"]
    assert manifest["registry_honesty"]["total_registered"] >= 100
    assert manifest["registry_honesty"]["l2_decision_grade_sources"] < manifest["registry_honesty"]["total_registered"]


def test_coingecko_is_not_decision_grade_l2():
    from data_source_trust import classify_source, classify_venue, l2_honesty_allowed

    row = classify_source("coingecko_prices")
    assert row["source_class"] == "aggregator"
    assert row["l2_decision_grade"] is False
    assert row["price_decision_grade"] is False
    assert l2_honesty_allowed(book_origin="synthetic", source_class="aggregator") is False
    assert l2_honesty_allowed(book_origin="venue_l2", source_class="venue_direct") is True
    venue = classify_venue("binance")
    assert venue["decision_grade"] is True
    assert venue["book_origin"] == "venue_l2"


def test_synthetic_book_flagged_on_coingecko_snapshot():
    from coingecko_cex_fetcher import _market_snapshots

    ticker, book = _market_snapshots(
        exchange_id="pionex",
        symbol="BTC/USDT",
        price=100.0,
        volume=1.0,
        market_type="spot",
    )
    assert ticker.decision_grade is False
    assert ticker.price_origin == "aggregator"
    assert book.decision_grade is False
    assert book.book_origin == "synthetic"


def test_consensus_quarantine_and_single_source_penalty():
    from data_trust_engine import apply_data_trust_gate, cross_source_consensus, make_observation

    a = make_observation(
        source="binance_spot",
        venue="binance",
        instrument="BTC",
        data_type="l2",
        raw_value=100.0,
        normalized_value=100.0,
        book_origin="venue_l2",
        latency_ms=200,
    )
    b = make_observation(
        source="coinbase_spot",
        venue="coinbase",
        instrument="BTC",
        data_type="l2",
        raw_value=100.05,
        normalized_value=100.05,
        book_origin="venue_l2",
        latency_ms=250,
    )
    ok = cross_source_consensus([a, b])
    assert ok["action"] == "accept"
    assert ok["canonical_value"] is not None

    fake = make_observation(
        source="coingecko_prices",
        venue="pionex",
        instrument="BTC",
        data_type="l2",
        raw_value=100.0,
        normalized_value=100.0,
        book_origin="synthetic",
        latency_ms=200,
    )
    rejected = cross_source_consensus([fake])
    assert rejected["action"] == "reject"
    assert rejected["rejected"]

    single = cross_source_consensus([a])
    assert single["action"] == "penalize"
    assert single["confidence_penalty"] > 0

    outlier = make_observation(
        source="kraken_spot",
        venue="kraken",
        instrument="BTC",
        data_type="l2",
        raw_value=108.0,
        normalized_value=108.0,
        book_origin="venue_l2",
        latency_ms=200,
    )
    clash = cross_source_consensus([a, b, outlier], max_rel_spread=0.0025, outlier_rel=0.0015)
    assert clash["action"] in {"quarantine", "accept"}
    if clash["action"] == "quarantine":
        assert clash["quarantined"]

    score, meta = apply_data_trust_gate(80.0, observations=[fake])
    assert meta["veto"] is True
    assert score <= 49.0

    untouched, idle = apply_data_trust_gate(80.0, observations=None)
    assert idle["action"] == "not_applied"
    assert untouched == 80.0


def test_canonical_state_ignores_synthetic_hub_rows():
    _books.clear()
    _last_update_ms.clear()
    update_top_of_book("binance", "BTC/USDT", bid=100.0, bid_qty=2.0, ask=100.1, ask_qty=2.0)
    update_top_of_book("okx", "BTC/USDT", bid=100.02, bid_qty=2.0, ask=100.12, ask_qty=2.0)
    update_top_of_book(
        "pionex",
        "BTC/USDT",
        bid=99.0,
        bid_qty=1.0,
        ask=101.0,
        ask_qty=1.0,
        decision_grade=False,
        book_origin="synthetic",
    )
    try:
        from canonical_market_state import build_canonical_market_state

        state = build_canonical_market_state("BTC")
        venues = {row["venue"] for row in state["observations"]}
        assert "pionex" not in venues
        assert "binance" in venues
        assert state["canonical_value"] is not None
        fresh = get_live_books_if_fresh(max_age_ms=10_000)
        assert fresh is not None
        books, _age = fresh
        assert "pionex" not in books
        assert "binance" in books
    finally:
        _books.clear()
        _last_update_ms.clear()


def test_registry_still_has_catalog_but_not_all_decision_grade():
    from data_sources_registry import registry_summary

    summary = registry_summary()
    assert summary["total_sources"] >= 100
    trust = summary["trust"]
    assert trust["l2_decision_grade_sources"] < trust["total_registered"]
    assert trust["by_source_class"]["aggregator"] >= 1


def test_routes_and_denylist_wired():
    from api.routers import heroes as heroes_router
    from trust_os import OVERCLAIM_DENYLIST, strategy_correction_manifest

    paths = {getattr(r, "path", None) for r in heroes_router.router.routes}
    assert "/api/strategy/data-trust-law" in paths
    assert "/api/public/canonical-market-state" in paths
    assert "/api/public/data-trust-closure" in paths
    claims = " ".join(row["claim"] for row in OVERCLAIM_DENYLIST)
    assert "100 APIs" in claims
    corr = strategy_correction_manifest()
    assert "hundred_source_ingestion_swamp" in corr["not_building"]
    canon = Path("docs/CANONICAL_BINDING.md").read_text(encoding="utf-8")
    assert "DATA_TRUST_LAW_BINDING.md" in canon


def test_synthetic_only_hub_rejects_canonical_and_gate():
    _books.clear()
    _last_update_ms.clear()
    update_top_of_book(
        "pionex",
        "BTC/USDT",
        bid=99.0,
        bid_qty=1.0,
        ask=101.0,
        ask_qty=1.0,
        decision_grade=False,
        book_origin="synthetic",
    )
    try:
        from canonical_market_state import build_canonical_market_state, live_book_posture
        from data_trust_engine import apply_data_trust_gate

        assert live_book_posture("BTC")["posture"] == "synthetic_only"
        state = build_canonical_market_state("BTC")
        assert state["action"] == "reject"
        assert state["reason"] == "synthetic_only"
        assert state["license"]["redistribution_allowed"] is False
        score, meta = apply_data_trust_gate(80.0, observations=[], hub_posture="synthetic_only")
        assert meta["veto"] is True
        assert score <= 49.0
    finally:
        _books.clear()
        _last_update_ms.clear()


def test_news_primary_beats_rewrite():
    from data_trust_engine import select_news_authority

    winner = select_news_authority(
        [
            {"title": "Blog rewrite", "source_class": "news_secondary"},
            {"title": "SEC press release", "source_class": "regulatory_primary"},
        ]
    )
    assert winner is not None
    assert winner["source_class"] == "regulatory_primary"


def test_institutional_closure_all_done():
    from data_trust_engine import build_data_trust_closure
    from decision_certificate import build_decision_certificate

    closure = build_data_trust_closure()
    assert closure["deferred_code_count"] == 0, closure["deferred_code_items"]
    assert closure["all_done_for_agreed_scope"] is True
    cert = build_decision_certificate(
        {
            "symbol": "BTC",
            "verdict": "WAIT",
            "opportunity_score": 55,
            "canonical_market_state": {
                "canonical_value": 100.1,
                "action": "accept",
                "venue_count": 2,
            },
        }
    )
    assert cert["canonical_value"] == 100.1
    assert cert["data_trust_action"] == "accept"
    assert "Canonical value" in cert["export_text"]
    fred = Path("ingestion_fetchers.py").read_text(encoding="utf-8")
    assert "vintage" in fred and "revision_policy" in fred
    html = Path("templates/coverage_honesty.html").read_text(encoding="utf-8")
    assert "decision-grade" in html
    adapter = Path("api/v1/oracle_adapter.py").read_text(encoding="utf-8")
    assert adapter.find("attach_data_trust") < adapter.find("build_decision_certificate")
    assert "stamp_license" in adapter.split("def build_v1_feed", 1)[1]
