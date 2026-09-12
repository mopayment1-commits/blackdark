"""User-facing surface routes for CAP646 capabilities."""

from __future__ import annotations

from cap646.waves import USER_FACING, WAVE_A, WAVE_B, WAVE_C

# capability_id -> {ui_path, api_path, label}
USER_SURFACES: dict[int, dict[str, str]] = {
    17: {"ui_path": "/dashboard", "api_path": "/api/cap646/17/execute", "label": "Smart Alerts"},
    47: {"ui_path": "/dashboard", "api_path": "/api/cap646/47/execute", "label": "Spot Market Metrics"},
    48: {"ui_path": "/dashboard", "api_path": "/api/cap646/48/execute", "label": "Futures Intelligence"},
    60: {"ui_path": "/dashboard", "api_path": "/api/cap646/60/execute", "label": "Alerts"},
    103: {"ui_path": "/institutional", "api_path": "/api/institutional", "label": "API Data Platform"},
    129: {"ui_path": "/dashboard", "api_path": "/api/cap646/129/execute", "label": "Sentiment"},
    175: {"ui_path": "/dashboard", "api_path": "/api/cap646/175/execute", "label": "Sentiment Intelligence"},
    245: {"ui_path": "/dashboard", "api_path": "/api/cap646/245/execute", "label": "Freshness Alerts"},
    507: {"ui_path": "/cap646", "api_path": "/api/cap646/507/execute", "label": "OHLCV"},
    534: {"ui_path": "/cap646", "api_path": "/api/cap646/534/execute", "label": "Market Data"},
    214: {"ui_path": "/dashboard", "api_path": "/api/cap646/214/execute", "label": "Watchlists"},
    629: {"ui_path": "/dashboard", "api_path": "/api/cap646/629/execute", "label": "Wallet Alerts"},
    631: {"ui_path": "/cap646", "api_path": "/api/cap646/631/execute", "label": "Ingestion Architecture"},
    630: {"ui_path": "/cap646", "api_path": "/api/cap646/630/execute", "label": "Freshness Assurance"},
    338: {"ui_path": "/cap646", "api_path": "/api/cap646/338/execute", "label": "Data Quality Pipeline"},
    500: {"ui_path": "/cap646", "api_path": "/api/cap646/500/execute", "label": "Normalization"},
    584: {"ui_path": "/dashboard", "api_path": "/api/arbitrage/opportunities", "label": "Risk Shield"},
    642: {"ui_path": "/oracle-accuracy", "api_path": "/api/cap646/642/execute", "label": "AI Provenance Footer"},
    644: {"ui_path": "/institutional", "api_path": "/api/cap646/644/execute", "label": "Capacity Evidence"},
    646: {"ui_path": "/institutional", "api_path": "/api/cap646/646/execute", "label": "Chaos Resilience"},
}


def user_surface_for(capability_id: int) -> dict[str, str] | None:
    if capability_id not in USER_FACING:
        return None
    if capability_id in USER_SURFACES:
        return USER_SURFACES[capability_id]
    return {
        "ui_path": "/cap646",
        "api_path": f"/api/cap646/{capability_id}/execute",
        "label": f"Capability #{capability_id}",
    }


def hub_context() -> dict:
    return {
        "waves": [
            {"id": "A", "title": "Wave A — Foundations", "capability_ids": list(WAVE_A)},
            {"id": "B", "title": "Wave B — Alerts & Domains", "capability_ids": list(WAVE_B)},
            {"id": "C", "title": "Wave C — Market Depth", "capability_ids": list(WAVE_C)},
        ],
        "user_facing": {str(k): v for k, v in USER_SURFACES.items()},
        "user_facing_count": len(USER_FACING),
        "api_base": "/api/cap646",
        "ui_base": "/cap646",
    }
