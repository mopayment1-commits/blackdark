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
    import config
    import institutional_store as store
    import oms

    monkeypatch.setattr(oms, "_PATH", tmp_path / "oms_orders.json")
    monkeypatch.setattr(oms, "_DATA_BASE", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "oms_lifecycle.db")
    monkeypatch.setattr(config, "DATABASE_URL", "")
    store._READY_FOR = None  # noqa: SLF001

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


def test_decision_intelligence_engine_stand_down(tmp_path, monkeypatch):
    import decision_graph as dg
    import institutional_memory as im
    from decision_intelligence_engine import evaluate_decision
    from risk_intelligence import liquidity_risk

    monkeypatch.setattr(dg, "_PATH", tmp_path / "decision_graph.jsonl")
    monkeypatch.setattr(dg, "_DATA_BASE", tmp_path)
    monkeypatch.setattr(im, "_PATH", tmp_path / "institutional_memory.jsonl")
    monkeypatch.setattr(im, "_DATA_BASE", tmp_path)

    blocked = liquidity_risk(
        symbol="BTC/USDT",
        notional=1_000_000,
        bid_depth=1000,
        ask_depth=1000,
        spread_bps=5,
    )
    out = evaluate_decision(
        market_state={"regime": "stress"},
        evidence=[{"k": "v"}],
        hypothesis={"view": "fade"},
        decision={"action": "enter", "wants_action": True},
        risk_reports=[blocked],
        confidence=0.9,
    )
    assert out["executable"] is False
    assert out["action"]["type"] == "stand_down"
    assert out["confidence"]["confidence_type"] == "heuristic_score"


def test_scim_honesty_endpoint(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "scim-honesty-admin-key")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    monkeypatch.setenv("SCIM_BEARER_TOKEN", "scim-honesty-bearer")
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    denied = client.get("/api/institutional/scim/status")
    assert denied.status_code in {401, 403}
    headers = {"X-Admin-Key": "scim-honesty-admin-key"}
    st = client.get("/api/institutional/scim/status", headers=headers)
    assert st.status_code == 200
    body = st.json()
    assert body["scim_ready"] is True
    assert body["product_complete"] is True
    assert body["bearer_configured"] is True


def test_oms_decision_api_wired(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "oms-decision-admin-key")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    from fastapi.testclient import TestClient

    from dashboard import app

    client = TestClient(app)
    headers = {"X-Admin-Key": "oms-decision-admin-key"}
    oms_st = client.get("/api/institutional/oms/status", headers=headers)
    assert oms_st.status_code == 200
    assert "lifecycle" in oms_st.json() or oms_st.json().get("surface")
    dg = client.get("/api/institutional/decision-graph/status", headers=headers)
    assert dg.status_code == 200
    di = client.get("/api/institutional/decision-intelligence/status", headers=headers)
    assert di.status_code == 200


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
        channel="inbox",
        message="liquidity gate",
        dedupe_key="liq-1",
    )
    assert al["status"] == "delivered"
    assert al.get("delivery", {}).get("delivered") is True
    pending = b2b.orchestrate_alert(
        org_id="org",
        severity="high",
        channel="pager",
        message="needs connector",
        dedupe_key="liq-pager",
    )
    assert pending["status"] == "accepted_pending_connector"
    assert pending.get("delivery", {}).get("delivered") is False
    sla = b2b.record_sla_event(org_id="org", metric="api_p95", value=900, target=500)
    assert sla["breached"] is True
    assert b2b.b2b_status()["alert_delivery"] is True
    assert b2b.b2b_status()["implementation_class"] == "PARTIAL"


