"""
Launch-57 Phase 5 — Derivatives Batch 1.

Build order: #25 CAP-0085/0048 → #26 CAP-0086 → #27 CAP-0088 → #28 CAP-0089/0087 → #29 CAP-0090
"""

from __future__ import annotations

from typing import Any

from launch57.decision_common import load_decision_spine, stale_gate_body, stamp_decision_batch
from launch57.derivatives_common import attach_derivatives_envelope, light_heatmap_footer

LAUNCH57_DERIVATIVES_BATCH1_CAP_IDS: frozenset[int] = frozenset({85, 48, 86, 88, 89, 87, 90})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    85: 25,
    48: 25,
    86: 26,
    88: 27,
    89: 28,
    87: 28,
    90: 29,
}

_BINDING = "launch57_phase5_derivatives_batch1"
_MODULE = "launch57.derivatives_batch1"


async def _gated(
    *,
    capability_id: int,
    launch_item_id: int,
    surface: str,
    entrypoint: str,
    symbol: str,
    params: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    spine = await load_decision_spine(symbol, params)
    if not spine["live_eligible"]:
        body = stamp_decision_batch(
            stale_gate_body(
                capability_id=capability_id,
                launch_item_id=launch_item_id,
                surface=surface,
                symbol=spine["symbol"],
                spine=spine,
                entrypoint=entrypoint,
            ),
            capability_id=capability_id,
            launch_item_id=launch_item_id,
            entrypoint=entrypoint,
            batch_module=_MODULE,
            binding_source=_BINDING,
        )
        return attach_derivatives_envelope(body, spine=spine), None
    return None, spine


async def futures_open_interest_intelligence(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #25 / CAP-0085 — futures open interest intelligence."""
    from bd_platform.derivatives_hub import derivatives_overview

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=85,
        launch_item_id=25,
        surface="futures_open_interest_intelligence",
        entrypoint="futures_open_interest_intelligence",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    overview = await derivatives_overview(spine["symbol"])
    ft = (overview.get("free_tier") or {}) if isinstance(overview, dict) else {}
    body = stamp_decision_batch(
        {
            "surface": "futures_open_interest_intelligence",
            "symbol": spine["symbol"],
            "success": bool(overview),
            "open_interest_usd": ft.get("open_interest_usd"),
            "open_interest_contracts": ft.get("open_interest_contracts"),
            "derivatives_overview": overview,
            "price_context_from": "launch57.data_batch1",
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=85,
        launch_item_id=25,
        entrypoint="futures_open_interest_intelligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_derivatives_envelope(body, spine=spine)


async def futures_intelligence_suite(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #25 / CAP-0048 — futures intelligence suite (OI companion)."""
    from bd_platform.derivatives_hub import derivatives_overview

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=48,
        launch_item_id=25,
        surface="futures_intelligence_suite",
        entrypoint="futures_intelligence_suite",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    overview = await derivatives_overview(spine["symbol"])
    body = stamp_decision_batch(
        {
            "surface": "futures_intelligence_suite",
            "symbol": spine["symbol"],
            "success": bool(overview),
            "futures_intelligence_suite": overview,
            "alias_launch_item": 25,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=48,
        launch_item_id=25,
        entrypoint="futures_intelligence_suite",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_derivatives_envelope(body, spine=spine)


async def funding_rate_intelligence(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #26 / CAP-0086 — funding rate intelligence."""
    from bd_platform.derivatives_hub import derivatives_overview

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=86,
        launch_item_id=26,
        surface="funding_rate_intelligence",
        entrypoint="funding_rate_intelligence",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    overview = await derivatives_overview(spine["symbol"])
    ft = (overview.get("free_tier") or {}) if isinstance(overview, dict) else {}
    body = stamp_decision_batch(
        {
            "surface": "funding_rate_intelligence",
            "symbol": spine["symbol"],
            "success": bool(overview),
            "funding_rate": ft.get("funding_rate"),
            "funding_rate_pct": ft.get("funding_rate_pct"),
            "derivatives_overview": overview,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=86,
        launch_item_id=26,
        entrypoint="funding_rate_intelligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_derivatives_envelope(body, spine=spine)


async def liquidation_intelligence_light(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #27 / CAP-0088 — liquidation intelligence / light heatmap."""
    from bd_platform.liquidation_radar import liquidation_radar

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=88,
        launch_item_id=27,
        surface="liquidation_intelligence",
        entrypoint="liquidation_intelligence_light",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    radar = await liquidation_radar(spine["symbol"])
    alerts = radar.get("alerts") or []
    heatmap = {
        "asset": spine["symbol"],
        "alert_count": len(alerts),
        "alerts_preview": alerts[:12],
        "metrics": radar.get("metrics"),
        "data_source": radar.get("data_source"),
        "light_heatmap_scope": light_heatmap_footer(),
        "global_coverage_claim": "FORBIDDEN",
    }
    body = stamp_decision_batch(
        {
            "surface": "liquidation_intelligence",
            "symbol": spine["symbol"],
            "success": bool(radar),
            "liquidation": radar,
            "liquidation_heatmap_light": heatmap,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=88,
        launch_item_id=27,
        entrypoint="liquidation_intelligence_light",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_derivatives_envelope(body, spine=spine)


async def taker_buy_sell_pressure(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #28 / CAP-0089 — taker buy/sell pressure."""
    from bd_platform.derivatives_hub import derivatives_overview

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=89,
        launch_item_id=28,
        surface="taker_buy_sell_pressure",
        entrypoint="taker_buy_sell_pressure",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    overview = await derivatives_overview(spine["symbol"])
    ft = (overview.get("free_tier") or {}) if isinstance(overview, dict) else {}
    buy = float(ft.get("taker_buy_ratio") or 0.5)
    body = stamp_decision_batch(
        {
            "surface": "taker_buy_sell_pressure",
            "symbol": spine["symbol"],
            "success": bool(overview),
            "taker_buy_ratio": buy,
            "taker_sell_ratio": round(1 - buy, 4),
            "derivatives": ft,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=89,
        launch_item_id=28,
        entrypoint="taker_buy_sell_pressure",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_derivatives_envelope(body, spine=spine)


async def estimated_leverage_ratio(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #28 / CAP-0087 — estimated leverage ratio."""
    from bd_platform.heroes_capability_layer import leverage_ratio_overhang_197

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=87,
        launch_item_id=28,
        surface="estimated_leverage_ratio",
        entrypoint="estimated_leverage_ratio",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    payload = leverage_ratio_overhang_197(symbol=spine["symbol"])
    body = stamp_decision_batch(
        {
            "surface": "estimated_leverage_ratio",
            "symbol": spine["symbol"],
            "success": bool(payload),
            "estimated_leverage_ratio": payload.get("leverage_ratio") or payload.get("estimated_leverage_ratio"),
            "leverage_payload": payload,
            "alias_launch_item": 28,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=87,
        launch_item_id=28,
        entrypoint="estimated_leverage_ratio",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_derivatives_envelope(body, spine=spine)


async def derivatives_sentiment_composite(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #29 / CAP-0090 — derivatives sentiment composite."""
    from bd_platform.derivatives_hub import derivatives_overview
    from sentiment_engine import build_sentiment_context_safe

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=90,
        launch_item_id=29,
        surface="derivatives_market_sentiment_composite",
        entrypoint="derivatives_sentiment_composite",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    sentiment = await build_sentiment_context_safe(spine["symbol"])
    deriv = await derivatives_overview(spine["symbol"])
    composite = sentiment.get("score")
    body = stamp_decision_batch(
        {
            "surface": "derivatives_market_sentiment_composite",
            "symbol": spine["symbol"],
            "success": bool(sentiment or deriv),
            "sentiment": sentiment,
            "derivatives": deriv,
            "composite_score": composite,
            "one_line_summary": f"{spine['symbol']} derivatives composite from live spine + sentiment",
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=90,
        launch_item_id=29,
        entrypoint="derivatives_sentiment_composite",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_derivatives_envelope(body, spine=spine)


_DISPATCH: dict[int, str] = {
    85: "futures_open_interest_intelligence",
    48: "futures_intelligence_suite",
    86: "funding_rate_intelligence",
    88: "liquidation_intelligence_light",
    89: "taker_buy_sell_pressure",
    87: "estimated_leverage_ratio",
    90: "derivatives_sentiment_composite",
}


async def execute_launch57_derivatives_batch1(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in LAUNCH57_DERIVATIVES_BATCH1_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 derivatives batch 1")
    fn = globals()[_DISPATCH[capability_id]]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
