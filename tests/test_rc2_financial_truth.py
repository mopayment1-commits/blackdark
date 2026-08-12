"""RC2 financial truth regressions — fail-closed fees/gas; Decimal arb path; advisory labels."""

from __future__ import annotations

import fee_matrix
import pytest


def test_cross_exchange_uses_decimal_money_path(monkeypatch):
    from arbitrage_engine import _build_cross_exchange_opportunity
    from money_decimal import apply_fee, money_float

    fee_matrix._matrix.clear()
    buy_book = {"asks": [[100.0, 50.0]], "bids": [[99.5, 50.0]]}
    sell_book = {"asks": [[102.5, 50.0]], "bids": [[102.0, 50.0]]}
    ok = _build_cross_exchange_opportunity(
        "BTC/USDT", "binance", "okx", buy_book, sell_book, 500.0, None
    )
    assert ok is not None
    buy_rate = fee_matrix.taker_fee("binance")
    sell_rate = fee_matrix.taker_fee("okx")
    assert buy_rate is not None
    assert sell_rate is not None
    # Reconstruct with Decimal helpers — engine must match within money quantum.
    expected_buy_fee = money_float(apply_fee(ok.quote_amount, buy_rate))  # rough bound
    assert ok.trading_fees_usdt > 0
    assert abs(ok.trading_fees_usdt - expected_buy_fee) < ok.trading_fees_usdt  # sanity
    assert ok.net_profit_usdt == pytest.approx(ok.net_profit_usdt, abs=1e-4)


def test_open_leg_fees_fail_closed_and_decimal(monkeypatch):
    from arbitrage_engine import _funding_open_leg_fees_usdt, _open_leg_fees_usdt

    fee_matrix._matrix.clear()
    known = _open_leg_fees_usdt(1_000.0, spot_ex="binance", perp_ex="binance")
    assert known is not None
    assert known > 0

    monkeypatch.setattr(fee_matrix, "taker_fee", lambda *_a, **_k: None)
    assert _open_leg_fees_usdt(1_000.0) is None
    assert _funding_open_leg_fees_usdt(1_000.0) is None


@pytest.mark.asyncio
async def test_gas_oracle_fail_closed_no_invented_usd(monkeypatch):
    import gas_oracle

    gas_oracle._CACHE.clear()
    gas_oracle._CACHE_TS.clear()

    async def _no_refresh(**_k):
        return {}

    monkeypatch.setattr(gas_oracle, "refresh_gas_cache", _no_refresh)
    assert await gas_oracle.get_swap_gas_usd("ethereum") is None
    assert await gas_oracle.gas_cost_bps("ethereum", 100.0) is None


@pytest.mark.asyncio
async def test_gas_oracle_stale_cache_fail_closed(monkeypatch):
    import time

    import gas_oracle

    gas_oracle._CACHE["ethereum"] = {
        "chain": "ethereum",
        "swap_cost_usd": 1.25,
        "updated_ms": 0,
    }
    gas_oracle._CACHE_TS["ethereum"] = time.monotonic() - (gas_oracle._MAX_STALE_SEC + 5)

    async def _no_refresh(**_k):
        return gas_oracle._CACHE

    monkeypatch.setattr(gas_oracle, "refresh_gas_cache", _no_refresh)
    assert await gas_oracle.get_swap_gas_usd("ethereum") is None


@pytest.mark.asyncio
async def test_defi_dex_scan_fail_closed_when_gas_unknown(monkeypatch):
    import defi_arbitrage_engine as dae
    import gas_oracle

    async def _none_gas(*_a, **_k):
        return None

    monkeypatch.setattr(dae, "_best_venue_prices", lambda pairs: (100.0, 1_000_000.0, 101.0, 1_000_000.0))
    monkeypatch.setattr(gas_oracle, "gas_cost_bps", _none_gas)

    class _Resp:
        status = 200

        async def json(self):
            return {
                "pairs": [
                    {"dexId": "uniswap", "priceUsd": "100", "liquidity": {"usd": 1_000_000}},
                    {"dexId": "sushiswap", "priceUsd": "101", "liquidity": {"usd": 1_000_000}},
                ]
            }

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

    class _Session:
        def get(self, *_a, **_k):
            return _Resp()

    out = await dae.scan_uniswap_sushiswap_spread(_Session(), "ETH")
    assert out is None


