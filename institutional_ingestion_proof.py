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


async def prove_durable_ingestion(*, symbol: str = "BTC/USDT") -> dict[str, Any]:
    """Record live venue probes + free prices ingest into ingestion_source_health."""
    import aiohttp

    from canonical_truth_bus import refresh_live_truth
    from database import fetch_ingestion_health_summary, init_db
    from ingestion_fetchers import ingest_category
    from live_data_truth_probe import (
        CORE_PUBLIC_CEX_MESH,
        _probe_aggregator_spot_l2,
        mesh_symbol_for,
        probe_kraken_depth,
        probe_okx_book,
    )

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

    # Expand durable health + pricing_logs across curated public CEX mesh (bounded concurrency).
    import asyncio

    mesh_venues = [v for v in CORE_PUBLIC_CEX_MESH if v not in {"okx", "kraken"}]
    sem = asyncio.Semaphore(8)

    async def _mesh_one(venue: str) -> dict[str, Any]:
        async with sem:
            probe_symbol = mesh_symbol_for(venue)
            try:
                return await asyncio.wait_for(
                    _probe_aggregator_spot_l2(venue, probe_symbol), timeout=14.0
                )
            except TimeoutError:
                return {
                    "ok": False,
                    "live": False,
                    "venue": venue,
                    "symbol": probe_symbol,
                    "reason": "probe_timeout",
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "ok": False,
                    "live": False,
                    "venue": venue,
                    "symbol": probe_symbol,
                    "reason": type(exc).__name__,
                }

    mesh_probes = await asyncio.gather(*[_mesh_one(v) for v in mesh_venues])
    for probe in mesh_probes:
        venue = str(probe.get("venue") or "unknown")
        ok = bool(
            probe.get("ok")
            and probe.get("live")
            and probe.get("depth_source") == "venue_l2"
            and not probe.get("fabricated_depth")
        )
        await _upsert_book_source(
            source_id=f"{venue}_public_spot",
            ok=ok,
            depth_source=probe.get("depth_source"),
            levels=probe.get("depth_levels"),
            reason=probe.get("reason"),
            records=records,
            exchange=venue,
            symbol=str(probe.get("symbol") or mesh_symbol_for(venue)),
            bid=probe.get("bid"),
            ask=probe.get("ask"),
            pricing_logs=pricing_logs,
        )

    try:
        from ccxt_market_fetcher import close_ccxt_pool

        await close_ccxt_pool()
    except Exception:
        pass

    prices_stats: dict[str, Any] = {}
    try:
        timeout = aiohttp.ClientTimeout(total=45)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            prices_stats = await ingest_category(session, "prices")
    except Exception as exc:  # noqa: BLE001
        prices_stats = {"ok": 0, "fail": 0, "skip": 0, "error": type(exc).__name__}

    bus = await refresh_live_truth(symbol=symbol)

    # Full registry-100 catalog price-health (honest synthetic_mid allowed for rollout %).
    catalog: dict[str, Any] = {}
    try:
        from full_catalog_mesh_proof import prove_full_catalog_health

        catalog = await prove_full_catalog_health()
    except Exception as exc:  # noqa: BLE001
        catalog = {"ok": False, "error": type(exc).__name__}

    summary = await fetch_ingestion_health_summary()
    rows = len(summary) if isinstance(summary, list) else 0
    # Prefer catalog prove metrics — avoid nested prove_multi_venue_live in coverage.
    coverage = dict(catalog.get("coverage") or {})
    if not coverage.get("live_ingestion_sources"):
        healthy_count = sum(1 for r in (summary or []) if isinstance(r, dict) and r.get("last_ok_at"))
        coverage = {
            "live_ingestion_sources": healthy_count,
            "coverage_percent_exchanges": round(healthy_count / 100 * 100, 1),
            "ingestion_health_rows": rows,
        }
    rows = max(rows, int(coverage.get("ingestion_health_rows") or 0))

    ok_sources = [r for r in records if r.get("ok")]
    live_ingestion = int(
        coverage.get("live_ingestion_sources")
        or catalog.get("healthy_exchanges")
        or len(ok_sources)
    )
    rollout: dict[str, Any] = {}
    try:
        from universe_rollout import live_rollout_status

        # pricing_logs already written above — skip second full public mesh probe.
        rollout = await live_rollout_status(include_public_probe=False)
    except Exception as exc:  # noqa: BLE001
        rollout = {"error": type(exc).__name__}

    catalog_pct = float(catalog.get("coverage_percent") or 0)
    rollout_pct = float(rollout.get("coverage_percent") or catalog_pct)
    return {
        "ok": len(ok_sources) >= 2 and rows >= 2 and catalog.get("ok") is True,
        "sources": records,
        "live_sources": max(len(ok_sources), int(catalog.get("healthy_exchanges") or 0)),
        "pricing_logs_written": pricing_logs,
        "pricing_log_exchanges": sorted(
            {p["exchange"] for p in pricing_logs}
            | set(catalog.get("l2_venues") or [])
            | set(catalog.get("tob_venues") or [])
            | set(catalog.get("synthetic_mid_venues") or [])
        ),
        "prices_ingest": prices_stats,
        "ingestion_health_rows": rows,
        "health_summary_count": len(summary) if isinstance(summary, list) else 0,
        "full_catalog": {
            "ok": catalog.get("ok"),
            "healthy_exchanges": catalog.get("healthy_exchanges"),
            "coverage_percent": catalog.get("coverage_percent"),
            "depth_breakdown": catalog.get("depth_breakdown"),
            "failed_count": catalog.get("failed_count"),
            "failed_sample": (catalog.get("failed") or [])[:10],
        },
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
            "coverage_percent_exchanges": coverage.get("coverage_percent_exchanges")
            or catalog.get("coverage", {}).get("coverage_percent_exchanges"),
        },
        "rollout": {
            "healthy_exchanges": rollout.get("healthy_exchanges"),
            "coverage_percent": rollout_pct,
            "healthy_sample": rollout.get("healthy_sample"),
            "public_live_venues": rollout.get("public_live_venues"),
        },
        "scheduled_note": (
            "Durable L2 mesh + full registry-100 catalog price-health + pricing_logs. "
            "synthetic_mid counted for catalog coverage only — not L2 VC."
        ),
        "proved_at": _utcnow(),
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
    }


def ingestion_proof_status() -> dict[str, Any]:
    from live_data_truth_probe import CORE_PUBLIC_CEX_MESH

    return {
        "surface": "institutional_ingestion_proof",
        "writes": ["ingestion_source_health", "pricing_logs"],
        "sources": ["okx_public_books", "kraken_public_depth", *[f"{v}_public_spot" for v in CORE_PUBLIC_CEX_MESH]],
        "mesh_target_count": len(CORE_PUBLIC_CEX_MESH),
        "fabricated_depth_forbidden": True,
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
    }
