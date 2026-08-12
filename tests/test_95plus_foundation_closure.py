"""95+ Phase Zero / P0 regression gates — foundations + Critical/High closures."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_baseline_register_exists():
    path = ROOT / "docs/dd/CURRENT_PRODUCT_TRUTH_BASELINE.md"
    text = path.read_text(encoding="utf-8")
    assert "e00971a034043046f4eefd3df1807c7b59101859" in text
    assert "STILL_PRESENT" in text
    assert "R-SSO-01" in text
    assert "Canonical Data Layer" in text


def test_canonical_data_layer_normalize_and_stale_gate():
    from canonical_data_layer import (
        FreshnessClass,
        assert_not_stale_as_live,
        ingest_quote,
        live_payload_or_raise,
        normalize_symbol,
        normalize_venue,
        reset_store_for_tests,
    )

    reset_store_for_tests()
    assert normalize_venue("OKEX") == "okx"
    assert normalize_symbol("btcusdt") == "BTC/USDT"

    live = ingest_quote(
        venue="binance",
        symbol="BTC/USDT",
        bid=100.0,
        ask=100.1,
        source="ws:binance",
        provider_timestamp=datetime.now(UTC),
    )
    assert live.provenance.freshness_class is FreshnessClass.LIVE
    assert live_payload_or_raise(live)["symbol"] == "BTC/USDT"

    stale = ingest_quote(
        venue="okx",
        symbol="ETH/USDT",
        bid=10.0,
        ask=10.1,
        source="ws:okx",
        provider_timestamp=datetime.now(UTC) - timedelta(seconds=60),
        # override ages via ingest defaults — 60s is STALE vs 10s degraded max
    )
    assert stale.provenance.freshness_class is FreshnessClass.STALE
    with pytest.raises(ValueError, match="stale_as_live_forbidden"):
        assert_not_stale_as_live(stale.provenance.freshness_class)
    with pytest.raises(ValueError, match="stale_as_live_forbidden"):
        live_payload_or_raise(stale)


def test_canonical_rejects_malformed_quote():
    from canonical_data_layer import ingest_quote, reset_store_for_tests

    reset_store_for_tests()
    with pytest.raises(ValueError):
        ingest_quote(
            venue="binance",
            symbol="BTC/USDT",
            bid=100.0,
            ask=99.0,
            source="ws",
            provider_timestamp=datetime.now(UTC),
        )


def test_stream_freshness_cannot_fake_live():
    from stream_freshness_truth import fanout_safe, label_tick, reject_stale_as_live

    now = int(time.time() * 1000)
    live = fanout_safe(label_tick(exchange="binance", symbol="BTC/USDT", bid=1, ask=1.1, provider_ts_ms=now))
    assert live["is_live"] is True
    assert live["display_badge"] == "LIVE"

    stale = label_tick(
        exchange="binance",
        symbol="BTC/USDT",
        bid=1,
        ask=1.1,
        provider_ts_ms=now - 60_000,
    )
    assert stale["freshness_class"] == "STALE"
    safe = fanout_safe(stale)
    assert safe["is_live"] is False
    assert safe["display_badge"] == "STALE"

    forged = dict(stale)
    forged["is_live"] = True
    with pytest.raises(ValueError, match="stale_as_live_forbidden"):
        reject_stale_as_live(forged)


def test_funding_without_depth_is_not_emitted():
    import config
    from arbitrage_engine import calculate_funding_arbitrage

    symbol = config.perpetual_symbols()[0]
    venues = list(config.enabled_exchanges())[:2]
    rates = {
        venues[0]: {symbol: {"funding_rate": 0.001}},
        venues[1]: {symbol: {"funding_rate": -0.0005}},
    }
    # No order books → fail closed (empty)
    assert calculate_funding_arbitrage(rates, quote_amount=1000.0) == []
    # Indicative research path allowed but never executable
    rows = calculate_funding_arbitrage(
        rates,
        quote_amount=1000.0,
        allow_indicative_without_depth=True,
    )
    assert rows
    assert all(r.indicative and not r.executable and not r.depth_verified for r in rows)


def test_funding_with_depth_computes_slippage():
    import config
    from arbitrage_engine import _perpetual_book_key, calculate_funding_arbitrage

    symbol = config.perpetual_symbols()[0]
    venues = list(config.enabled_exchanges())[:2]
    rates = {
        venues[0]: {symbol: {"funding_rate": 0.002}},
        venues[1]: {symbol: {"funding_rate": -0.001}},
    }
    # Deep books so walk succeeds; invent spread so slip > 0
    def book(mid: float = 100.0):
        # Multi-level book so average price diverges from top-of-book (slippage > 0).
        return {
            "bids": [[mid - 0.1, 0.2], [mid - 1.0, 50.0], [mid - 2.0, 50.0]],
            "asks": [[mid + 0.1, 0.2], [mid + 1.0, 50.0], [mid + 2.0, 50.0]],
            "market_type": "perpetual",
        }

    books = {
        venues[0]: {_perpetual_book_key(symbol): book(100.0)},
        venues[1]: {_perpetual_book_key(symbol): book(100.0)},
    }
    rows = calculate_funding_arbitrage(rates, quote_amount=500.0, order_books=books)
    assert rows
    assert rows[0].depth_verified is True
    assert rows[0].total_slippage_bps > 0
    assert rows[0].executable == (rows[0].net_yield_usdt > 0)


def test_confidence_never_claims_probability_for_heuristic():
    from confidence_truth import claim_calibrated_probability, claim_heuristic, sanitize_confidence_field

    h = claim_heuristic(0.87).to_dict()
    assert h["is_probability"] is False
    assert "heuristic_score" in h["display"]

    insuff = claim_calibrated_probability(0.9, sample_size=3).to_dict()
    assert insuff["confidence_type"] == "insufficient_evidence"
    assert insuff["display"] == "I_DONT_KNOW"

    ok = claim_calibrated_probability(0.62, sample_size=100, brier_score=0.1).to_dict()
    assert ok["is_probability"] is True

    sanitized = sanitize_confidence_field(0.55)
    assert sanitized["confidence_type"] == "heuristic_score"


def test_decision_graph_and_memory_append_only(tmp_path, monkeypatch):
    import decision_graph as dg
    import institutional_memory as im

    monkeypatch.setattr(dg, "_PATH", tmp_path / "decision_graph.jsonl")
    monkeypatch.setattr(dg, "_DATA_BASE", tmp_path)
    monkeypatch.setattr(im, "_PATH", tmp_path / "institutional_memory.jsonl")
    monkeypatch.setattr(im, "_DATA_BASE", tmp_path)

    bundle = dg.record_decision_bundle(
        market_state={"regime": "risk_on"},
        evidence=[{"source": "funding", "note": "spread"}],
        contradictions=[{"note": "whale outflow"}],
        hypothesis={"view": "mean_revert"},
        decision={"action": "stand_down"},
        risk={"gate": "pass"},
        execution_feasibility={"executable": False, "reason": "insufficient_depth"},
        confidence=0.7,
    )
    nodes = dg.query_graph(bundle["graph_id"])
    kinds = {n.get("kind") for n in nodes}
    assert "DECISION" in kinds
    assert "EXECUTION_FEASIBILITY" in kinds
    # confidence typed
    dec = next(n for n in nodes if n.get("kind") == "DECISION")
    assert dec["payload"]["confidence"]["confidence_type"] == "heuristic_score"

    out = dg.attach_outcome(
        bundle["graph_id"],
        decision_node_id=bundle["decision_node_id"],
        outcome={"pnl": 0},
    )
    learn = dg.attach_learning(
        bundle["graph_id"],
        outcome_node_id=out["node_id"],
        learning={"lesson": "wait_for_depth"},
    )
    assert learn["payload"]["hindsight_rewrite_forbidden"] is True

    mem = im.remember("decision", {"graph_id": bundle["graph_id"]}, graph_id=bundle["graph_id"])
    assert mem["immutable"] is True
    assert im.query(graph_id=bundle["graph_id"])


def test_risk_intelligence_fail_closed_and_gates():
    from risk_intelligence import (
        aggregate_risk_gate,
        flash_crash_risk,
        liquidity_risk,
        smart_contract_risk,
        stress_test_portfolio,
    )

    liq = liquidity_risk(symbol="BTC/USDT", notional=10_000, bid_depth=None, ask_depth=None, spread_bps=None)
    assert liq["executable"] is False
    assert liq["gate"] == "fail_closed"

    flash = flash_crash_risk(returns_bps=[-900, -100], window_sec=60)
    assert flash["gate"] == "block"

    sc = smart_contract_risk(
        protocol="mystery",
        audited=None,
        upgradeable=True,
        tvl_usd=1000,
        incident_count=2,
    )
    assert sc["executable"] is False

    stress = stress_test_portfolio(positions=[{"notional_usd": None}])
    assert stress["gate"] == "fail_closed"

    agg = aggregate_risk_gate([liq, flash])
    assert agg["blocked"] is True
    assert agg["executable"] is False


def test_oms_lifecycle_and_idempotency(tmp_path, monkeypatch):
    import oms

    monkeypatch.setattr(oms, "_PATH", tmp_path / "oms_orders.json")
    monkeypatch.setattr(oms, "_DATA_BASE", tmp_path)

    a = oms.create_intent(
        org_id="org1",
        venue="binance",
        symbol="BTC/USDT",
        side="buy",
        quantity=1.0,
        idempotency_key="k1",
        actor="tester",
        limit_price=100.0,
    )
    b = oms.create_intent(
        org_id="org1",
        venue="binance",
        symbol="BTC/USDT",
        side="buy",
        quantity=1.0,
        idempotency_key="k1",
        actor="tester",
        limit_price=100.0,
    )
    assert a["order_id"] == b["order_id"]

    row = oms.transition(a["order_id"], "VALIDATION", actor="tester")
    row = oms.transition(row["order_id"], "RISK_CHECK", actor="tester")
    row = oms.transition(row["order_id"], "ROUTING", actor="tester")
    row = oms.transition(row["order_id"], "SUBMISSION", actor="tester")
    row = oms.transition(row["order_id"], "ACK", actor="tester", venue_ack_id="ex-1")
    row = oms.transition(row["order_id"], "FILL", actor="tester", fill_qty=1.0)
    row = oms.transition(row["order_id"], "RECONCILE", actor="tester")
    assert row["state"] == "RECONCILE"

    with pytest.raises(ValueError, match="illegal_transition"):
        oms.transition(row["order_id"], "ACK", actor="tester")

    st = oms.oms_status()
    assert st["not_execution_engine"] is True


def test_b2b_ops_surfaces(tmp_path, monkeypatch):
    import b2b_institutional_ops as b2b

    monkeypatch.setattr(b2b, "_REPORTS", tmp_path / "b2b_reports.jsonl")
    monkeypatch.setattr(b2b, "_ALERTS", tmp_path / "alert_orchestration.jsonl")
    monkeypatch.setattr(b2b, "_SLA", tmp_path / "sla_events.jsonl")
    monkeypatch.setattr(b2b, "_DATA_BASE", tmp_path)

    rpt = b2b.generate_committee_report(
        org_id="org",
        title="Weekly",
        evidence_pack={"decisions": 1},
        actor="risk",
    )
    assert rpt["report_id"]
    al = b2b.orchestrate_alert(
        org_id="org",
        severity="high",
        channel="pager",
        message="liquidity gate",
        dedupe_key="liq-1",
    )
    assert al["status"] == "queued"
    sla = b2b.record_sla_event(org_id="org", metric="api_p95", value=900, target=500)
    assert sla["breached"] is True
    assert b2b.b2b_status()["product_complete"] is True


def test_cex_dex_remains_indicative_not_executable():
    from bd_platform.cex_dex_arbitrage import scan_cex_dex_opportunities
    import inspect

    src = Path(inspect.getfile(scan_cex_dex_opportunities)).read_text(encoding="utf-8")
    assert '"executable": False' in src
    assert "indicative" in src
