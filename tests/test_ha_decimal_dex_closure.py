"""Guardrail tests for HA / Decimal / DEX / low-gap closures."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import pytest


def test_live_cross_arb_uses_decimal_money_engine():
    from arbitrage_engine import calculate_cross_exchange_arbitrage

    books = {
        "binance": {
            "BTC/USDT": {
                "asks": [[100.0, 10.0]],
                "bids": [[99.0, 10.0]],
            }
        },
        "okx": {
            "BTC/USDT": {
                "asks": [[101.0, 10.0]],
                "bids": [[100.8, 10.0]],
            }
        },
    }
    opps = calculate_cross_exchange_arbitrage(books, quote_amount=100.0)
    assert opps, "expected at least one cross opportunity"
    # Profit path must come from money.py Decimal engine (via profit_fee_algorithms)
    top = opps[0]
    assert isinstance(top.net_profit_usdt, float)
    from profit_fee_algorithms import net_cross_exchange_profit

    priced = net_cross_exchange_profit(
        books["binance"]["BTC/USDT"],
        books["okx"]["BTC/USDT"],
        buy_exchange="binance",
        sell_exchange="okx",
        symbol="BTC/USDT",
        notional=100.0,
    )
    assert priced is not None
    assert priced["precision_engine"] == "decimal_money_v1"
    assert abs(top.net_profit_usdt - priced["net_profit_usdt"]) < 1e-6


def test_redis_coord_rate_limit_local_fallback(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    import redis_coord as rc

    monkeypatch.setattr(rc, "_sync_client", None)
    rc._local_counters.clear()

    allowed, count = rc.rate_limit_check("u@x.com", limit=3, window_sec=60, namespace="t")
    assert allowed is True
    assert count == 0
    for _ in range(3):
        rc.rate_limit_hit("u@x.com", limit=3, window_sec=60, namespace="t")
    allowed2, count2 = rc.rate_limit_check("u@x.com", limit=3, window_sec=60, namespace="t")
    assert allowed2 is False
    assert count2 >= 3


def test_login_rate_limit_does_not_double_count(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    from security_auth import check_login_rate_limit, record_login_failure
    import redis_coord as rc
    import security_auth as sa

    monkeypatch.setattr(rc, "_sync_client", None)
    rc._local_counters.clear()
    monkeypatch.setattr(sa, "_login_attempts", defaultdict(list))
    monkeypatch.setattr(sa, "_AUTH_AUDIT_PATH", Path("/tmp/bd_auth_audit_test.jsonl"))

    # 9 failures should still allow check; 10th failure then blocks
    for i in range(9):
        check_login_rate_limit("rate@x.com")
        record_login_failure("rate@x.com", reason=f"bad_{i}")
    check_login_rate_limit("rate@x.com")  # still allowed at 9
    record_login_failure("rate@x.com", reason="bad_9")
    with pytest.raises(Exception) as exc:
        check_login_rate_limit("rate@x.com")
    assert getattr(exc.value, "status_code", None) == 429 or "Too many" in str(exc.value)


def test_audit_chain_append_with_lock(tmp_path, monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    import oracle_audit_chain as chain

    path = tmp_path / "chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)
    entry = chain.append_prediction_record({"asset": "BTC", "verdict": "WAIT"})
    assert entry.get("lock_mode") in {"redis", "process_local"}
    assert chain.verify_chain()["valid"] is True


def test_oauth_state_redis_fallback(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_ID", "gid")
    monkeypatch.setenv("OAUTH_GOOGLE_CLIENT_SECRET", "gsecret")
    monkeypatch.setenv("APP_BASE_URL", "http://localhost:8080")
    import redis_coord as rc
    from oauth_service import build_authorize_url, exchange_code

    monkeypatch.setattr(rc, "_sync_client", None)
    rc._local_kv.clear()

    payload = build_authorize_url("google")
    state = payload["state"]
    # Local + kv fallback both hold state
    assert rc.kv_get(state, namespace="oauth") == "google"

    # Simulate callback consuming Redis/local state without real token exchange
    stored = rc.kv_pop(state, namespace="oauth")
    assert stored == "google"


def test_shared_books_adapter():
    from live_book_hub import _adapt_redis_row

    book = _adapt_redis_row(
        "BTC/USDT",
        {"bid": 100.0, "ask": 100.1, "bid_qty": 2.0, "ask_qty": 3.0, "ts_ms": 1_700_000_000_000},
    )
    assert book is not None
    assert book["bids"][0][0] == 100.0
    assert book["asks"][0][0] == 100.1
    assert book["source"] == "redis_shared"


@pytest.mark.asyncio
async def test_shared_books_from_redis_mirror(monkeypatch):
    import live_book_hub as hub
    import redis_price_cache as rpc

    now_ms = __import__("time").time() * 1000.0
    fake = {
        "binance": {
            "BTC/USDT": {"bid": 100.0, "ask": 100.2, "bid_qty": 1, "ask_qty": 1, "ts_ms": now_ms},
        },
        "okx": {
            "BTC/USDT": {"bid": 100.1, "ask": 100.3, "bid_qty": 1, "ask_qty": 1, "ts_ms": now_ms},
        },
    }

    async def _fake_all():
        return fake

    monkeypatch.setattr(rpc, "get_all_books", _fake_all)
    hub._books.clear()
    result = await hub.get_shared_books_if_fresh(max_age_ms=5000)
    assert result is not None
    books, age = result
    assert "binance" in books and "okx" in books
    assert age >= 0


def test_jupiter_ready_and_executor_status():
    from jupiter_swap import jupiter_ready

    status = jupiter_ready()
    assert "wallet_configured" in status
    assert "signing_deps" in status
    assert "ready" in status


@pytest.mark.asyncio
async def test_dex_leg_dry_run_and_live_block_without_wallet(monkeypatch):
    monkeypatch.delenv("SOLANA_PRIVATE_KEY", raising=False)
    from bd_platform.cex_dex_executor import _dex_leg

    dry = await _dex_leg("SOL", "buy", 50.0, "jupiter", dry_run=True)
    assert dry["mode"] == "dry_run"
    assert dry["executed"] is False

    live = await _dex_leg("SOL", "buy", 50.0, "jupiter", dry_run=False)
    assert live["executed"] is False
    assert live["blocked_reason"] in {
        "missing_solana_private_key",
        "missing_solders_base58_deps",
        "missing_solana_private_key_and_jupiter",
        "jupiter_not_ready",
    } or str(live.get("blocked_reason", "")).startswith("missing_")


def test_whatsapp_twilio_helpers(monkeypatch):
    from alert_service import twilio_whatsapp_configured, whatsapp_alert_url

    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TWILIO_WHATSAPP_FROM", raising=False)
    assert twilio_whatsapp_configured() is False
    url = whatsapp_alert_url("+15551234567", "hello")
    assert url.startswith("https://wa.me/15551234567")

    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "ACxxx")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "token")
    monkeypatch.setenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
    assert twilio_whatsapp_configured() is True


@pytest.mark.asyncio
async def test_user_keys_seal_fernet_only(monkeypatch):
    monkeypatch.setenv("SECRETS_MASTER_KEY", "test-master-key-for-unit-tests-only")
    monkeypatch.setattr("postgres_backend.use_postgres", lambda: False, raising=False)
    from user_keys_service import _seal_for_storage, _unseal_from_storage

    sealed, engine = await _seal_for_storage("sk-test-secret")
    assert engine == "fernet"
    assert not sealed.startswith("pgc1:")
    assert await _unseal_from_storage(sealed) == "sk-test-secret"


def test_money_decimal_still_precise():
    from money import D

    assert D("0.1") + D("0.2") == Decimal("0.3")
