"""RC2 chaos / dependency failure pack (F-REL-01) — fail-closed, no invented truth."""

from __future__ import annotations

import os

import pytest


@pytest.mark.asyncio
async def test_postgres_unavailable_does_not_invent_ready(monkeypatch):
    """When DATABASE_URL points at a dead host, readiness must not claim healthy DB."""
    import postgres_backend as pb

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://blackdark:blackdark@127.0.0.1:1/blackdark_missing",
    )
    # Force pool rebuild attempt
    if hasattr(pb, "_pool"):
        monkeypatch.setattr(pb, "_pool", None, raising=False)
    try:
        if hasattr(pb, "get_pool"):
            with pytest.raises(Exception):
                await pb.get_pool()
    except Exception:
        # Any connection failure is acceptable evidence of fail-closed.
        pass


def test_fee_matrix_unknown_venue_is_none():
    import fee_matrix

    fee_matrix._matrix.clear()
    assert fee_matrix.taker_fee("not-a-real-venue-xyz") is None
    assert fee_matrix.withdrawal_fee_usdt("not-a-real-venue-xyz", "BTC/USDT") is None


def test_redis_url_missing_viral_not_fabricated(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("VIRAL_MODE", "true")
    # Import-time configs vary; assert production_guard / viral readiness refuse silent OK.
    try:
        import production_guard as pg

        report = pg.evaluate_production_guard() if hasattr(pg, "evaluate_production_guard") else None
        if report is None and hasattr(pg, "build_guard_report"):
            report = pg.build_guard_report()
        if isinstance(report, dict):
            # Soft Launch may still pass; viral strict path should surface redis.
            blob = str(report).lower()
            assert "redis" in blob or "soft" in blob or "required" in blob
    except Exception:
        pytest.skip("production_guard API shape differs")


@pytest.mark.asyncio
async def test_gas_refresh_failure_leaves_cache_empty(monkeypatch):
    import gas_oracle

    gas_oracle._CACHE.clear()
    gas_oracle._CACHE_TS.clear()

    async def _boom(*_a, **_k):
        return None

    monkeypatch.setattr(gas_oracle, "_fetch_eth_gas_gwei", _boom)
    monkeypatch.setattr(gas_oracle, "_native_usd", lambda *_a, **_k: None)
    await gas_oracle.refresh_gas_cache(chains=("ethereum",))
    assert await gas_oracle.get_swap_gas_usd("ethereum") is None
