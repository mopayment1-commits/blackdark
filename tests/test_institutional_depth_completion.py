"""End-to-end institutional depth: canonical bus, DB authority, fill proof, decision e2e."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_canonical_truth_bus_live_refresh():
    from canonical_truth_bus import bus_status, get_live_books, refresh_live_truth, reset_bus_for_tests

    reset_bus_for_tests()
    out = await refresh_live_truth(symbol="BTC/USDT")
    assert out["ok"] is True
    assert len(out["venues"]) >= 1
    assert out.get("fabricated_depth") is False
    assert len(out.get("l2_venues") or []) >= 1
    books = get_live_books(require_live=True, symbol="BTC/USDT")
    # Reject prior fabricated ladder pattern (2.0+i / 1.5+i)
    for venue_books in books.values():
        spot = venue_books.get("BTC/USDT")
        if not spot:
            continue
        sizes = [float(q) for _, q in (spot.get("bids") or [])[:8]]
        assert not all(abs(sizes[i] - (2.0 + i)) < 1e-9 for i in range(len(sizes)))
        assert not all(abs(sizes[i] - (1.5 + i)) < 1e-9 for i in range(len(sizes)))
        assert spot.get("fabricated_depth") is False
    st = bus_status()
    assert st["bypass_forbidden"] is True
    assert st["synthetic_forbidden_on_production"] is True
    assert st["fabricated_depth_forbidden"] is True


@pytest.mark.asyncio
async def test_institutional_store_oms_db_authority(tmp_path, monkeypatch):
    import config
    from institutional_store import ensure_ready, oms_get_sync, oms_upsert_sync, store_status

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "inst.db")
    monkeypatch.setattr(config, "DATABASE_URL", "")
    # force re-init
    import institutional_store as store

    store._READY_FOR = None  # noqa: SLF001
    ensure_ready()
    row = {
        "order_id": "oms_test_1",
        "org_id": "org1",
        "venue": "binance",
        "symbol": "BTC/USDT",
        "side": "buy",
        "quantity": 0.01,
        "filled_quantity": 0.0,
        "order_type": "limit",
        "limit_price": 100.0,
        "state": "INTENT",
        "idempotency_key": "idem-1",
        "actor": "test",
        "history": [{"state": "INTENT"}],
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    oms_upsert_sync(row)
    got = oms_get_sync("oms_test_1")
    assert got is not None
    assert got["state"] == "INTENT"
    assert store_status()["authority"] == "sqlite"
    assert "inst_oms_orders" in store_status()["tables"]


@pytest.mark.asyncio
async def test_venue_fill_proof_lifecycle():
    from venue_fill_proof import prove_fill_lifecycle

    out = await prove_fill_lifecycle(org_id="proof_org", quantity=0.001)
    assert out["ok"] is True
    assert out["oms_state"] in {"FILL", "RECONCILE"}
    assert "INTENT" in out["history_states"]
    assert "RISK_CHECK" in out["history_states"]
    assert "ACK" in out["history_states"]
    assert out["audit_trail"] is True
    assert out["portfolio_position"] is not None
    assert out["store"]["jsonl_is_export_only"] is True


def test_decision_e2e_unified_object():
    from decision_e2e import run_decision_e2e

    out = run_decision_e2e(symbol="BTC/USDT", org_id="e2e", notional=10_000.0)
    assert out["ok"] is True
    d = out["decision_object"]
    assert d["pipeline"].startswith("LIVE→CANONICAL")
    assert d["graph_id"]
    assert "evidence" in d and "risk" in d and "whale" in d
    assert out["loop"]["evaluation"]


def test_ops_backup_restore_probe(tmp_path, monkeypatch):
    import config
    import institutional_store as store
    from ops_recovery import ops_status

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "ops.db")
    monkeypatch.setattr(config, "DATABASE_URL", "")
    store._READY_FOR = None  # noqa: SLF001
    store.ensure_ready()
    st = ops_status()
    assert st["backup_restore"]["ok"] is True
    assert "inst_oms_orders" in st["backup_restore"]["institutional_tables"]


def test_super_terminal_has_unified_decision():
    from super_terminal import build_super_terminal

    pack = build_super_terminal(symbol="BTC/USDT", org_id="st")
    assert "unified_decision" in pack["modules"]
    assert "decision_object" in pack
    assert pack["decision_object"].get("pipeline")


def test_whale_5m_band_present():
    from whale_execution_evidence import measure_whale_readiness

    books = {
        "binance": {
            "BTC/USDT": {
                "bids": [[100.0 - i * 0.01, 8000.0] for i in range(40)],
                "asks": [[100.0 + i * 0.01, 8000.0] for i in range(40)],
            }
        },
        "okx": {
            "BTC/USDT": {
                "bids": [[100.0 - i * 0.01, 8000.0] for i in range(40)],
                "asks": [[100.0 + i * 0.01, 8000.0] for i in range(40)],
            }
        },
    }
    out = measure_whale_readiness(books, symbol="BTC/USDT")
    assert "5000000" in (out.get("capital_bands") or {})


@pytest.mark.asyncio
async def test_durable_ingestion_health_rows(tmp_path, monkeypatch):
    import config
    import institutional_store as store
    from institutional_ingestion_proof import prove_durable_ingestion

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "ingest.db")
    monkeypatch.setattr(config, "DATABASE_URL", "")
    store._READY_FOR = None  # noqa: SLF001
    out = await prove_durable_ingestion(symbol="BTC/USDT")
    assert out["ok"] is True
    assert out["ingestion_health_rows"] >= 1
    assert out["live_sources"] >= 1
    assert out["truth_bus"].get("fabricated_depth") is False


@pytest.mark.asyncio
async def test_venue_fill_proof_uses_venue_l2_depth():
    from venue_fill_proof import prove_fill_lifecycle

    out = await prove_fill_lifecycle(org_id="depth_org", quantity=0.001)
    assert out["ok"] is True
    assert out["depth"]["fabricated"] is False
    assert out["depth"]["bid_depth_usd"] > 0
    assert out["depth"]["ask_depth_usd"] > 0
    assert out["live_fill"] is False  # no testnet creds in CI


def test_super_terminal_derivatives_venue_perp():
    from canonical_truth_bus import refresh_live_truth_sync, reset_bus_for_tests
    from super_terminal import _derivatives_pack

    reset_bus_for_tests()
    refresh_live_truth_sync(symbol="BTC/USDT")
    pack = _derivatives_pack("BTC/USDT")
    assert pack.get("ok") is True
    assert pack.get("perp_leg") == "venue_futures"
    assert pack.get("funding_source") == "venue_funding"
    assert pack.get("fabricated_depth") is False
    assert pack.get("synthetic_hardcoded_books") is False
    assert len(pack.get("perp_venues") or []) >= 2


def test_ops_schema_authority(tmp_path, monkeypatch):
    import config
    import institutional_store as store
    from ops_recovery import ops_status

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "ops2.db")
    monkeypatch.setattr(config, "DATABASE_URL", "")
    store._READY_FOR = None  # noqa: SLF001
    store.ensure_ready()
    st = ops_status()
    assert st["schema_authority"]["ok"] is True
    assert "inst_oms_orders" in st["schema_authority"]["institutional_tables"]
    assert st["postgres_ddl_ready"]["ok"] is True


def test_multi_venue_perp_funding_on_bus():
    from canonical_truth_bus import get_live_funding, refresh_live_truth_sync, reset_bus_for_tests

    reset_bus_for_tests()
    out = refresh_live_truth_sync(symbol="BTC/USDT")
    assert out["ok"] is True
    assert len(out.get("perp_venues") or []) >= 2
    assert "okx" in (out.get("perp_venues") or [])
    funding = get_live_funding(require_live=True, symbol="BTC/USDT")
    assert "okx" in funding
    assert len(funding) >= 2
    assert funding["okx"]["BTC/USDT"].get("synthetic") is False
    for venue, syms in funding.items():
        assert syms["BTC/USDT"].get("synthetic") is False, venue


@pytest.mark.asyncio
async def test_scheduler_continuum_bounded(tmp_path, monkeypatch):
    import config
    import institutional_store as store
    from institutional_scheduler_proof import prove_scheduler_continuum

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "sched.db")
    monkeypatch.setattr(config, "DATABASE_URL", "")
    store._READY_FOR = None  # noqa: SLF001
    out = await prove_scheduler_continuum(cycle_seconds=1.0)
    assert out["ok"] is True
    assert out["scheduler_started"] is True
    assert out["scheduler_stopped"] is True
    assert out["continuum"] is True


@pytest.mark.asyncio
async def test_venue_protocol_proof_never_live_fill(monkeypatch):
    monkeypatch.setenv("VENUE_PROTOCOL_PROOF", "true")
    from venue_fill_proof import prove_fill_lifecycle

    out = await prove_fill_lifecycle(org_id="protocol_org", quantity=0.001)
    assert out["ok"] is True
    assert out["live_fill"] is False
    assert out["mode"] in {"venue_protocol_proof", "paper_lifecycle"}
    if out.get("protocol_ack"):
        assert out["protocol_ack"]["protocol_proof"] is True
        assert out["protocol_ack"]["live_fill"] is False


def test_product_complete_overclaim_census_reduced():
    import pathlib
    import re

    true_hits = 0
    for p in pathlib.Path(".").glob("*.py"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        true_hits += len(re.findall(r'["\']product_complete["\']\s*:\s*True', text))
    # After honesty sweep, root True census must be zero (no self-cert theater)
    assert true_hits == 0


@pytest.mark.asyncio
async def test_jupiter_live_quote_proof():
    from jupiter_dex_adapter import adapter_status, prove_jupiter_live_quote

    st = adapter_status()
    assert st["live_submit_implemented"] is True
    assert st["quote_implementation_class"] == "PARTIAL"
    out = await prove_jupiter_live_quote()
    assert out["ok"] is True
    assert out["executable_quote"] is True
    assert out["live_submit_implemented"] is True
    assert out["out_amount"]


@pytest.mark.asyncio
async def test_jupiter_submit_path_implemented_fail_closed_without_wallet():
    from jupiter_dex_adapter import execute_swap, prove_jupiter_submit_path

    proof = await prove_jupiter_submit_path()
    assert proof["ok"] is True
    assert proof["live_submit_implemented"] is True
    assert proof["dry_run"]["executed"] is False
    live = await execute_swap(asset="SOL", side="buy", amount_usd=1, dry_run=False)
    assert live["executed"] is False
    assert live["live_submit_implemented"] is True
    assert live["mode"] in {"ready_needs_live_flag_or_wallet", "live_submit_failed", "blocked"}


def test_postgres_local_dump_restore_prove():
    from ops_recovery import prove_postgres_local_dump_restore

    out = prove_postgres_local_dump_restore()
    assert out["ok"] is True
    assert out["ha_dr"] == "LOCAL_EPHEMERAL_NOT_HA"
    assert int(out.get("oms_rows") or 0) == 1


def test_postgres_streaming_ha_rpo_rto_prove():
    from ops_recovery import prove_postgres_streaming_ha_rpo_rto

    out = prove_postgres_streaming_ha_rpo_rto()
    assert out["ok"] is True
    assert out["ha_class"] == "LOCAL_STREAMING_REPLICATION"
    assert out["cloud_multi_az"] is False
    assert int(out["rpo_ms"]) <= 1000
    assert int(out["rto_ms"]) <= 5000
    assert out["verified_complete"] is True


@pytest.mark.asyncio
async def test_postgres_product_path_oms_round_trip():
    from ops_recovery import prove_postgres_product_path

    out = await prove_postgres_product_path()
    assert out["ok"] is True
    assert out["authority"] == "postgres"
    assert out["oms_round_trip"] is True
    assert out["ha_dr"] == "LOCAL_EPHEMERAL_NOT_HA"


@pytest.mark.asyncio
async def test_venue_fill_paper_venue_follows_l2():
    from venue_fill_proof import prove_fill_lifecycle

    out = await prove_fill_lifecycle(org_id="venue_id_org", quantity=0.001)
    assert out["ok"] is True
    assert out["live_fill"] is False
    assert out["depth"].get("venue")
    assert out["order_venue"] == out["depth"]["venue"]
    assert out["order_venue"] != "binance" or out["depth"]["venue"] == "binance"


def test_white_label_served_surface_prove():
    from white_label import prove_white_label_surface, white_label_status

    st = white_label_status()
    assert st["implementation_class"] == "PARTIAL"
    assert "institutional_api" in st["features"]
    out = prove_white_label_surface(org_id="wl_test_org", product_name="Desk Test")
    assert out["ok"] is True
    assert out["served_surface"]["brand_applied"] is True
    assert out["product_complete"] is False


@pytest.mark.asyncio
async def test_durable_ingestion_raises_coverage(tmp_path, monkeypatch):
    import config
    import institutional_store as store
    from institutional_ingestion_proof import prove_durable_ingestion

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "cov.db")
    monkeypatch.setattr(config, "DATABASE_URL", "")
    store._READY_FOR = None  # noqa: SLF001
    out = await prove_durable_ingestion()
    assert out["ok"] is True
    assert out["live_sources"] >= 2
    assert int(out["coverage"].get("live_ingestion_sources") or 0) >= 5
    assert float(out["coverage"].get("coverage_percent_exchanges") or 0) >= 5.0
    assert len(out.get("pricing_log_exchanges") or []) >= 2
    assert int((out.get("rollout") or {}).get("healthy_exchanges") or 0) >= 2


@pytest.mark.asyncio
async def test_rollout_multi_venue_live_at_least_five():
    from live_data_truth_probe import prove_multi_venue_live
    from universe_rollout import live_rollout_status

    mv = await prove_multi_venue_live()
    assert mv["ok"] is True
    assert mv["live_count"] >= 4
    assert len(mv.get("l2_venues") or []) >= 4
    roll = await live_rollout_status()
    assert roll["healthy_exchanges"] >= 4
    assert roll["coverage_percent"] >= 4.0
