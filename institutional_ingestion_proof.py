"""Institutional ingestion proof — durable health rows from live public venues.

One-shot (and optionally scheduler-backed) path that:
1. Pulls real venue L2 via live_data_truth_probe / truth bus / aggregator
2. Runs a prices-category ingest pass for free public handlers
3. Upserts `ingestion_source_health` so universe coverage sees durable rows
4. Never fabricates success without a live probe
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _write_live_mid_pricing_log(
    *,
    exchange: str,
    symbol: str,
    bid: float | None,
    ask: float | None,
) -> dict[str, Any] | None:
    """Persist real TOB mid into pricing_logs so rollout health sees durable live venues."""
    if bid is None or ask is None:
        return None
    try:
        bid_f = float(bid)
        ask_f = float(ask)
    except (TypeError, ValueError):
        return None
    if bid_f <= 0 or ask_f <= 0 or ask_f < bid_f:
        return None
    mid = (bid_f + ask_f) / 2.0
    from database import insert_pricing_log

    row_id = await insert_pricing_log(
        exchange=str(exchange).lower(),
        symbol=symbol,
        price=mid,
        volume=None,
        opportunity_score=None,
        market_type="spot",
    )
    return {
        "exchange": str(exchange).lower(),
        "symbol": symbol,
        "mid": mid,
        "pricing_log_id": row_id,
    }


async def _upsert_book_source(
    *,
    source_id: str,
    ok: bool,
    depth_source: str | None,
    levels: Any,
    reason: str | None,
    records: list[dict[str, Any]],
    exchange: str | None = None,
    symbol: str = "BTC/USDT",
    bid: float | None = None,
    ask: float | None = None,
    pricing_logs: list[dict[str, Any]] | None = None,
) -> None:
    from database import upsert_ingestion_health

    await upsert_ingestion_health(
        source_id,
        "prices",
        ok=ok,
        error=None if ok else str(reason or f"{source_id}_fail"),
    )
    pricing_row = None
    if ok and exchange:
        pricing_row = await _write_live_mid_pricing_log(
            exchange=exchange, symbol=symbol, bid=bid, ask=ask
        )
        if pricing_row is not None and pricing_logs is not None:
            pricing_logs.append(pricing_row)
    records.append(
        {
            "source_id": source_id,
            "ok": ok,
            "depth_source": depth_source,
            "levels": levels,
            "exchange": exchange,
            "pricing_log": bool(pricing_row),
        }
    )


async def _probe_aggregator_spot(venue: str, symbol: str = "BTC/USDT") -> dict[str, Any]:
    try:
        import aiohttp

        from aggregator import MARKET_FETCHERS
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": type(exc).__name__}
    fn = MARKET_FETCHERS.get(venue)
    if not fn:
        return {"ok": False, "reason": "fetcher_missing"}
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            _t, book = await fn(session, symbol, "spot")
        if not book or not book.bids or not book.asks:
            return {"ok": False, "reason": "empty_book"}
        bid = float(book.bids[0][0])
        ask = float(book.asks[0][0])
        return {
            "ok": True,
            "live": True,
            "venue": venue,
            "bid": bid,
            "ask": ask,
            "depth_source": "venue_l2",
            "fabricated_depth": False,
            "depth_levels": {"bids": len(book.bids), "asks": len(book.asks)},
            "source": f"{venue}_public_spot",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": f"{type(exc).__name__}:{exc}"[:160]}


async def prove_durable_ingestion(*, symbol: str = "BTC/USDT") -> dict[str, Any]:
    """Record live venue probes + free prices ingest into ingestion_source_health."""
    import aiohttp

    from canonical_truth_bus import refresh_live_truth
    from database import fetch_ingestion_health_summary, init_db
    from ingestion_fetchers import ingest_category
    from live_data_truth_probe import probe_kraken_depth, probe_okx_book

    await init_db()
    records: list[dict[str, Any]] = []
    pricing_logs: list[dict[str, Any]] = []

    okx = await probe_okx_book("BTC-USDT", depth=20)
    await _upsert_book_source(
        source_id="okx_public_books",
        ok=bool(okx.get("ok") and okx.get("live") and not okx.get("fabricated_depth")),
        depth_source=okx.get("depth_source"),
        levels=okx.get("depth_levels"),
        reason=okx.get("reason"),
        records=records,
        exchange="okx",
        symbol=str(okx.get("symbol") or symbol),
        bid=okx.get("bid"),
        ask=okx.get("ask"),
        pricing_logs=pricing_logs,
    )

    kr = await probe_kraken_depth("XBTUSDT", depth=25)
    await _upsert_book_source(
        source_id="kraken_public_depth",
        ok=bool(kr.get("ok") and kr.get("live") and not kr.get("fabricated_depth")),
        depth_source=kr.get("depth_source"),
        levels=kr.get("depth_levels"),
        reason=kr.get("reason"),
        records=records,
        exchange="kraken",
        symbol=str(kr.get("symbol") or symbol),
        bid=kr.get("bid"),
        ask=kr.get("ask"),
        pricing_logs=pricing_logs,
    )

    for venue in ("gateio", "bitget", "kucoin"):
        probe = await _probe_aggregator_spot(venue, symbol)
        await _upsert_book_source(
            source_id=f"{venue}_public_spot",
            ok=bool(probe.get("ok") and probe.get("live")),
            depth_source=probe.get("depth_source"),
            levels=probe.get("depth_levels"),
            reason=probe.get("reason"),
            records=records,
            exchange=venue,
            symbol=symbol,
            bid=probe.get("bid"),
            ask=probe.get("ask"),
            pricing_logs=pricing_logs,
        )

    prices_stats: dict[str, Any] = {}
    try:
        timeout = aiohttp.ClientTimeout(total=45)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            prices_stats = await ingest_category(session, "prices")
    except Exception as exc:  # noqa: BLE001
        prices_stats = {"ok": 0, "fail": 0, "skip": 0, "error": type(exc).__name__}

    bus = await refresh_live_truth(symbol=symbol)
    summary = await fetch_ingestion_health_summary()
    rows = len(summary) if isinstance(summary, list) else 0

    coverage: dict[str, Any] = {}
    try:
        from platform_universe import compute_universe_coverage

        coverage = await compute_universe_coverage()
        rows = max(rows, int(coverage.get("ingestion_health_rows") or 0))
    except Exception as exc:  # noqa: BLE001
        coverage = {"error": type(exc).__name__}

    ok_sources = [r for r in records if r.get("ok")]
    live_ingestion = int(coverage.get("live_ingestion_sources") or len(ok_sources))
    rollout: dict[str, Any] = {}
    try:
        from universe_rollout import live_rollout_status

        rollout = await live_rollout_status()
    except Exception as exc:  # noqa: BLE001
        rollout = {"error": type(exc).__name__}

    return {
        "ok": len(ok_sources) >= 2 and rows >= 2,
        "sources": records,
        "live_sources": len(ok_sources),
        "pricing_logs_written": pricing_logs,
        "pricing_log_exchanges": sorted({p["exchange"] for p in pricing_logs}),
        "prices_ingest": prices_stats,
        "ingestion_health_rows": rows,
        "health_summary_count": len(summary) if isinstance(summary, list) else 0,
        "truth_bus": {
            "ok": bus.get("ok"),
            "l2_venues": bus.get("l2_venues"),
            "perp_venues": bus.get("perp_venues"),
            "fabricated_depth": bus.get("fabricated_depth"),
            "funding_venues": bus.get("funding_venues"),
        },
        "coverage": {
            "ingestion_health_rows": coverage.get("ingestion_health_rows"),
            "live_ingestion_sources": live_ingestion,
            "coverage_percent_exchanges": coverage.get("coverage_percent_exchanges"),
        },
        "rollout": {
            "healthy_exchanges": rollout.get("healthy_exchanges"),
            "coverage_percent": rollout.get("coverage_percent"),
            "healthy_sample": rollout.get("healthy_sample"),
            "public_live_venues": rollout.get("public_live_venues"),
        },
        "scheduled_note": (
            "Durable L2 + prices ingest + pricing_logs written. "
            "Continuum: prove_scheduler_continuum(categories=prices)."
        ),
        "proved_at": _utcnow(),
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
    }


def ingestion_proof_status() -> dict[str, Any]:
    return {
        "surface": "institutional_ingestion_proof",
        "writes": ["ingestion_source_health", "pricing_logs"],
        "sources": [
            "okx_public_books",
            "kraken_public_depth",
            "gateio_public_spot",
            "bitget_public_spot",
            "kucoin_public_spot",
        ],
        "fabricated_depth_forbidden": True,
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
    }
