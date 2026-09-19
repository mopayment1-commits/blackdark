"""
Launch-57 Phase 5 — Derivatives Batch 1.

Build order: #25 CAP-0085/0048 → #26 CAP-0086 → #27 CAP-0088 → #28 CAP-0089/0087 → #29 CAP-0090
"""

from __future__ import annotations

from typing import Any

from launch57.decision_common import load_decision_spine, stale_gate_body, stamp_decision_batch
from launch57.derivatives_common import attach_derivatives_envelope, light_heatmap_footer
from launch57.trust_adaptive_common import (
    apply_funding_rate_derivatives_semantics,
    apply_liquidation_derivatives_semantics,
    apply_open_interest_derivatives_semantics,
    apply_taker_leverage_derivatives_semantics,
    attach_adaptive_disclosure,
    build_derivatives_composite_disclosure,
    build_funding_rate_derivatives_disclosure,
    build_level1_decision_disclosure,
    build_liquidation_derivatives_disclosure,
    build_open_interest_derivatives_disclosure,
    build_taker_leverage_derivatives_disclosure,
    compute_derivatives_sentiment_composite,
)

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


def _governed_params(p: dict[str, Any], semantics: dict[str, Any], spine: dict[str, Any]) -> dict[str, Any]:
    out = dict(p)
    governed = dict(out.get("governed_payload") or {})
    contract = semantics.get("contract") or {}
    if contract.get("material_contradiction"):
        governed["critical_contradiction"] = contract["material_contradiction"]
    if contract.get("material_limitation"):
        governed["critical_limitation"] = contract["material_limitation"]
    if semantics.get("material_disagreements"):
        governed["contradictions"] = semantics["material_disagreements"]
    out["governed_payload"] = governed
    out["freshness_state"] = spine.get("freshness_state")
    return out


