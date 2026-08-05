"""
BLACKDARK — Stealth Execution Advisor (whale persona shell).

Advisory sizing / slice guidance to reduce market impact — wraps existing
smart-order / risk ideas without claiming live stealth routing guarantees.
Deepens Portfolio AI + whale entry (Section H).
"""

from __future__ import annotations

from typing import Any


def advise_stealth_execution(
    *,
    asset: str,
    notional_usd: float,
    side: str = "buy",
    half_life_seconds: float | None = None,
    average_daily_volume_usd: float | None = None,
) -> dict[str, Any]:
    notional = max(0.0, float(notional_usd or 0))
    adv = float(average_daily_volume_usd or 50_000_000)
    participation = (notional / adv) if adv > 0 else 0.0

    if participation > 0.02:
        slices = max(5, min(20, int(participation * 400)))
        style = "aggressive_slice"
        note = "Size is large vs ADV — slice across time; avoid single print."
    elif participation > 0.005:
        slices = max(3, min(10, int(participation * 500)))
        style = "standard_slice"
        note = "Moderate footprint — use staggered limits."
    else:
        slices = 1
        style = "single_clip_ok"
        note = "Small vs ADV — single clip usually fine."

    urgency = "normal"
    if half_life_seconds is not None and half_life_seconds < 30:
        urgency = "edge_dying"
        note += " Half-life short — prioritize speed over stealth or stand down."

    slice_usd = round(notional / slices, 2) if slices else notional
    return {
        "asset": asset.upper(),
        "side": side.lower(),
        "notional_usd": round(notional, 2),
        "participation_of_adv": round(participation, 5),
        "recommended_slices": slices,
        "slice_usd": slice_usd,
        "style": style,
        "urgency": urgency,
        "advice": note,
        "disclaimer": (
            "Advisory only — not a guarantee against front-running. "
            "Not financial advice. Live stealth routing may require Whale execution keys."
        ),
        "hero_deepening": "portfolio_ai",
        "status": "advisory_shell_v1",
    }
