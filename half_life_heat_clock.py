"""
BLACKDARK — Half-Life Heat Clock (U3) for Decision Desk.

Urgency bands + clock model for opportunity remaining life (seconds = money).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _band(remaining: float, disappear_p: float) -> dict[str, Any]:
    if remaining <= 5 or disappear_p >= 0.85:
        return {
            "id": "critical",
            "label": "CRITICAL",
            "heat": 1.0,
            "color": "#ef4444",
            "advice": "Edge dying — size only if execution path is already hot.",
        }
    if remaining <= 15 or disappear_p >= 0.55:
        return {
            "id": "high",
            "label": "HOT",
            "heat": 0.72,
            "color": "#f59e0b",
            "advice": "Half-life compressing — desk priority.",
        }
    if remaining <= 45:
        return {
            "id": "warm",
            "label": "WARM",
            "heat": 0.42,
            "color": "#eab308",
            "advice": "Window open — validate Net-Edge before commit.",
        }
    return {
        "id": "cool",
        "label": "COOL",
        "heat": 0.18,
        "color": "#22d3ee",
        "advice": "More time — still subject to Truth + Veto gates.",
    }


def build_heat_clock(opportunity: dict[str, Any] | None = None) -> dict[str, Any]:
    from opportunity_tracker import estimate_opportunity_half_life, get_active_durations, half_life_status

    opp = dict(opportunity or {})
    if not opp:
        active = get_active_durations(limit=1)
        if active:
            row = active[0]
            opp = {
                "kind": row.get("kind"),
                "asset": row.get("asset"),
                "live_duration_seconds": row.get("duration_seconds"),
            }
        else:
            opp = {"kind": "cross_exchange", "asset": "BTC", "live_duration_seconds": 6}

    half = estimate_opportunity_half_life(opp, live_duration_seconds=opp.get("live_duration_seconds"))
    remaining = float(half.get("remaining_seconds") or 0)
    disappear = float(half.get("disappearance_probability") or 0)
    expected = float(half.get("expected_half_life_seconds") or 1) or 1.0
    elapsed_frac = min(1.0, max(0.0, 1.0 - (remaining / expected)))
    band = _band(remaining, disappear)

    # SVG clock: 360° sweep by elapsed fraction
    angle = round(elapsed_frac * 360, 1)
    svg = (
        f'<svg viewBox="0 0 120 120" width="160" height="160" aria-label="Half-life heat clock">'
        f'<circle cx="60" cy="60" r="52" fill="#0a0a0f" stroke="#2a2a35" stroke-width="4"/>'
        f'<circle cx="60" cy="60" r="44" fill="none" stroke="{band["color"]}" stroke-width="8" '
        f'stroke-dasharray="{round(angle * 0.767, 1)} 276" stroke-linecap="round" '
        f'transform="rotate(-90 60 60)"/>'
        f'<text x="60" y="58" text-anchor="middle" fill="#e4e4e7" font-size="18" font-family="monospace">'
        f'{int(remaining)}s</text>'
        f'<text x="60" y="76" text-anchor="middle" fill="{band["color"]}" font-size="11">{band["label"]}</text>'
        f"</svg>"
    )

    return {
        "surface": "half_life_heat_clock",
        "generated_at": datetime.now(UTC).isoformat(),
        "opportunity": {
            "kind": opp.get("kind"),
            "asset": opp.get("asset") or opp.get("symbol"),
        },
        "half_life": half,
        "band": band,
        "elapsed_fraction": round(elapsed_frac, 4),
        "sweep_degrees": angle,
        "svg": svg,
        "desk_line": (
            f"{band['label']} · {int(remaining)}s left · "
            f"disappear p={disappear:.0%} · {band['advice']}"
        ),
        "status": half_life_status(),
        "api": "/api/oracle/half-life/heat",
        "tier_surface": "decision_desk",
        "disclaimer": "Time model is probabilistic — not a guarantee the edge fills.",
    }


def build_heat_clock_board(limit: int = 8) -> dict[str, Any]:
    from opportunity_tracker import get_active_durations

    clocks = []
    for row in get_active_durations(limit=limit):
        clocks.append(
            build_heat_clock(
                {
                    "kind": row.get("kind"),
                    "asset": row.get("asset"),
                    "live_duration_seconds": row.get("duration_seconds"),
                }
            )
        )
    if not clocks:
        clocks = [build_heat_clock(None)]
    return {
        "surface": "half_life_heat_board",
        "generated_at": datetime.now(UTC).isoformat(),
        "count": len(clocks),
        "clocks": clocks,
        "api": "/api/oracle/half-life/heat",
    }
