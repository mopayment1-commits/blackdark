"""Institutional ingestion proof — durable health rows from live public venues.

One-shot (and optionally scheduler-backed) path that:
1. Pulls real venue L2 via live_data_truth_probe / truth bus
2. Upserts `ingestion_source_health` so universe coverage sees durable rows
3. Never fabricates success without a live probe

This closes the clean-room gap where coverage was only an on-demand probe
(`ingestion_health_rows:0`).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def prove_durable_ingestion(*, symbol: str = "BTC/USDT") -> dict[str, Any]:
    """Record live venue probes into ingestion_source_health and refresh truth bus."""
    from canonical_truth_bus import refresh_live_truth
    from database import fetch_ingestion_health_summary, init_db, upsert_ingestion_health
    from live_data_truth_probe import probe_kraken_depth, probe_okx_book

    await init_db()
    records: list[dict[str, Any]] = []

    okx = await probe_okx_book("BTC-USDT", depth=20)
    await upsert_ingestion_health(
        "okx_public_books",
        "prices",
        ok=bool(okx.get("ok") and okx.get("live") and not okx.get("fabricated_depth")),
        error=None if okx.get("ok") else str(okx.get("reason") or "okx_fail"),
    )
    records.append(
        {
            "source_id": "okx_public_books",
            "ok": bool(okx.get("ok") and okx.get("live")),
            "depth_source": okx.get("depth_source"),
            "levels": okx.get("depth_levels"),
        }
    )

    kr = await probe_kraken_depth("XBTUSDT", depth=25)
    await upsert_ingestion_health(
        "kraken_public_depth",
        "prices",
        ok=bool(kr.get("ok") and kr.get("live") and not kr.get("fabricated_depth")),
        error=None if kr.get("ok") else str(kr.get("reason") or "kraken_fail"),
    )
    records.append(
        {
            "source_id": "kraken_public_depth",
            "ok": bool(kr.get("ok") and kr.get("live")),
            "depth_source": kr.get("depth_source"),
            "levels": kr.get("depth_levels"),
        }
    )

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
    return {
        "ok": len(ok_sources) >= 1 and rows >= 1,
        "sources": records,
        "live_sources": len(ok_sources),
        "ingestion_health_rows": rows,
        "health_summary": summary,
        "truth_bus": {
            "ok": bus.get("ok"),
            "l2_venues": bus.get("l2_venues"),
            "fabricated_depth": bus.get("fabricated_depth"),
            "funding_venues": bus.get("funding_venues"),
        },
        "coverage": {
            "ingestion_health_rows": coverage.get("ingestion_health_rows"),
            "live_ingestion_sources": coverage.get("live_ingestion_sources"),
            "coverage_percent_exchanges": coverage.get("coverage_percent_exchanges"),
        },
        "scheduled_note": (
            "Durable rows written now. Full scheduler: INGESTION_ENABLED=true + "
            "startup_orchestrator / start_ingestion_scheduler(bootstrap=True)."
        ),
        "proved_at": _utcnow(),
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
    }


def ingestion_proof_status() -> dict[str, Any]:
    return {
        "surface": "institutional_ingestion_proof",
        "writes": ["ingestion_source_health"],
        "sources": ["okx_public_books", "kraken_public_depth"],
        "fabricated_depth_forbidden": True,
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
    }
