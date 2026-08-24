"""
Due Diligence Report Engine — Feature #173 (BLACKDARK Research).

Auto-generated project diligence with evidence-based risk assessment.
Premium/Institution tier only.

Standards:
  1. Every claim sourced — no unsourced assertions
  2. Unknown explicitly marked — missing data = red flag
  3. Methodology versioned — reports cite methodology version
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DDReportEngine")

_FEATURE_ID = 173
_METHODOLOGY_VERSION = "2.1"
_REPORTS_PATH = Path("data/due_diligence_reports.jsonl")

ReportMode = Literal["one_page", "full"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _claim(
    *,
    section: str,
    claim: str,
    value: Any,
    source: str,
    citation: str,
    unknown: bool = False,
    red_flag: bool = False,
) -> dict[str, Any]:
    return {
        "section": section,
        "claim": claim,
        "value": value,
        "source": source,
        "citation": citation,
        "unknown": unknown,
        "red_flag": red_flag or unknown,
    }


def _append_report(row: dict[str, Any]) -> None:
    _REPORTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _REPORTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def _risk_level(score: float) -> str:
    if score >= 70:
        return "elevated"
    if score >= 45:
        return "moderate"
    return "lower"


async def build_due_diligence_report(
    asset: str = "BTC",
    *,
    mode: ReportMode = "one_page",
) -> dict[str, Any]:
    """Generate auto DD report from canonical data sources."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")
    claims: list[dict[str, Any]] = []
    risk_areas: list[dict[str, Any]] = []
    unknown_count = 0
    red_flag_count = 0

    async def _price():
        from bd_platform.price_aggregation_engine import aggregate_prices

        return await aggregate_prices(sym, use_cache=True)

    async def _health():
        from bd_platform.market_health_engine import build_market_health_dashboard

        return await build_market_health_dashboard(sym)

    async def _confidence():
        from bd_platform.confidence_engine import score_asset_confidence

        return await score_asset_confidence(sym)

    async def _financial():
        from research_lab import compute_financial_models

        return await compute_financial_models(sym)

    price_agg, health, confidence, financial = await asyncio.gather(
        _price(), _health(), _confidence(), _financial()
    )

    # Fundamentals
    if price_agg.get("ok"):
        claims.append(
            _claim(
                section="fundamentals",
                claim=f"{sym} aggregated spot price",
                value=price_agg.get("weighted_price"),
                source=price_agg.get("source_metadata", {}).get("primary_source", "price_aggregation_engine"),
                citation="GET /api/platform/infra/prices/aggregate",
            )
        )
        outlier_count = int(price_agg.get("outlier_count") or 0)
        if outlier_count > 0:
            risk_areas.append(
                {
                    "area": "price_discrepancy",
                    "severity": "medium",
                    "detail": f"{outlier_count} outlier sources excluded",
                    "source": "data_validation_layer",
                }
            )
    else:
        unknown_count += 1
        red_flag_count += 1
        claims.append(
            _claim(
                section="fundamentals",
                claim=f"{sym} spot price",
                value="UNKNOWN",
                source="price_aggregation_engine",
                citation="GET /api/platform/infra/prices/aggregate",
                unknown=True,
            )
        )

    # Market data
    if health.get("ok"):
        claims.append(
            _claim(
                section="market_data",
                claim=f"{sym} market health score",
                value=health.get("overall_score"),
                source="market_health_engine",
                citation="GET /api/platform/market-health/dashboard",
            )
        )
        if health.get("overall_status") == "unhealthy":
            risk_areas.append(
                {
                    "area": "market_health",
                    "severity": "high",
                    "detail": health.get("classification_reason"),
                    "source": "market_health_engine",
                }
            )
    else:
        unknown_count += 1
        claims.append(
            _claim(
                section="market_data",
                claim=f"{sym} market health",
                value="UNKNOWN",
                source="market_health_engine",
                citation="GET /api/platform/market-health/dashboard",
                unknown=True,
            )
        )

    # Tokenomics (proxy from research lab)
    if financial and not financial.get("error"):
        mvrv = (financial.get("mvrv") or {}).get("ratio")
        nvt = financial.get("nvt_ratio")
        claims.append(
            _claim(
                section="tokenomics",
                claim=f"{sym} MVRV ratio proxy",
                value=mvrv,
                source="research_lab",
                citation="research_lab.compute_financial_models",
            )
        )
        claims.append(
            _claim(
                section="tokenomics",
                claim=f"{sym} NVT ratio proxy",
                value=nvt,
                source="research_lab",
                citation="research_lab.compute_financial_models",
            )
        )
        if mvrv and float(mvrv) > 3.5:
            risk_areas.append(
                {
                    "area": "valuation",
                    "severity": "medium",
                    "detail": f"MVRV proxy {mvrv} above historical comfort zone",
                    "source": "research_lab",
                }
            )
    else:
        unknown_count += 1
        claims.append(
            _claim(
                section="tokenomics",
                claim=f"{sym} on-chain valuation metrics",
                value="UNKNOWN",
                source="research_lab",
                citation="research_lab.compute_financial_models",
                unknown=True,
            )
        )

    # Governance — explicit unknown unless sourced
    claims.append(
        _claim(
            section="governance",
            claim=f"{sym} governance structure",
            value="UNKNOWN",
            source="none",
            citation="No verified governance registry linked",
            unknown=True,
            red_flag=True,
        )
    )
    unknown_count += 1
    red_flag_count += 1
    risk_areas.append(
        {
            "area": "governance",
            "severity": "high",
            "detail": "Governance structure not verified — manual review required",
            "source": "methodology_v2.1",
        }
    )

    # Team — explicit unknown
    claims.append(
        _claim(
            section="team",
            claim=f"{sym} founding team identity",
            value="UNKNOWN",
            source="none",
            citation="No verified team registry (LinkedIn/official docs) linked",
            unknown=True,
            red_flag=True,
        )
    )
    unknown_count += 1
    red_flag_count += 1

    # Security
    validation = (price_agg or {}).get("validation") or {}
    verified = bool(validation.get("price_verified"))
    claims.append(
        _claim(
            section="security",
            claim=f"{sym} price feed validation",
            value="verified" if verified else "unverified",
            source="data_validation_layer",
            citation="GET /api/platform/infra/validation/status",
            red_flag=not verified,
        )
    )
    if not verified:
        risk_areas.append(
            {
                "area": "data_integrity",
                "severity": "medium",
                "detail": "Price feed not fully verified across sources",
                "source": "data_validation_layer",
            }
        )

    # Confidence / events
    if confidence.get("ok"):
        claims.append(
            _claim(
                section="events",
                claim=f"{sym} confidence score",
                value=confidence.get("confidence_score"),
                source="confidence_engine",
                citation="GET /api/platform/confidence/score",
            )
        )

    risk_score = float(confidence.get("confidence_score") or 50)
    inverted_risk = round(100 - risk_score, 1)
    overall_risk = _risk_level(inverted_risk)

    summary = (
        f"BLACKDARK Research DD — {sym}: {overall_risk} risk profile. "
        f"{len(risk_areas)} risk areas flagged, {unknown_count} unknowns (methodology v{_METHODOLOGY_VERSION})."
    )
    headline = summary

    one_page = {
        "asset": sym,
        "overall_risk": overall_risk,
        "risk_score": inverted_risk,
        "unknown_count": unknown_count,
        "red_flag_count": red_flag_count,
        "top_risk_areas": risk_areas[:5],
        "key_claims": [c for c in claims if c.get("section") in {"fundamentals", "market_data", "security"}][:6],
        "methodology_version": _METHODOLOGY_VERSION,
        "summary": summary,
    }

    elapsed = time.perf_counter() - t0
    report = {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "product": "BLACKDARK Research",
        "asset": sym,
        "mode": mode,
        "methodology_version": _METHODOLOGY_VERSION,
        "methodology_note": f"This report uses BLACKDARK DD methodology v{_METHODOLOGY_VERSION}",
        "review_workflow": {
            "stage": "auto_generated",
            "human_review_required": unknown_count > 0 or red_flag_count > 0,
            "next_step": "Institution analyst review when unknowns present",
        },
        "headline": headline,
        "summary": summary,
        "overall_risk": overall_risk,
        "risk_areas": risk_areas,
        "claims": claims if mode == "full" else one_page["key_claims"],
        "one_page": one_page,
        "citations": sorted({c["citation"] for c in claims}),
        "unknown_explicitly_marked": unknown_count,
        "red_flags": red_flag_count,
        "disclaimer": (
            "Auto-generated research report — not investment advice. "
            "Every claim is sourced or marked UNKNOWN. Verify independently before decisions."
        ),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }

    _append_report(
        {
            "feature_id": _FEATURE_ID,
            "asset": sym,
            "mode": mode,
            "overall_risk": overall_risk,
            "unknown_count": unknown_count,
            "timestamp": report["timestamp"],
        }
    )
    return report


def due_diligence_report_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "product": "BLACKDARK Research",
        "methodology_version": _METHODOLOGY_VERSION,
        "mode": "auto_generated",
        "tier_required": "institutional",
        "standards": [
            "every_claim_sourced",
            "unknown_explicitly_marked",
            "methodology_versioned",
            "review_workflow",
        ],
        "endpoints": {
            "one_page": "GET /api/platform/research/dd-report?asset=BTC&mode=one_page",
            "full": "GET /api/platform/research/dd-report?asset=BTC&mode=full",
        },
        "timestamp": _utcnow(),
    }