def _attach_derivatives_adaptive(
    wrapped: dict[str, Any],
    *,
    p: dict[str, Any],
    spine: dict[str, Any],
    launch_item_id: int,
    surface: str,
    semantics: dict[str, Any],
    disclosure_key: str,
    disclosure: dict[str, Any],
) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    wrapped["derivatives_contract"] = contract
    wrapped["evidence_class_visible"] = contract.get("evidence_class")
    wrapped["evidence_display"] = {
        "canonical_evidence_class": contract.get("evidence_class"),
        "freshness_state": spine.get("freshness_state"),
    }
    governed_p = _governed_params(p, semantics, spine)
    uncertainty = "qualified" if contract.get("material_contradiction") or semantics.get("material_disagreements") else "standard"
    level1 = build_level1_decision_disclosure(
        governed_p,
        launch_item_id=launch_item_id,
        surface=surface,
        answer_state=semantics.get("answer_state"),
        evidence_display=wrapped.get("evidence_display"),
        uncertainty=uncertainty,
    )
    return attach_adaptive_disclosure(wrapped, level1, extra={disclosure_key: disclosure})


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
        return attach_derivatives_envelope(body, spine=spine, params=params), None
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
    semantics = apply_open_interest_derivatives_semantics(overview=overview, ft=ft, spine=spine)
    body = stamp_decision_batch(
        {
            "surface": "futures_open_interest_intelligence",
            "symbol": spine["symbol"],
            "success": bool(semantics.get("oi_observable")),
            "open_interest_usd": semantics.get("open_interest_usd"),
            "open_interest_contracts": semantics.get("open_interest_contracts"),
            "derivatives_overview": overview,
            "derivatives_semantics": semantics,
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
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_open_interest_derivatives_disclosure(semantics)
    return _attach_derivatives_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=25,
        surface="futures_open_interest_intelligence",
        semantics=semantics,
        disclosure_key="open_interest_derivatives_disclosure",
        disclosure=disclosure,
    )


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
    ft = (overview.get("free_tier") or {}) if isinstance(overview, dict) else {}
    semantics = apply_open_interest_derivatives_semantics(overview=overview, ft=ft, spine=spine)
    body = stamp_decision_batch(
        {
            "surface": "futures_intelligence_suite",
            "symbol": spine["symbol"],
            "success": bool(semantics.get("oi_observable")),
            "futures_intelligence_suite": overview,
            "derivatives_semantics": semantics,
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
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_open_interest_derivatives_disclosure(semantics)
    return _attach_derivatives_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=25,
        surface="futures_intelligence_suite",
        semantics=semantics,
        disclosure_key="open_interest_derivatives_disclosure",
        disclosure=disclosure,
    )


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
    semantics = apply_funding_rate_derivatives_semantics(overview=overview, ft=ft, spine=spine)
    body = stamp_decision_batch(
        {
            "surface": "funding_rate_intelligence",
            "symbol": spine["symbol"],
            "success": bool(semantics.get("funding_observable")),
            "funding_rate": semantics.get("funding_rate"),
            "funding_rate_pct": semantics.get("funding_rate_pct"),
            "funding_direction": semantics.get("funding_direction"),
            "derivatives_overview": overview,
            "derivatives_semantics": semantics,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=86,
        launch_item_id=26,
        entrypoint="funding_rate_intelligence",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_funding_rate_derivatives_disclosure(semantics)
    return _attach_derivatives_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=26,
        surface="funding_rate_intelligence",
        semantics=semantics,
        disclosure_key="funding_rate_derivatives_disclosure",
        disclosure=disclosure,
    )


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
    semantics = apply_liquidation_derivatives_semantics(radar=radar, spine=spine)
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
            "success": semantics.get("answer_state") == "LIQUIDATION_SIGNAL",
            "liquidation": radar,
            "liquidation_heatmap_light": heatmap,
            "derivatives_semantics": semantics,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=88,
        launch_item_id=27,
        entrypoint="liquidation_intelligence_light",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_liquidation_derivatives_disclosure(semantics)
    return _attach_derivatives_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=27,
        surface="liquidation_intelligence",
        semantics=semantics,
        disclosure_key="liquidation_derivatives_disclosure",
        disclosure=disclosure,
    )


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
    semantics = apply_taker_leverage_derivatives_semantics(ft=ft, leverage_payload=None, spine=spine)
    body = stamp_decision_batch(
        {
            "surface": "taker_buy_sell_pressure",
            "symbol": spine["symbol"],
            "success": semantics.get("answer_state") not in {"INSUFFICIENT_EVIDENCE"},
            "taker_buy_ratio": buy,
            "taker_sell_ratio": round(1 - buy, 4),
            "taker_direction": semantics.get("taker_direction"),
            "derivatives": ft,
            "derivatives_semantics": semantics,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=89,
        launch_item_id=28,
        entrypoint="taker_buy_sell_pressure",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_taker_leverage_derivatives_disclosure(semantics)
    return _attach_derivatives_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=28,
        surface="taker_buy_sell_pressure",
        semantics=semantics,
        disclosure_key="taker_leverage_derivatives_disclosure",
        disclosure=disclosure,
    )


async def estimated_leverage_ratio(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #28 / CAP-0087 — estimated leverage ratio."""
    from bd_platform.derivatives_hub import derivatives_overview
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

    overview = await derivatives_overview(spine["symbol"])
    ft = (overview.get("free_tier") or {}) if isinstance(overview, dict) else {}
    payload = leverage_ratio_overhang_197(symbol=spine["symbol"])
    semantics = apply_taker_leverage_derivatives_semantics(ft=ft, leverage_payload=payload, spine=spine)
    body = stamp_decision_batch(
        {
            "surface": "estimated_leverage_ratio",
            "symbol": spine["symbol"],
            "success": semantics.get("answer_state") not in {"INSUFFICIENT_EVIDENCE"},
            "estimated_leverage_ratio": payload.get("leverage_ratio") or payload.get("estimated_leverage_ratio"),
            "leverage_direction": semantics.get("leverage_direction"),
            "leverage_payload": payload,
            "derivatives_semantics": semantics,
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
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_taker_leverage_derivatives_disclosure(semantics)
    return _attach_derivatives_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=28,
        surface="estimated_leverage_ratio",
        semantics=semantics,
        disclosure_key="taker_leverage_derivatives_disclosure",
        disclosure=disclosure,
    )


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
    semantics = compute_derivatives_sentiment_composite(sentiment=sentiment, deriv_overview=deriv, spine=spine)
    decision_score = semantics.get("decision_driving_composite_score")
    observable_score = semantics.get("observable_sentiment_score")
    body = stamp_decision_batch(
        {
            "surface": "derivatives_market_sentiment_composite",
            "symbol": spine["symbol"],
            "success": semantics.get("answer_state") not in {"INSUFFICIENT_EVIDENCE"},
            "sentiment": sentiment,
            "derivatives": deriv,
            "composite_score": decision_score,
            "observable_sentiment_score": observable_score,
            "derivatives_semantics": semantics,
            "material_disagreements": semantics.get("material_disagreements"),
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
    wrapped = attach_derivatives_envelope(body, spine=spine, params=p)
    disclosure = build_derivatives_composite_disclosure(semantics)
    return _attach_derivatives_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=29,
        surface="derivatives_market_sentiment_composite",
        semantics=semantics,
        disclosure_key="derivatives_composite_disclosure",
        disclosure=disclosure,
    )


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