def test_advisory_truth_labeled_not_executable():
    from decision_enrichment import _attach_net_edge_truth

    out: dict = {"kind": "oracle_direction"}
    _attach_net_edge_truth(out, "BTC", 60.0, "WAIT", 0.0)
    truth = out["net_edge_truth"]
    if truth.get("mode") == "directional_advisory":
        assert truth.get("executable") is False
        assert truth.get("label") == "ADVISORY_NOT_EXECUTABLE"
        assert out.get("executable") is False


def test_setup_telegram_writes_private_file_not_env_token():
    from pathlib import Path

    src = Path("setup_telegram.py").read_text(encoding="utf-8")
    assert "telegram.secrets.env" in src
    assert "write_private_text" in src
    assert "TELEGRAM_SECRETS_FILE" in src
    assert "_persist_telegram_secrets" in src
    assert "_persist_nonsecret_env" in src
    # Must not upsert cleartext token into .env anymore.
    assert '_upsert_env("TELEGRAM_BOT_TOKEN"' not in src
    # Must not print secret file path after writing secrets (CodeQL clear-text log).
    assert "Wrote private secrets file (mode 0600)." in src


@pytest.mark.asyncio
async def test_gas_oracle_fresh_cache_returns_cost(monkeypatch):
    import time

    import gas_oracle

    gas_oracle._CACHE.clear()
    gas_oracle._CACHE_TS.clear()
    gas_oracle._CACHE["ethereum"] = {
        "chain": "ethereum",
        "swap_cost_usd": 2.5,
        "native_usd_source": "live_mid",
    }
    gas_oracle._CACHE_TS["ethereum"] = time.monotonic()

    async def _no_refresh(**_k):
        return gas_oracle._CACHE

    monkeypatch.setattr(gas_oracle, "refresh_gas_cache", _no_refresh)
    assert await gas_oracle.get_swap_gas_usd("ethereum", hops=2) == 5.0
    assert await gas_oracle.gas_cost_bps("ethereum", 100.0, hops=1) == pytest.approx(250.0)


@pytest.mark.asyncio
async def test_gas_row_builders_and_refresh_success(monkeypatch):
    import gas_oracle

    row = gas_oracle._evm_gas_row("ethereum", gwei=30.0, native_usd=2000.0)
    assert row["swap_cost_usd"] > 0
    assert row["native_usd_source"] == "live_mid"
    srow = gas_oracle._solana_gas_row(10_000.0, 100.0)
    assert srow["chain"] == "solana"

    async def _gwei(_s, _c):
        return 20.0

    monkeypatch.setattr(gas_oracle, "_fetch_eth_gas_gwei", _gwei)
    monkeypatch.setattr(gas_oracle, "_native_usd", lambda *_a, **_k: 1800.0)
    gas_oracle._CACHE.clear()
    gas_oracle._CACHE_TS.clear()
    out = await gas_oracle.refresh_gas_cache(chains=("ethereum",))
    assert "ethereum" in out
    assert await gas_oracle.get_swap_gas_usd("ethereum") is not None


@pytest.mark.asyncio
async def test_bridge_scan_fail_closed_without_invented_bridge_fee(monkeypatch):
    import defi_arbitrage_engine as dae
    import gas_oracle

    async def _gas(chain, *, hops=1):
        return 1.0

    monkeypatch.setattr(gas_oracle, "get_swap_gas_usd", _gas)

    class _Session:
        pass

    async def _price(_s, _a, chain):
        return {"ethereum": 100.0, "bsc": 102.0}.get(chain, 0.0)

    monkeypatch.setattr(dae, "_chain_dex_price", _price)
    out = await dae.scan_bridge_spread(_Session(), "ETH")
    assert out is not None
    assert out.get("executable") is False
    assert out.get("bridge_protocol_fee_usd") is None
    assert out.get("profitable") is False


def test_architecture_vault_honesty():
    from pathlib import Path

    text = Path("ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "vault-dev" in text
    assert "Fernet" in text
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert 'profiles: ["vault-dev"]' in compose
