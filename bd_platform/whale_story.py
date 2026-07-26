"""Whale movement storytelling — narrative blocks for UI."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


async def whale_narrative(limit: int = 5) -> dict[str, Any]:
    from whale_tracker import get_latest_whale_alerts, get_latest_sector_flows

    alerts = await get_latest_whale_alerts(limit=limit)
    flows = await get_latest_sector_flows(limit=limit)
    stories: list[str] = []

    for alert in alerts[:limit]:
        asset = alert.get("asset") or alert.get("symbol") or "?"
        usd = float(alert.get("amount_usd") or alert.get("value_usd") or 0)
        direction = alert.get("direction") or alert.get("flow_type") or "movement"
        stories.append(
            f"Whale {direction} on {asset}: ${usd:,.0f} detected — "
            f"{'accumulation pressure' if 'in' in str(direction).lower() else 'distribution risk'}."
        )

    for flow in flows[:3]:
        sector = flow.get("sector") or "market"
        net = float(flow.get("net_flow_usd") or 0)
        stories.append(f"Sector {sector} net flow ${net:,.0f} in the last window.")

    if not stories:
        stories.append("No major whale narratives in the current window — market in equilibrium.")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stories": stories,
        "alert_count": len(alerts),
        "flow_count": len(flows),
    }
