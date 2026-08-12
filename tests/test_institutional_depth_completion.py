"""End-to-end institutional depth: canonical bus, DB authority, fill proof, decision e2e."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_canonical_truth_bus_live_refresh():
    from canonical_truth_bus import bus_status, refresh_live_truth, reset_bus_for_tests

    reset_bus_for_tests()
    out = await refresh_live_truth(symbol="BTC/USDT")
    assert out["ok"] is True
    assert len(out["venues"]) >= 1
    st = bus_status()
    assert st["bypass_forbidden"] is True
    assert st["synthetic_forbidden_on_production"] is True


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
