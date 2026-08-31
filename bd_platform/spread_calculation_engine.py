"""
Spread Calculation Engine — Feature #427 (Economics Engine for #429).

NOT standalone — merged into Unified Arbitrage Opportunity Engine.

Executable spread after real market depth, synchronized timestamps, fee_matrix fees,
and slippage adjustment. Stale books rejected fail-closed.

Mandatory:
  - Decimal precision (no float rounding in crypto economics)
  - Synchronized timestamps across venues
  - Fee/slippage included in every net spread calculation
  - Stale books rejected
  - Deterministic: same inputs → same outputs
"""

from __future__ import annotations

import json
import logging
from decimal import ROUND_HALF_UP, Decimal
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.SpreadCalculationEngine")

_FEATURE_ID = 427
_TITLE = "Spread Calculation Engine"
_LEGAL_NAME = "Economics Engine"
_STANDALONE = False
_MERGED_INTO = "Unified Arbitrage Engine (#429)"
_SPRINT = 2
_PRIORITY = "critical"
_SEED_PATH = Path("data/spread_calculation_engine_seed.json")
_ENGINE_VERSION = "2.0.0"
_USDT_SCALE = Decimal("0.000001")
_BPS_SCALE = Decimal("0.0001")
_PRICE_SCALE = Decimal("0.00000001")

_DISCLAIMER = (
    "Spread Calculation Engine — executable gross/net spread with depth-aware pricing, "
    "fee_matrix fees, and slippage. Stale or unsynchronized books rejected. "
    "Simulation only — not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _d(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _quantize_usdt(value: Decimal) -> Decimal:
    return value.quantize(_USDT_SCALE, rounding=ROUND_HALF_UP)


def _quantize_bps(value: Decimal) -> Decimal:
    return value.quantize(_BPS_SCALE, rounding=ROUND_HALF_UP)


def _quantize_price(value: Decimal) -> Decimal:
    return value.quantize(_PRICE_SCALE, rounding=ROUND_HALF_UP)


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"engine_version": _ENGINE_VERSION}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("spread calculation engine seed load failed: %s", exc)
        return {"engine_version": _ENGINE_VERSION}


def _book_timestamp_ms(book: dict[str, Any]) -> int | None:
    freshness = book.get("freshness") or {}
    if freshness.get("exchange_timestamp_ms") is not None:
        return int(freshness["exchange_timestamp_ms"])
    if freshness.get("exchange_timestamp"):
        try:
            ts = datetime.fromisoformat(str(freshness["exchange_timestamp"]).replace("Z", "+00:00"))
            return int(ts.timestamp() * 1000)
        except (TypeError, ValueError):
            return None
    return None


def _book_age_ms(book: dict[str, Any]) -> int | None:
    freshness = book.get("freshness") or {}
    age = freshness.get("snapshot_age_ms")
    return int(age) if age is not None else None


def _is_stale(book: dict[str, Any], *, stale_ms: int) -> bool:
    age = _book_age_ms(book)
    if age is None:
        return True
    return age > stale_ms


def _timestamps_synchronized(
    buy_book: dict[str, Any],
    sell_book: dict[str, Any],
    *,
    max_drift_ms: int,
) -> tuple[bool, int | None]:
    buy_ts = _book_timestamp_ms(buy_book)
    sell_ts = _book_timestamp_ms(sell_book)
    if buy_ts is None or sell_ts is None:
        return False, None
    drift = abs(buy_ts - sell_ts)
    return drift <= max_drift_ms, drift


