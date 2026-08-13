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
    live = exchanges_by_status("ingestion_ready")
    mapped = exchanges_by_status("ccxt_mapped")
    planned = [r for r in universe_exchanges() if r.get("status") == "planned"]
    prov = compute_data_provenance_score(symbol="BTC")

    doctrine = (
        "We do not claim coverage we cannot execute. "
        "Decision-grade = live books + freshness + Net-Edge. "
        "Planned venues are roadmap, never marketed as live."
    )

    return {
        "surface": "coverage_honesty_board",
        "generated_at": datetime.now(UTC).isoformat(),
        "headline": "Coverage honesty — depth over vanity breadth",
        "doctrine": doctrine,
        "live": {
            "count": len(live),
            "ids": [r.get("id") for r in live],
            "label": "ingestion_ready — used in decisions",
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
            "live_exchange_count": len(live),
            "target_exchange_count": (coverage.get("target") or {}).get("exchanges"),
            "live_ingestion_sources": coverage.get("live_ingestion_sources"),
            "vanity_coverage_percent_if_miscounted": coverage.get("coverage_percent_exchanges"),
            "decision_grade_posture": prov.get("band"),
            "btc_provenance_score": prov.get("score"),
        },
        "radical_fix": {
            "problem": "Newer brand + narrower live coverage vs Glassnode/Kaiko catalogs",
            "solution": (
                "Publish LIVE vs PLANNED with provenance score on every decision; "
                "refuse to inflate coverage; win on executable honesty + public miss feed."
            ),
            "status": "product_complete",
        },
        "data_trust": {
            "doc": "docs/DATA_TRUST_LAW_BINDING.md",
            "api": "/api/strategy/data-trust-law",
            "canonical_api": "/api/public/canonical-market-state",
            "closure_api": "/api/public/data-trust-closure",
            "rule": "Catalog size ≠ decision coverage. Aggregators never produce venue L2.",
        },
        "provenance_sample": prov,
        "strategy": coverage.get("strategy"),
        "page": "/coverage-honesty",
        "api": "/api/public/coverage-honesty",
        "share_line": (
            f"BLACKDARK Coverage Honesty · {len(live)} live decision venues · "
            f"planned never sold as live · Provenance {prov.get('score')} · /coverage-honesty"
        ),
        "disclaimer": (
            "Analytical coverage posture — not a promise of every global venue. "
            "Not financial advice."
        ),
    }
