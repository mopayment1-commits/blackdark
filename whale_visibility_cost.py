"""
BLACKDARK — F7 Whale Visibility Cost Meter.

Live estimate: if you execute $X now, expected visibility tax (MEV/slippage) ≈ $Y.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def build_visibility_cost_meter(
    *,
    asset: str = "ETH",
    notional_usd: float = 250_000.0,
    venue: str = "public_memepool",
) -> dict[str, Any]:
    asset_u = (asset or "ETH").upper()
    notional = max(0.0, float(notional_usd))

    # Compose MEV sandwich heuristic + size impact + venue premium
    try:
        from mev_sandwich_report import build_mev_sandwich_report

        mev = build_mev_sandwich_report(asset=asset_u, notional_usd=notional)
        sandwich_bps = float(mev.get("estimated_sandwich_bps") or 5.0)
    except Exception:
        mev = {}
        sandwich_bps = 8.0 if asset_u in {"ETH", "WETH"} else 5.0

    # Size impact grows with notional (educational curve)
    size_bps = min(40.0, 2.0 + (notional / 1_000_000.0) * 6.0)
    venue_bps = 3.0 if "private" in venue.lower() or "relay" in venue.lower() else 0.0
    # Private relay reduces sandwich component
    effective_sandwich = sandwich_bps * (0.35 if venue_bps else 1.0)
    total_bps = round(effective_sandwich + size_bps + (0 if venue_bps else 1.5), 2)
    cost = round(notional * total_bps / 10_000.0, 2)

    stealth = {}
    try:
        from stealth_execution_advisor import advise_stealth_execution

        stealth = advise_stealth_execution(asset=asset_u, notional_usd=notional)
    except Exception:
        stealth = {}

    half = {}
    try:
        from opportunity_tracker import estimate_opportunity_half_life

        half = estimate_opportunity_half_life({"kind": "cross_exchange", "asset": asset_u})
    except Exception:
        half = {}

    share = (
        f"BLACKDARK Visibility Cost · {asset_u} · ${notional:,.0f} now ≈ ${cost:,.0f} "
        f"({total_bps} bps MEV/slippage tax) · /visibility-cost · Not financial advice"
    )
    return {
        "feature_id": "F7",
        "surface": "whale_visibility_cost_meter",
        "product_complete": True,
        "generated_at": _utcnow(),
        "asset": asset_u,
        "notional_usd": notional,
        "venue": venue,
        "components_bps": {
            "sandwich_mev": round(effective_sandwich, 2),
            "size_impact": round(size_bps, 2),
            "public_venue_premium": 0.0 if venue_bps else 1.5,
        },
        "total_visibility_bps": total_bps,
        "estimated_visibility_cost_usd": cost,
        "headline": f"Visibility will cost ≈ ${cost:,.0f}",
        "stealth": stealth,
        "half_life": half,
        "mev_report": {
            "estimated_sandwich_bps": mev.get("estimated_sandwich_bps"),
            "api": "/api/mev/sandwich-report",
        },
        "advice": [
            "Split size via Stealth Advisor before marketable size",
            "Prefer private relay when available",
            "Do not chase a dying Half-Life into sandwichable flow",
        ],
        "share_text": share,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(share)}",
            "whatsapp": f"https://wa.me/?text={quote(share)}",
        },
        "page": "/visibility-cost",
        "api": "/api/visibility-cost",
        "disclaimer": "Educational visibility tax estimate — not a guaranteed fill cost.",
    }
