"""RC2 chaos / dependency failure pack (F-REL-01) — fail-closed, no invented truth."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_postgres_unavailable_does_not_invent_ready(monkeypatch):
    """When DATABASE_URL points at a dead host, readiness must not claim healthy DB."""
    import postgres_backend as pb

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://blackdark:blackdark@127.0.0.1:1/blackdark_missing",
    )
    if hasattr(pb, "_pool"):
        monkeypatch.setattr(pb, "_pool", None, raising=False)
    if not hasattr(pb, "get_pool"):
        pytest.skip("postgres_backend.get_pool not present")
    with pytest.raises((OSError, ConnectionError, TimeoutError, RuntimeError, Exception)):
        await pb.get_pool()


def test_fee_matrix_unknown_venue_is_none():
    import fee_matrix

    fee_matrix._matrix.clear()
    assert fee_matrix.taker_fee("not-a-real-venue-xyz") is None
    assert fee_matrix.withdrawal_fee_usdt("not-a-real-venue-xyz", "BTC/USDT") is None


def test_redis_url_missing_viral_not_fabricated(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("VIRAL_MODE", "true")
    import production_guard as pg

    report = pg.evaluate_production_guard()
    assert isinstance(report, dict)
    blob = str(report).lower()
    assert ("redis" in blob) or ("soft" in blob) or ("required" in blob)


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
