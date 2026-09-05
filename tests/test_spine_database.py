"""Spine database coverage tests — CLOSURE-MANDATE-LAST item 2."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest


@pytest.fixture
async def spine_db(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "spine.db"
    monkeypatch.setattr(config, "DB_PATH", str(db_path))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    await database.init_db()
    return database


@pytest.mark.asyncio
async def test_init_db_idempotent(spine_db):
    import database

    await database.init_db()
    await database.init_db()
    telemetry = await database.fetch_system_telemetry()
    assert telemetry.get("database_online") is True


@pytest.mark.asyncio
async def test_database_ddl_ssot_semantics(spine_db):
    from database_ddl import table_schema

    ddl = table_schema("platform_analytics")
    assert ddl.startswith("CREATE TABLE IF NOT EXISTS platform_analytics")
    assert ddl.rstrip().endswith(";")
    assert table_schema("journal_entries") in spine_db.SCHEMA


@pytest.mark.asyncio
async def test_deserialize_payload_json_rows(spine_db):
    import database

    rows = [{"payload_json": "{\"a\": 1}"}, {"payload_json": "not-json"}]
    out = database._deserialize_payload_json_rows(rows)
    assert out[0]["payload"] == {"a": 1}
    assert out[1]["payload"] == {}


@pytest.mark.asyncio
async def test_insert_and_fetch_pricing_log(spine_db):
    row_id = await spine_db.insert_pricing_log("binance", "BTC/USDT", 50000.0, volume=1.5, opportunity_score=0.8)
    assert row_id > 0
    telemetry = await spine_db.fetch_system_telemetry()
    assert telemetry.get("pricing_count", 0) >= 1


@pytest.mark.asyncio
async def test_insert_order_book_and_fetch_latest(spine_db):
    bids = [[49900.0, 1.0], [49800.0, 2.0]]
    asks = [[50100.0, 1.0], [50200.0, 2.0]]
    ob_id = await spine_db.insert_order_book("binance", "BTC/USDT", bids, asks)
    assert ob_id > 0
    latest = await spine_db.fetch_latest_order_books()
    assert "binance" in latest
    assert any(v.get("symbol") == "BTC/USDT" for v in latest["binance"].values())


@pytest.mark.asyncio
async def test_insert_order_books_batch(spine_db):
    ts = datetime.now(UTC).isoformat()
    rows = [
        (ts, "okx", "ETH/USDT", json.dumps([[1, 1]]), json.dumps([[2, 1]]), "spot"),
    ]
    await spine_db.insert_order_books(rows)
    books = await spine_db.fetch_latest_order_books(market_type="spot")
    assert isinstance(books, dict)


@pytest.mark.asyncio
async def test_insert_funding_rate(spine_db):
    fr_id = await spine_db.insert_funding_rate("binance", "BTC/USDT", 0.0001)
    assert fr_id > 0
    rates = await spine_db.fetch_latest_funding_rates()
    assert isinstance(rates, dict)


@pytest.mark.asyncio
async def test_insert_evaluated_opportunity(spine_db):
    oid = await spine_db.insert_evaluated_opportunity(
        kind="arb",
        asset="BTC/USDT",
        payload_json=json.dumps({"edge_bps": 12}),
        opportunity_score=0.8,
        net_profit_usdt=2.5,
        oracle_verdict="WAIT",
        oracle_sentence="test",
        explanation_json="{}",
        confidence_percent=72.0,
    )
    assert oid > 0
    rows = await spine_db.fetch_evaluated_opportunities(limit=5)
    assert len(rows) >= 1


@pytest.mark.asyncio
async def test_institutional_flows_and_feed(spine_db):
    flow_id = await spine_db.insert_institutional_flow(
        flow_type="sector_inflow_index",
        sector="defi",
        asset="ETH",
        notional_usd=1_000_000.0,
        metadata_json="{}",
    )
    assert flow_id > 0
    flows = await spine_db.fetch_latest_sector_flows(limit=5)
    assert isinstance(flows, list)
    feed = await spine_db.fetch_institutional_feed_rows(limit=10)
    assert isinstance(feed, list)
    assert await spine_db.fetch_institutional_flow_count() >= 1


@pytest.mark.asyncio
async def test_whale_alert_flow(spine_db):
    await spine_db.insert_institutional_flow(
        flow_type="whale_alert",
        asset="BTC",
        notional_usd=5_000_000.0,
        metadata_json='{"wallet":"0xabc"}',
    )
    alerts = await spine_db.fetch_latest_whale_alerts(limit=5)
    assert isinstance(alerts, list)


@pytest.mark.asyncio
async def test_compaction_and_archival(spine_db):
    cutoff = spine_db.compaction_cutoff_iso(hours=24)
    assert "T" in cutoff or "-" in cutoff
    arch_pricing = await spine_db.fetch_archivable_pricing_logs(cutoff, limit=10)
    arch_books = await spine_db.fetch_archivable_order_books(cutoff, limit=10)
    arch_sentiment = await spine_db.fetch_archivable_sentiment_logs(cutoff, limit=10)
    assert all(isinstance(x, list) for x in (arch_pricing, arch_books, arch_sentiment))


@pytest.mark.asyncio
async def test_delete_archived_rows(spine_db):
    pid = await spine_db.insert_pricing_log("binance", "BTC/USDT", 1.0)
    deleted = await spine_db.delete_pricing_logs_by_ids([pid])
    assert deleted == 1
    bid = await spine_db.insert_order_book("binance", "BTC/USDT", [[1, 1]], [[2, 1]])
    assert await spine_db.delete_order_books_by_ids([bid]) == 1


@pytest.mark.asyncio
async def test_batch_pricing_logs_insert(spine_db):
    rows = [
        ("2026-01-01T00:00:00Z", "binance", "ETH/USDT", 3000.0, 1.0, 0.5, "spot"),
        ("2026-01-01T00:01:00Z", "okx", "ETH/USDT", 3001.0, 2.0, 0.6, "spot"),
    ]
    await spine_db.insert_pricing_logs(rows)
    telemetry = await spine_db.fetch_system_telemetry()
    assert telemetry.get("pricing_count", 0) >= 2


@pytest.mark.asyncio
async def test_create_user_roundtrip(spine_db):
    uid = await spine_db.create_user(email="spine-test@blackdark.local", password_hash="x")
    assert uid > 0
    user = await spine_db.fetch_user_by_email("spine-test@blackdark.local")
    assert user is not None


@pytest.mark.asyncio
async def test_cloud_sync_log(spine_db):
    sync_id = await spine_db.insert_cloud_sync_log(
        local_path="/tmp/test.parquet",
        s3_bucket="bd-backup",
        s3_key="test/key",
        status="uploaded",
        etag="abc",
        size_bytes=1024,
    )
    assert sync_id > 0
    latest = await spine_db.fetch_latest_cloud_sync_log("/tmp/test.parquet")
    assert latest is not None
    assert latest["status"] == "uploaded"


@pytest.mark.asyncio
async def test_market_sentiment_logs(spine_db):
    sid = await spine_db.insert_market_sentiment_log(
        "BTC",
        "test",
        "bullish headline",
        0.55,
        0.12,
    )
    assert sid > 0
    logs = await spine_db.fetch_sentiment_logs_for_asset("BTC", limit=5)
    assert isinstance(logs, list)
    ts = datetime.now(UTC).isoformat()
    batch = [
        (ts, "ETH", None, "test", "neutral", 0.6, 0.1),
    ]
    await spine_db.insert_market_sentiment_logs(batch)
    compound = await spine_db.fetch_rolling_compound_sentiment_index("BTC", window_seconds=3600)
    assert isinstance(compound, float)
    all_indices = await spine_db.fetch_all_rolling_compound_sentiment_indices(["BTC", "ETH"])
    assert isinstance(all_indices, dict)


@pytest.mark.asyncio
async def test_macro_market_log(spine_db):
    mid = await spine_db.insert_macro_market_log(104.2, 4500.0, "risk_on", 0.15)
    assert mid > 0
    latest = await spine_db.fetch_latest_macro_market_log()
    assert latest is not None


@pytest.mark.asyncio
async def test_waitlist_and_subscriptions(spine_db):
    wl = await spine_db.insert_waitlist_signup("wait@blackdark.local", name="Test")
    assert wl.get("success") is True
    sub_id = await spine_db.insert_subscription(
        email="sub@blackdark.local",
        tier="pro",
        stripe_sub_id="sub_test",
    )
    assert sub_id > 0
    trial = await spine_db.insert_pro_trial("trial@blackdark.local", days=7)
    assert trial.get("tier") == "pro"
    extended = await spine_db.extend_pro_trial("trial@blackdark.local", extra_days=3)
    assert "trial_ends_at" in extended
    assert await spine_db.db_count_waitlist() >= 1
    assert await spine_db.db_count_subscribers() >= 1


@pytest.mark.asyncio
async def test_oracle_predictions(spine_db):
    pred_id = await spine_db.insert_oracle_prediction(
        asset="BTC",
        price_at_prediction=50000.0,
        verdict="BUY",
        opportunity_score=80,
        confidence=72,
        features_json="{}",
    )
    assert pred_id > 0
    unresolved = await spine_db.fetch_unresolved_oracle_predictions(limit=10)
    assert any(r["id"] == pred_id for r in unresolved)
    await spine_db.update_oracle_prediction_horizons(pred_id, price_after_1h=50100.0, price_after_4h=50200.0)
    await spine_db.resolve_oracle_prediction(
        pred_id,
        price_after=50300.0,
        outcome="win",
        accuracy_score=0.85,
    )
    stats = await spine_db.fetch_oracle_audit_stats()
    assert isinstance(stats, dict)
    labeled = await spine_db.fetch_labeled_oracle_predictions(limit=5)
    assert isinstance(labeled, list)


@pytest.mark.asyncio
async def test_ml_model_runs(spine_db):
    run_id = await spine_db.insert_ml_model_run(
        model_name="oracle_direction",
        model_version="v1",
        samples_used=100,
        metrics_json='{"accuracy":0.7}',
        model_path="/tmp/model.joblib",
        status="completed",
    )
    assert run_id > 0
    latest = await spine_db.fetch_latest_ml_model_run("oracle_direction")
    assert latest is not None


@pytest.mark.asyncio
async def test_arbitrage_and_simulation_logs(spine_db):
    aid = await spine_db.insert_arbitrage_alert_log("spread", "BTC arb", "{}", delivered=True)
    assert aid > 0
    alerts = await spine_db.fetch_arbitrage_alert_log(limit=5)
    assert len(alerts) >= 1
    sim_id = await spine_db.insert_simulation_log("paper", "BTC", "{}", 12.5)
    assert sim_id > 0
    sims = await spine_db.fetch_simulation_logs(limit=5)
    assert len(sims) >= 1


@pytest.mark.asyncio
async def test_alert_subscriptions_and_delivery(spine_db):
    sub_id = await spine_db.insert_alert_subscription(
        email="alerts@blackdark.local",
        telegram_chat_id=None,
        whatsapp_phone=None,
        min_profit_pct=0.5,
        oracle_alerts=True,
        arbitrage_alerts=True,
    )
    assert sub_id > 0
    active = await spine_db.fetch_active_alert_subscriptions()
    assert isinstance(active, list)
    delivery_id = await spine_db.insert_alert_delivery_log("test", "{}", "{}")
    assert delivery_id > 0


@pytest.mark.asyncio
async def test_execution_state_and_logs(spine_db):
    state = await spine_db.fetch_execution_state()
    assert "panic_active" in state
    await spine_db.set_execution_state(panic_active=True, auto_execution_enabled=False)
    updated = await spine_db.fetch_execution_state()
    assert updated.get("panic_active") in (1, True)
    log_id = await spine_db.insert_execution_log("buy", "BTC", "{}", live=False)
    assert log_id > 0
    logs = await spine_db.fetch_execution_logs(limit=5)
    assert len(logs) >= 1


@pytest.mark.asyncio
async def test_risk_freeze_and_user_risk(spine_db):
    freeze = await spine_db.fetch_risk_freeze_state()
    assert isinstance(freeze, dict)
    await spine_db.set_risk_freeze_state(frozen=True, reason="test")
    uid = await spine_db.create_user(email="risk@blackdark.local", password_hash="hash")
    settings = await spine_db.fetch_user_risk_settings(uid)
    assert isinstance(settings, dict)
    await spine_db.upsert_user_risk_settings(uid, max_daily_loss_usd=100.0, max_slippage_bps=25.0)
    updated = await spine_db.fetch_user_risk_settings(uid)
    assert updated.get("max_daily_loss_usd") == 100.0


@pytest.mark.asyncio
async def test_platform_analytics_and_behavior(spine_db):
    analytics = await spine_db.fetch_platform_analytics()
    assert isinstance(analytics, dict)
    bumped = await spine_db.increment_platform_metric("page_views")
    assert isinstance(bumped, dict)
    assert await spine_db.fetch_user_count() >= 0
    eid = await spine_db.insert_behavior_event("page_view", user_email="behav@blackdark.local", asset="BTC")
    assert eid > 0
    stats = await spine_db.fetch_behavior_event_stats(days=7)
    assert stats["total_events"] >= 1


@pytest.mark.asyncio
async def test_journal_entries(spine_db):
    jid = await spine_db.insert_journal_entry(
        "journal@blackdark.local",
        "BTC",
        "buy",
        notes="entry",
        oracle_verdict="WAIT",
        entry_price=50000.0,
    )
    assert jid > 0
    entries = await spine_db.fetch_journal_entries("journal@blackdark.local", limit=5)
    assert len(entries) >= 1
    assert await spine_db.update_journal_entry(jid, "journal@blackdark.local", exit_price=51000.0, pnl_usd=100.0)
    assert await spine_db.delete_journal_entry(jid, "journal@blackdark.local")


@pytest.mark.asyncio
async def test_sentiment_delete_archival(spine_db):
    sid = await spine_db.insert_market_sentiment_log("SOL", "test", "text", 0.4, 0.05)
    assert await spine_db.delete_sentiment_logs_by_ids([sid]) == 1


@pytest.mark.asyncio
async def test_institutional_flows_batch(spine_db):
    ts = datetime.now(UTC).isoformat()
    rows = [
        (ts, "whale_alert", None, None, "BTC", None, None, None, None, 1_000_000.0, None, "{}"),
    ]
    await spine_db.insert_institutional_flows(rows)
    count = await spine_db.fetch_institutional_flow_count()
    assert count >= 1