def test_cex_dex_depth_aware_and_executor_blocks_indicative():
    from pathlib import Path
    import inspect
    import asyncio
    from bd_platform.cex_dex_arbitrage import scan_cex_dex_opportunities, _cex_dex_row
    from bd_platform.cex_dex_executor import execute_cex_dex_opportunity

    src = Path(inspect.getfile(scan_cex_dex_opportunities)).read_text(encoding="utf-8")
    assert "depth_verified" in src
    assert "impact_bps_estimate" in src
    assert "cex_l2_walk_verified" in src
    # Without CEX L2 walk, never executable — even with huge DEX liquidity.
    row = _cex_dex_row(
        "BTC",
        {"binance": 100.0},
        100.0,
        {"price": 99.0, "venue": "jupiter", "liquidity_usd": 10_000_000.0},
        "jupiter",
        99.0,
        "binance",
        100.0,
        100.0,
        80.0,
        1000.0,
        fee_bps=10.0,
        cex_l2_walk_verified=False,
    )
    assert row["executable"] is False
    assert row["indicative"] is True
    assert row["cex_l2_walk_verified"] is False
    assert row["indicative_reason"] == "cex_l2_walk_required"

    async def _run():
        return await execute_cex_dex_opportunity(row, dry_run=True)

    out = asyncio.run(_run())
    assert out["blocked"] is True


def test_stream_lifecycle_gap_duplicate_outage_failover():
    from streaming_institutional import (
        StreamLifecycleManager,
        reset_stream_lifecycle_for_tests,
        streaming_control_plane,
    )

    reset_stream_lifecycle_for_tests()
    m = StreamLifecycleManager()
    m.register_subscription("binance", "BTC/USDT", worker_id="w1")
    assert m.heartbeat("binance")["alive"] is True
    assert m.mark_message("binance", seq=1)["ok"] is True
    dup = m.mark_message("binance", seq=1)
    assert dup["duplicate"] is True
    assert dup["ok"] is False
    gap = m.mark_message("binance", seq=5)
    assert gap["gap"] is True
    outage = m.mark_outage("binance", failover_to="okx")
    assert outage["executable_quotes"] is False
    assert m.mark_message("binance", seq=6)["ok"] is False
    assert m.reconnect("binance")["recovery"] is True
    assert m.is_alive("binance")["alive"] is True
    plane = streaming_control_plane()
    assert plane["stale_as_live"] == 0
    assert "gap_detection" in plane["controls"]


def test_portfolio_and_stress_fail_closed_unknown_notional():
    from portfolio_intelligence import analyze_portfolio
    from stress_testing import run_stress_battery

    bad = analyze_portfolio([{"asset": "BTC", "side": "long"}])
    assert bad["executable_analysis"] is False
    assert bad["reason"] == "notional_unknown"

    positions = [
        {"asset": "BTC", "side": "long", "notional_usd": 500_000, "unrealized_pnl_usd": -1000},
        {"asset": "ETH", "side": "long", "notional_usd": 200_000, "unrealized_pnl_usd": 500},
        {"asset": "SOL", "side": "long", "notional_usd": 200_000, "unrealized_pnl_usd": 100},
        {"asset": "BNB", "side": "long", "notional_usd": 100_000, "unrealized_pnl_usd": 50},
    ]
    good = analyze_portfolio(positions)
    assert good["herfindahl"] > 0
    # Concentration/contagion may block executable_analysis — still a valid analysis result
    assert "correlation" in good
    assert good.get("gate") in {"pass", "block"}
    battery = run_stress_battery(positions)
    assert battery["scenarios"]
    names = {s["scenario"] for s in battery["scenarios"]}
    assert "market_crash" in names
    assert "protocol_failure" in names


def test_alert_ack_silence_dedupe():
    import b2b_institutional_ops as b2b

    a1 = b2b.orchestrate_alert(
        org_id="org-x",
        severity="critical",
        channel="pager",
        message="flash",
        dedupe_key="flash-1",
    )
    a2 = b2b.orchestrate_alert(
        org_id="org-x",
        severity="critical",
        channel="pager",
        message="flash",
        dedupe_key="flash-1",
    )
    assert a2.get("deduplicated") is True
    ack = b2b.acknowledge_alert(a1["alert_id"], actor="ops")
    assert ack["status"] == "acked"
    sil = b2b.silence_alert(a1["alert_id"], actor="ops", reason="known")
    assert sil["status"] == "silenced"
