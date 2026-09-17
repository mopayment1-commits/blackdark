"""
Launch-57 Phase 3 — Decision Batch 1 canonical runtime spine.

Build order: #7 CAP-0035 → #8 CAP-0034 → #9 CAP-0031 → #10 CAP-0032 → #11 CAP-0033
"""

from __future__ import annotations

from typing import Any

from launch57.decision_common import (
    attach_decision_envelope,
    load_decision_spine,
    require_net_edge_if_cost_claim,
    stale_gate_body,
    stamp_decision_batch,
)

LAUNCH57_DECISION_BATCH1_CAP_IDS: frozenset[int] = frozenset({35, 34, 31, 32, 33})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    35: 7,
    34: 8,
    31: 9,
    32: 10,
    33: 11,
}

_BINDING = "launch57_phase3_decision_batch1"
_MODULE = "launch57.decision_batch1"


async def market_regime_compass(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #7 / CAP-0035 — Market Regime / Compass."""
    from onchain_tracker import build_onchain_context_safe
    from weight_aggregator import detect_market_regime, get_regime_dimension_weights

    p = dict(params or {})
    spine = await load_decision_spine(symbol, p)
    if not spine["live_eligible"]:
        return attach_decision_envelope(
            stamp_decision_batch(
                stale_gate_body(
                    capability_id=35,
                    launch_item_id=7,
                    surface="market_compass_regime_engine",
                    symbol=spine["symbol"],
                    spine=spine,
                    entrypoint="market_regime_compass",
                ),
                capability_id=35,
                launch_item_id=7,
                entrypoint="market_regime_compass",
                batch_module=_MODULE,
                binding_source=_BINDING,
            ),
            spine=spine,
        )

    change = float(spine.get("change_24h") or 0)
    ctx = await build_onchain_context_safe()
    regime = detect_market_regime(ctx, change_24h=change)
    weights = get_regime_dimension_weights(regime)

    body = stamp_decision_batch(
        {
            "surface": "market_compass_regime_engine",
            "symbol": spine["symbol"],
            "success": True,
            "market_compass": {
                "regime": regime,
                "dimension_weights": weights,
                "change_24h_pct": change,
                "compass_question": "في أي سوق أنا؟",
            },
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
            "data_spine_ref": spine["data_spine"],
        },
        capability_id=35,
        launch_item_id=7,
        entrypoint="market_regime_compass",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    from launch57.b7_market_regime_bridge import finalize_b7_cross_signal_surface

    return finalize_b7_cross_signal_surface(
        attach_decision_envelope(body, spine=spine),
        payload=p,
        spine=spine,
        fail_closed_on_mismatch=body.get("success") is not False,
    )


async def beginner_decision_mode(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #8 / CAP-0034 — Beginner Decision Mode."""
    from bd_platform.retail_intelligence_layer import build_one_clear_answer_63

    p = dict(params or {})
    spine = await load_decision_spine(symbol, p)
    if not spine["live_eligible"]:
        return attach_decision_envelope(
            stamp_decision_batch(
                stale_gate_body(
                    capability_id=34,
                    launch_item_id=8,
                    surface="beginner_decision_mode",
                    symbol=spine["symbol"],
                    spine=spine,
                    entrypoint="beginner_decision_mode",
                ),
                capability_id=34,
                launch_item_id=8,
                entrypoint="beginner_decision_mode",
                batch_module=_MODULE,
                binding_source=_BINDING,
            ),
            spine=spine,
        )

    verdict = str(p.get("verdict") or "Neutral")
    answer = build_one_clear_answer_63(
        verdict=verdict,  # type: ignore[arg-type]
        reasons=[{"point": f"Simplified read for {spine['symbol']}", "weight": 1.0, "rule_based": True}],
        risk_score=float(p.get("risk_score") or 5.0),
    )
    body = stamp_decision_batch(
        {
            "surface": "beginner_decision_mode",
            "symbol": spine["symbol"],
            "success": True,
            "beginner_mode": True,
            "clear_answer": answer,
            "ux_mode": "beginner",
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=34,
        launch_item_id=8,
        entrypoint="beginner_decision_mode",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_decision_envelope(body, spine=spine)


async def cross_signal_confirmation(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #9 / CAP-0031 — Cross-Signal Confirmation."""
    from sentiment_gate import fetch_asset_sentiment
    from signal_registry import registry_stats

    p = dict(params or {})
    spine = await load_decision_spine(symbol, p)
    if not spine["live_eligible"]:
        return attach_decision_envelope(
            stamp_decision_batch(
                stale_gate_body(
                    capability_id=31,
                    launch_item_id=9,
                    surface="cross_signal_confirmation",
                    symbol=spine["symbol"],
                    spine=spine,
                    entrypoint="cross_signal_confirmation",
                ),
                capability_id=31,
                launch_item_id=9,
                entrypoint="cross_signal_confirmation",
                batch_module=_MODULE,
                binding_source=_BINDING,
            ),
            spine=spine,
        )

    stats = registry_stats()
    sentiment = await fetch_asset_sentiment(spine["symbol"])
    change = float(spine.get("change_24h") or 0)
    bullish = sum(1 for s in (sentiment.get("signals") or []) if str(s).lower() in {"bullish", "buy", "positive"})
    bearish = sum(1 for s in (sentiment.get("signals") or []) if str(s).lower() in {"bearish", "sell", "negative"})
    confirmed = (change > 0 and bullish >= bearish) or (change < 0 and bearish >= bullish)

    body = stamp_decision_batch(
        {
            "surface": "cross_signal_confirmation",
            "symbol": spine["symbol"],
            "success": True,
            "cross_signal_confirmation": {
                "confirmed": confirmed,
                "price_change_24h": change,
                "sentiment_bias": sentiment.get("bias"),
                "registry_stats": stats,
                "price_source": "launch57.data_batch1",
            },
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=31,
        launch_item_id=9,
        entrypoint="cross_signal_confirmation",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_decision_envelope(body, spine=spine)


async def contradiction_detection(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #10 / CAP-0032 — Contradiction Detection."""
    from sentiment_gate import fetch_asset_sentiment

    p = dict(params or {})
    spine = await load_decision_spine(symbol, p)
    if not spine["live_eligible"]:
        return attach_decision_envelope(
            stamp_decision_batch(
                stale_gate_body(
                    capability_id=32,
                    launch_item_id=10,
                    surface="contradiction_detection",
                    symbol=spine["symbol"],
                    spine=spine,
                    entrypoint="contradiction_detection",
                ),
                capability_id=32,
                launch_item_id=10,
                entrypoint="contradiction_detection",
                batch_module=_MODULE,
                binding_source=_BINDING,
            ),
            spine=spine,
        )

    sentiment = await fetch_asset_sentiment(spine["symbol"])
    change = float(spine.get("change_24h") or 0)
    bias = str(sentiment.get("bias") or "neutral").lower()
    contradictions: list[dict[str, Any]] = []
    if change > 2 and bias in {"bearish", "negative"}:
        contradictions.append({"type": "price_up_sentiment_down", "severity": "moderate"})
    if change < -2 and bias in {"bullish", "positive"}:
        contradictions.append({"type": "price_down_sentiment_up", "severity": "moderate"})

    body = stamp_decision_batch(
        {
            "surface": "contradiction_detection",
            "symbol": spine["symbol"],
            "success": True,
            "contradiction_detection": {
                "contradictions": contradictions,
                "count": len(contradictions),
                "price_change_24h": change,
                "sentiment_bias": bias,
            },
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=32,
        launch_item_id=10,
        entrypoint="contradiction_detection",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_decision_envelope(body, spine=spine)


async def smart_money_actionability_score(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #11 / CAP-0033 — Smart Money Actionability Score."""
    from whale_tracker import get_latest_whale_alerts

    p = dict(params or {})
    spine = await load_decision_spine(symbol, p)
    if not spine["live_eligible"]:
        return attach_decision_envelope(
            stamp_decision_batch(
                stale_gate_body(
                    capability_id=33,
                    launch_item_id=11,
                    surface="smart_money_actionability_score",
                    symbol=spine["symbol"],
                    spine=spine,
                    entrypoint="smart_money_actionability_score",
                ),
                capability_id=33,
                launch_item_id=11,
                entrypoint="smart_money_actionability_score",
                batch_module=_MODULE,
                binding_source=_BINDING,
            ),
            spine=spine,
        )

    cost_claim = bool(p.get("cost_claim") or p.get("opportunity"))
    net_edge_gate = await require_net_edge_if_cost_claim(
        symbol=spine["symbol"],
        params=p,
        cost_claim=cost_claim,
    )
    if net_edge_gate and net_edge_gate.get("blocked"):
        body = stamp_decision_batch(
            {
                "surface": "smart_money_actionability_score",
                "symbol": spine["symbol"],
                "success": False,
                "error": net_edge_gate.get("reason"),
                "net_edge_gate": net_edge_gate,
                "actionability_score": None,
                "cost_claim_blocked": True,
                "freshness_state": spine["freshness_state"],
                "presented_as_live": False,
            },
            capability_id=33,
            launch_item_id=11,
            entrypoint="smart_money_actionability_score",
            batch_module=_MODULE,
            binding_source=_BINDING,
        )
        return attach_decision_envelope(body, spine=spine)

    alerts = await get_latest_whale_alerts(limit=10)
    score = min(100.0, max(0.0, len(alerts) * 12.5))
    body = stamp_decision_batch(
        {
            "surface": "smart_money_actionability_score",
            "symbol": spine["symbol"],
            "success": True,
            "alerts": alerts,
            "actionability_score": score,
            "net_edge_gate": net_edge_gate,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=33,
        launch_item_id=11,
        entrypoint="smart_money_actionability_score",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    from launch57.b7_market_regime_bridge import finalize_b7_cross_signal_surface

    return finalize_b7_cross_signal_surface(
        attach_decision_envelope(body, spine=spine),
        payload=p,
        spine=spine,
        fail_closed_on_mismatch=body.get("success") is not False,
    )


_DISPATCH_ENTRYPOINTS: dict[int, str] = {
    35: "market_regime_compass",
    34: "beginner_decision_mode",
    31: "cross_signal_confirmation",
    32: "contradiction_detection",
    33: "smart_money_actionability_score",
}


async def execute_launch57_decision_batch1(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in LAUNCH57_DECISION_BATCH1_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 decision batch 1")
    entrypoint = _DISPATCH_ENTRYPOINTS[capability_id]
    fn = globals()[entrypoint]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
