"""Decision expiry / half-life integration for Decision Truth."""

from __future__ import annotations

from typing import Any


def attach_half_life(payload: dict[str, Any], *, asset: str | None = None) -> dict[str, Any]:
    """Attach opportunity half-life metadata when available."""
    out = dict(payload)
    sym = str(asset or out.get("symbol") or out.get("asset") or "BTC").upper()
    try:
        from opportunity_half_life import compute_opportunity_half_life

        hl = compute_opportunity_half_life(sym, out)
        out["opportunity_half_life"] = hl
    except Exception:
        out["opportunity_half_life"] = {
            "asset": sym,
            "expected_half_life_seconds": out.get("horizon_seconds"),
            "remaining_seconds": out.get("remaining_seconds"),
            "source": "fallback",
        }
    return out
