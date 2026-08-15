"""
BLACKDARK — Coverage Honesty Board (radical fix for relative coverage weakness).

Doctrine: depth of LIVE executable venues beats vanity of 100 planned names.
Publishes live vs planned clearly so narrower coverage becomes a trust moat.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


async def build_coverage_honesty_board() -> dict[str, Any]:
    from data_provenance_score import compute_data_provenance_score
    from platform_universe import compute_universe_coverage, exchanges_by_status, universe_exchanges

    coverage = await compute_universe_coverage()
    catalog_ready = exchanges_by_status("ingestion_ready")
    mapped = exchanges_by_status("ccxt_mapped")
    planned = [r for r in universe_exchanges() if r.get("status") == "planned"]
    prov = compute_data_provenance_score(symbol="BTC")
    live_sources = int(coverage.get("live_ingestion_sources") or 0)

    doctrine = (
        "We do not claim coverage we cannot execute. "
        "Decision-grade = live books + freshness + Net-Edge. "
        "Catalog ingestion_ready ≠ live healthy sources. "
        "Planned venues are roadmap, never marketed as live."
    )

    return {
        "surface": "coverage_honesty_board",
        "generated_at": datetime.now(UTC).isoformat(),
        "headline": "Coverage honesty — depth over vanity breadth",
        "doctrine": doctrine,
        "live": {
            "count": live_sources,
            "ids": [],
            "label": "live_ingestion_sources — healthy observed feeds only",
        },
        "catalog_ready": {
            "count": len(catalog_ready),
            "ids": [r.get("id") for r in catalog_ready][:20],
            "label": "ingestion_ready catalog — NOT live decision venues",
        },
        "next_wave": {
            "count": len(mapped),
            "ids": [r.get("id") for r in mapped][:20],
            "label": "ccxt_mapped — rollout queue, not live claims",
        },
        "planned": {
            "count": len(planned),
            "label": "catalog / regional — never sold as live",
        },
        "targets": coverage.get("target") or {},
        "metrics": {
            "live_exchange_count": live_sources,
            "catalog_ready_count": len(catalog_ready),
            "target_exchange_count": (coverage.get("target") or {}).get("exchanges"),
            "live_ingestion_sources": live_sources,
            "live_coverage_percent_exchanges": coverage.get("live_coverage_percent_exchanges"),
            "catalog_ready_percent_exchanges": coverage.get("catalog_ready_percent_exchanges"),
            "decision_grade_posture": prov.get("band"),
            "btc_provenance_score": prov.get("score"),
        },
        "radical_fix": {
            "problem": "Newer brand + narrower live coverage vs Glassnode/Kaiko catalogs",
            "solution": (
                "Publish LIVE healthy sources vs CATALOG ready; "
                "refuse to inflate coverage; win on executable honesty + public miss feed."
            ),
            "status": "honesty_surface_not_product_complete",
        },
        "provenance_sample": prov,
        "strategy": coverage.get("strategy"),
        "page": "/coverage-honesty",
        "api": "/api/public/coverage-honesty",
        "share_line": (
            f"BLACKDARK Coverage Honesty · {live_sources} live healthy sources · "
            f"{len(catalog_ready)} catalog-ready (not live) · "
            f"Provenance {prov.get('score')} · /coverage-honesty"
        ),
        "disclaimer": (
            "Analytical coverage posture — not a promise of every global venue. "
            "Catalog-ready is not live. Not financial advice."
        ),
    }