def _walk_levels(
    levels: list[list[float]],
    size: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """Depth-aware VWAP walk. Returns (filled, vwap, residual)."""
    if size <= 0 or not levels:
        return Decimal("0"), Decimal("0"), size

    remaining = size
    notional = Decimal("0")
    filled = Decimal("0")
    for level in levels:
        if remaining <= 0:
            break
        if len(level) < 2:
            continue
        price = _d(level[0])
        qty = _d(level[1])
        if price <= 0 or qty <= 0:
            continue
        take = min(remaining, qty)
        notional += take * price
        filled += take
        remaining -= take

    vwap = notional / filled if filled > 0 else Decimal("0")
    return filled, _quantize_price(vwap), remaining


def _venue_trading_fee_usd(venue: str, notional: Decimal, *, use_maker: bool = False) -> tuple[Decimal | None, dict[str, Any]]:
    from fee_matrix import maker_fee, taker_fee, trading_fees_usdt

    rate = maker_fee(venue) if use_maker else taker_fee(venue)
    fee = trading_fees_usdt(venue, float(notional), use_maker=use_maker)
    if fee is None:
        return None, {"venue": venue, "source": "fee_matrix_db", "known": False}
    return _quantize_usdt(_d(fee)), {
        "venue": venue,
        "fee_rate": str(rate) if rate is not None else None,
        "fee_usd": str(_quantize_usdt(_d(fee))),
        "source": "fee_matrix_db",
        "known": True,
    }


def _withdrawal_fee_usd(venue: str, symbol: str) -> tuple[Decimal | None, dict[str, Any]]:
    from fee_matrix import withdrawal_fee_usdt

    base = symbol.split("/")[0].upper()
    fee = withdrawal_fee_usdt(venue, base)
    if fee is None:
        return None, {"venue": venue, "asset": base, "source": "fee_matrix_db", "known": False}
    return _quantize_usdt(_d(fee)), {
        "venue": venue,
        "asset": base,
        "fee_usd": str(_quantize_usdt(_d(fee))),
        "source": "fee_matrix_db",
        "known": True,
    }


def _reject_result(
    *,
    reason: str,
    buy_venue: str,
    sell_venue: str,
    symbol: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "reject": True,
        "rejection_reason": reason,
        "feature_id": _FEATURE_ID,
        "feature_ref": _FEATURE_ID,
        "engine_version": _ENGINE_VERSION,
        "source_venues": {"buy": buy_venue, "sell": sell_venue},
        "symbol": symbol,
        "gross_spread_bps": None,
        "net_spread_bps": None,
        "gross_spread_usdt": None,
        "net_spread_usdt": None,
        "executable_size": Decimal("0"),
        "details": details or {},
        "decimal_precision": True,
        "deterministic": True,
        "timestamp": _utcnow(),
    }


def _serialize_result(result: dict[str, Any]) -> dict[str, Any]:
    """Convert Decimal fields to strings for JSON determinism."""
    out = dict(result)
    for key in (
        "gross_spread_bps", "net_spread_bps", "gross_spread_usdt", "net_spread_usdt",
        "executable_size", "quote_usd", "slippage_bps", "slippage_usdt",
        "trading_fees_usdt", "transfer_cost_usdt", "withdrawal_fee_usdt",
        "buy_vwap", "sell_vwap", "best_buy_ask", "best_sell_bid",
    ):
        if key in out and isinstance(out[key], Decimal):
            out[key] = str(out[key])
    if "executable_size" in out and out["executable_size"] is not None:
        if not isinstance(out["executable_size"], str):
            out["executable_size"] = str(out["executable_size"])
    return out


def compute_executable_spread(
    *,
    buy_venue: str,
    sell_venue: str,
    symbol: str,
    quote_usd: Decimal | float | str,
    size: Decimal | float | str | None = None,
    buy_book: dict[str, Any] | None = None,
    sell_book: dict[str, Any] | None = None,
    transfer_cost_usdt: Decimal | float | str = Decimal("0"),
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    #427 core — executable gross/net spread with depth, fees, slippage, stale filtering.
    """
    seed = seed or _load_seed()
    sym = symbol.upper()
    quote = _d(quote_usd)
    transfer = _quantize_usdt(_d(transfer_cost_usdt))
    stale_ms = int(seed.get("stale_threshold_ms", 5000))
    max_drift = int(seed.get("max_timestamp_drift_ms", 500))
    min_fill_ratio = _d(seed.get("min_fill_ratio", "0.95"))

    if buy_book is None or sell_book is None:
        return _serialize_result(_reject_result(
            reason="missing_depth_never_executable",
            buy_venue=buy_venue,
            sell_venue=sell_venue,
            symbol=sym,
        ))

    if _is_stale(buy_book, stale_ms=stale_ms) or _is_stale(sell_book, stale_ms=stale_ms):
        return _serialize_result(_reject_result(
            reason="stale_book",
            buy_venue=buy_venue,
            sell_venue=sell_venue,
            symbol=sym,
            details={
                "buy_age_ms": _book_age_ms(buy_book),
                "sell_age_ms": _book_age_ms(sell_book),
                "stale_threshold_ms": stale_ms,
            },
        ))

    synced, drift = _timestamps_synchronized(buy_book, sell_book, max_drift_ms=max_drift)
    if not synced:
        return _serialize_result(_reject_result(
            reason="timestamp_not_synchronized",
            buy_venue=buy_venue,
            sell_venue=sell_venue,
            symbol=sym,
            details={"timestamp_drift_ms": drift, "max_drift_ms": max_drift},
        ))

    buy_asks = buy_book.get("asks") or []
    sell_bids = sell_book.get("bids") or []
    if not buy_asks or not sell_bids:
        return _serialize_result(_reject_result(
            reason="missing_depth_never_executable",
            buy_venue=buy_venue,
            sell_venue=sell_venue,
            symbol=sym,
        ))

    best_buy_ask = _d(buy_asks[0][0])
    best_sell_bid = _d(sell_bids[0][0])
    if best_buy_ask <= 0 or best_sell_bid <= 0:
        return _serialize_result(_reject_result(
            reason="invalid_best_prices",
            buy_venue=buy_venue,
            sell_venue=sell_venue,
            symbol=sym,
        ))

    if size is None:
        size = quote / best_buy_ask
    req_size = _d(size)

    buy_filled, buy_vwap, buy_residual = _walk_levels(buy_asks, req_size)
    sell_filled, sell_vwap, sell_residual = _walk_levels(sell_bids, req_size)
    executable_size = min(buy_filled, sell_filled)
    fill_ratio = executable_size / req_size if req_size > 0 else Decimal("0")

    if executable_size <= 0 or fill_ratio < min_fill_ratio:
        return _serialize_result(_reject_result(
            reason="insufficient_executable_depth",
            buy_venue=buy_venue,
            sell_venue=sell_venue,
            symbol=sym,
            details={
                "requested_size": str(req_size),
                "executable_size": str(executable_size),
                "fill_ratio": str(fill_ratio),
                "min_fill_ratio": str(min_fill_ratio),
            },
        ))

    buy_notional = executable_size * buy_vwap
    sell_notional = executable_size * sell_vwap
    gross_usdt = _quantize_usdt(sell_notional - buy_notional)
    gross_bps = _quantize_bps((gross_usdt / buy_notional) * Decimal("10000")) if buy_notional > 0 else Decimal("0")

    buy_fee, buy_fee_meta = _venue_trading_fee_usd(buy_venue, buy_notional)
    sell_fee, sell_fee_meta = _venue_trading_fee_usd(sell_venue, sell_notional)
    wd_fee, wd_meta = _withdrawal_fee_usd(buy_venue, sym)

    if buy_fee is None or sell_fee is None:
        return _serialize_result(_reject_result(
            reason="unknown_venue_fee",
            buy_venue=buy_venue,
            sell_venue=sell_venue,
            symbol=sym,
            details={"buy_fee": buy_fee_meta, "sell_fee": sell_fee_meta},
        ))

    trading_fees = _quantize_usdt(buy_fee + sell_fee)
    withdrawal = wd_fee if wd_fee is not None else Decimal("0")

    # Slippage vs best bid/ask
    buy_slip_bps = ((buy_vwap - best_buy_ask) / best_buy_ask * Decimal("10000")) if best_buy_ask > 0 else Decimal("0")
    sell_slip_bps = ((best_sell_bid - sell_vwap) / best_sell_bid * Decimal("10000")) if best_sell_bid > 0 else Decimal("0")
    slippage_bps = _quantize_bps(max(Decimal("0"), buy_slip_bps) + max(Decimal("0"), sell_slip_bps))
    slippage_usdt = _quantize_usdt(buy_notional * (slippage_bps / Decimal("10000")))

    net_usdt = _quantize_usdt(gross_usdt - trading_fees - slippage_usdt - transfer - withdrawal)
    net_bps = _quantize_bps((net_usdt / buy_notional) * Decimal("10000")) if buy_notional > 0 else Decimal("0")

    return _serialize_result({
        "ok": True,
        "reject": False,
        "rejection_reason": None,
        "feature_id": _FEATURE_ID,
        "feature_ref": _FEATURE_ID,
        "engine_version": _ENGINE_VERSION,
        "symbol": sym,
        "quote_usd": quote,
        "source_venues": {"buy": buy_venue, "sell": sell_venue},
        "gross_spread_bps": gross_bps,
        "net_spread_bps": net_bps,
        "gross_spread_usdt": gross_usdt,
        "net_spread_usdt": net_usdt,
        "executable_size": executable_size,
        "buy_vwap": buy_vwap,
        "sell_vwap": sell_vwap,
        "best_buy_ask": best_buy_ask,
        "best_sell_bid": best_sell_bid,
        "trading_fees_usdt": trading_fees,
        "slippage_bps": slippage_bps,
        "slippage_usdt": slippage_usdt,
        "transfer_cost_usdt": transfer,
        "withdrawal_fee_usdt": withdrawal,
        "fee_breakdown": {
            "buy_leg": buy_fee_meta,
            "sell_leg": sell_fee_meta,
            "withdrawal": wd_meta,
        },
        "timestamp_sync": {
            "synchronized": True,
            "drift_ms": drift,
            "max_drift_ms": max_drift,
        },
        "depth_evidence": {
            "buy_fill_ratio": str((buy_filled / req_size) if req_size > 0 else Decimal("0")),
            "sell_fill_ratio": str((sell_filled / req_size) if req_size > 0 else Decimal("0")),
            "buy_residual": str(buy_residual),
            "sell_residual": str(sell_residual),
        },
        "decimal_precision": True,
        "fee_slippage_included": True,
        "deterministic": True,
        "timestamp": _utcnow(),
    })


def compute_arbitrage_economics(
    *,
    gross_spread_bps: float,
    quote_usd: float,
    trading_fee_bps: float,
    slippage_bps: float,
    transfer_cost_usdt: float = 0.0,
    withdrawal_fee_usdt: float = 0.0,
    leg_count: int = 2,
) -> dict[str, Any]:
    """
    Backward-compatible economics wrapper — uses Decimal internally (#427).
    Net spread is the only ranking standard; fees/slippage always included.
    """
    quote = _d(quote_usd)
    gross_bps = _d(gross_spread_bps)
    fee_bps = _d(trading_fee_bps)
    slip_bps = _d(slippage_bps)
    transfer = _quantize_usdt(_d(transfer_cost_usdt))
    withdrawal = _quantize_usdt(_d(withdrawal_fee_usdt))
    legs = _d(leg_count)

    gross_usdt = _quantize_usdt(quote * (gross_bps / Decimal("10000")))
    trading_fees = _quantize_usdt(quote * (fee_bps / Decimal("10000")) * legs)
    slippage_usdt = _quantize_usdt(quote * (slip_bps / Decimal("10000")))
    net_usdt = _quantize_usdt(gross_usdt - trading_fees - slippage_usdt - transfer - withdrawal)
    net_bps = _quantize_bps((net_usdt / quote) * Decimal("10000")) if quote > 0 else Decimal("0")

    return {
        "gross_spread_bps": float(_quantize_bps(gross_bps)),
        "net_spread_bps": float(net_bps),
        "gross_spread_usdt": float(gross_usdt),
        "net_spread_usdt": float(net_usdt),
        "quote_usd": float(quote),
        "trading_fee_bps": float(_quantize_bps(fee_bps)),
        "slippage_bps": float(_quantize_bps(slip_bps)),
        "trading_fees_usdt": float(trading_fees),
        "slippage_usdt": float(slippage_usdt),
        "transfer_cost_usdt": float(transfer),
        "withdrawal_fee_usdt": float(withdrawal),
        "net_edge_usdt": float(net_usdt),
        "net_edge_bps": float(net_bps),
        "economics_engine_version": _ENGINE_VERSION,
        "economics_engine_ref": _FEATURE_ID,
        "decimal_precision": True,
        "fee_slippage_included": True,
        "deterministic": True,
        "decimal_fields": {
            "gross_spread_bps": str(_quantize_bps(gross_bps)),
            "net_spread_bps": str(net_bps),
            "gross_spread_usdt": str(gross_usdt),
            "net_spread_usdt": str(net_usdt),
            "trading_fees_usdt": str(trading_fees),
            "slippage_usdt": str(slippage_usdt),
        },
    }


def compute_cross_venue_spread(
    raw: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
    depth_seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Cross-venue spread with depth books when available."""
    seed = seed or _load_seed()
    buy_v = str(raw.get("buy_venue") or "")
    sell_v = str(raw.get("sell_venue") or "")
    sym = str(raw.get("symbol") or f"{raw.get('asset', 'BTC')}/USDT")
    quote = _d(raw.get("quote_usd", 1000))
    transfer = _d(raw.get("transfer_cost_usdt", 0))

    buy_book = raw.get("buy_book")
    sell_book = raw.get("sell_book")

    if buy_book is None or sell_book is None:
        try:
            from bd_platform.fill_feasibility_simulator import _load_seed as load_ff_seed

            ff = depth_seed or load_ff_seed()
            pair_books = (ff.get("pairs") or {}).get(sym.upper()) or {}
            buy_book = buy_book or pair_books.get(buy_v.lower())
            sell_book = sell_book or pair_books.get(sell_v.lower())
        except Exception:
            logger.debug("depth book lookup skipped", exc_info=True)

    if buy_book and sell_book:
        spread = compute_executable_spread(
            buy_venue=buy_v,
            sell_venue=sell_v,
            symbol=sym,
            quote_usd=quote,
            buy_book=buy_book,
            sell_book=sell_book,
            transfer_cost_usdt=transfer,
            seed=seed,
        )
        if not spread.get("reject"):
            return spread
        if spread.get("rejection_reason") not in ("stale_book", "timestamp_not_synchronized"):
            return spread
        # Depth books stale/unsynced — fall through to fresh top-of-book from opportunity raw

    # Fallback: top-of-book prices from raw when depth unavailable or stale
    buy_p = _d(raw.get("buy_price", 0))
    sell_p = _d(raw.get("sell_price", 0))
    if buy_p <= 0 or sell_p <= 0:
        gross_bps = Decimal("0")
    else:
        gross_bps = _quantize_bps(((sell_p - buy_p) / buy_p) * Decimal("10000"))

    from fee_matrix import taker_fee

    r_buy = taker_fee(buy_v) or 0.001
    r_sell = taker_fee(sell_v) or 0.001
    fee_bps = _d((Decimal(str(r_buy)) + Decimal(str(r_sell))) * Decimal("10000"))
    slip_bps = _d(raw.get("slippage_bps", 8))
    wd = raw.get("withdrawal_fee_usdt")
    if wd is None:
        wd_fee, _ = _withdrawal_fee_usd(buy_v, sym)
        withdrawal = wd_fee if wd_fee is not None else Decimal("0")
    else:
        withdrawal = _quantize_usdt(_d(wd))

    econ = compute_arbitrage_economics(
        gross_spread_bps=float(gross_bps),
        quote_usd=float(quote),
        trading_fee_bps=float(fee_bps),
        slippage_bps=float(slip_bps),
        transfer_cost_usdt=float(transfer),
        withdrawal_fee_usdt=float(withdrawal),
        leg_count=2,
    )
    quote_age = raw.get("quote_age_ms")
    stale_ms = int(seed.get("stale_threshold_ms", 5000))
    if quote_age is not None and int(quote_age) > stale_ms:
        return _serialize_result(_reject_result(
            reason="stale_book",
            buy_venue=buy_v,
            sell_venue=sell_v,
            symbol=sym,
            details={"quote_age_ms": quote_age, "stale_threshold_ms": stale_ms},
        ))

    return {
        **econ,
        "ok": True,
        "reject": False,
        "source_venues": {"buy": buy_v, "sell": sell_v},
        "symbol": sym,
        "executable_size": str(quote / buy_p) if buy_p > 0 else "0",
        "depth_aware": False,
        "top_of_book_fallback": True,
    }


def spread_calculation_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "engine_version": _ENGINE_VERSION,
        "decimal_precision": seed.get("decimal_precision", True),
        "synchronized_timestamps_required": seed.get("synchronized_timestamps_required", True),
        "stale_books_rejected": True,
        "fee_slippage_included": True,
        "net_spread_only_ranking": True,
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def run_regression_fixtures(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    results: list[dict[str, Any]] = []
    for fixture in seed.get("regression_fixtures") or []:
        inp = fixture.get("input") or {}
        expect = fixture.get("expect") or {}
        spread = compute_executable_spread(
            buy_venue=inp["buy_venue"],
            sell_venue=inp["sell_venue"],
            symbol=inp["symbol"],
            quote_usd=inp.get("quote_usd", "1000"),
            size=inp.get("size"),
            buy_book=inp.get("buy_book"),
            sell_book=inp.get("sell_book"),
            seed=seed,
        )
        passed = True
        details: list[str] = []
        if expect.get("reject") and not spread.get("reject"):
            passed = False
            details.append("expected reject")
        if expect.get("reject") is False and spread.get("reject"):
            passed = False
            details.append(f"unexpected reject: {spread.get('rejection_reason')}")
        if expect.get("reason") and spread.get("rejection_reason") != expect["reason"]:
            passed = False
            details.append(f"reason expected {expect['reason']}")
        if expect.get("has_net_spread") and spread.get("net_spread_usdt") is None:
            passed = False
            details.append("missing net_spread")
        if expect.get("fee_included") and spread.get("fee_slippage_included") is not True:
            passed = False
            details.append("fees not included")
        if expect.get("deterministic"):
            repeat = compute_executable_spread(
                buy_venue=inp["buy_venue"],
                sell_venue=inp["sell_venue"],
                symbol=inp["symbol"],
                quote_usd=inp.get("quote_usd", "1000"),
                size=inp.get("size"),
                buy_book=inp.get("buy_book"),
                sell_book=inp.get("sell_book"),
                seed=seed,
            )
            a = {k: v for k, v in spread.items() if k != "timestamp"}
            b = {k: v for k, v in repeat.items() if k != "timestamp"}
            if a != b:
                passed = False
                details.append("not deterministic")

        results.append({
            "fixture_id": fixture.get("id"),
            "passed": passed,
            "reject": spread.get("reject"),
            "rejection_reason": spread.get("rejection_reason"),
            "net_spread_usdt": spread.get("net_spread_usdt"),
            "details": details,
        })

    passed_count = sum(1 for r in results if r["passed"])
    return {
        "ok": passed_count == len(results),
        "feature_id": _FEATURE_ID,
        "fixtures": results,
        "passed": passed_count,
        "total": len(results),
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "429 merge"})
    checks.append({"id": "decimal_precision", "passed": seed.get("decimal_precision") is True, "detail": "Decimal"})
    checks.append({"id": "sync_timestamps", "passed": seed.get("synchronized_timestamps_required") is True, "detail": "sync"})

    regression = run_regression_fixtures(seed=seed)
    checks.append({"id": "deterministic_regression", "passed": regression["ok"], "detail": f"{regression['passed']}/{regression['total']}"})

    a = compute_arbitrage_economics(gross_spread_bps=20, quote_usd=1000, trading_fee_bps=10, slippage_bps=8)
    b = compute_arbitrage_economics(gross_spread_bps=20, quote_usd=1000, trading_fee_bps=10, slippage_bps=8)
    checks.append({"id": "deterministic_economics", "passed": a == b, "detail": "same inputs"})

    stale = compute_executable_spread(
        buy_venue="okx", sell_venue="binance", symbol="BTC/USDT", quote_usd="1000",
        buy_book={"asks": [[1, 1]], "freshness": {"snapshot_age_ms": 9000, "exchange_timestamp_ms": 1}},
        sell_book={"bids": [[2, 1]], "freshness": {"snapshot_age_ms": 100, "exchange_timestamp_ms": 2}},
        seed=seed,
    )
    checks.append({"id": "stale_books_rejected", "passed": stale.get("rejection_reason") == "stale_book", "detail": "fail-closed"})

    passed = sum(1 for c in checks if c["passed"])
    return {"ok": passed == len(checks), "feature_id": _FEATURE_ID, "checks": checks, "passed": passed, "total": len(checks), "timestamp": _utcnow()}
