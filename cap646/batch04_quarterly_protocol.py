"""Domain logic for capability #151 — Quarterly Protocol Performance Reports."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def quarter_label(*, now: datetime | None = None) -> str:
    now = now or datetime.now(UTC)
    q = (now.month - 1) // 3 + 1
    return f"{now.year}-Q{q}"


def build_quarterly_protocol_report(
    *,
    symbol: str,
    explanation: dict[str, Any],
    defi_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Transform hero opportunity + DeFi protocol snapshot into quarterly report payload."""
    breakdown = explanation.get("breakdown") or {}
    tvl = float(defi_snapshot.get("tvl_usd") or 0)
    opportunity = float(explanation.get("opportunity_score") or 0)
    risk = float(explanation.get("risk_score") or 0)

    dimension_scores = {
        key: 1.0 if str(val.get("value", "")).lower() in {"positive", "adequate", "neutral", "accumulating", "low_risk", "support_zone"}
        else 0.5
        for key, val in breakdown.items()
        if isinstance(val, dict)
    }
    performance_score = round(
        (sum(dimension_scores.values()) / max(len(dimension_scores), 1)) * 100,
        1,
    )

    return {
        "ok": True,
        "feature_ref": 151,
        "symbol": symbol.upper(),
        "catalog_goal": "quarterly_protocol_performance_reports",
        "reporting_period": "quarterly",
        "quarter_label": quarter_label(),
        "protocol_symbol": symbol.upper(),
        "protocol_tvl_usd": tvl,
        "performance_score": performance_score,
        "opportunity_score": opportunity,
        "risk_score": risk,
        "confidence_level": explanation.get("confidence_level") or "medium",
        "protocol_performance": {
            "quarterly_summary": {
                "headline": f"{symbol.upper()} quarterly protocol review",
                "performance_score": performance_score,
                "tvl_usd": tvl,
                "opportunity_score": opportunity,
                "risk_score": risk,
            },
            "dimension_breakdown": breakdown,
            "data_sources": ["explain_opportunity_151", "ingest_defillama_149"],
        },
        "insight_not_recommendation": True,
    }
