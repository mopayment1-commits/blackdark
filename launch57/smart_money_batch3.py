"""
Launch-57 Phase 4 — Smart Money Batch 3 (Instant risk surfaces).

Build order: #55 CAP-0238 → #56 CAP-0297 → #57 CAP-0916
"""

from __future__ import annotations

from typing import Any

from launch57.smart_money_common import (
    attach_smart_money_envelope,
    cautious_exchange_footer,
    load_decision_spine,
    mini_aml_footer,
    stale_gate_body,
    stamp_decision_batch,
)

LAUNCH57_SMART_MONEY_BATCH3_CAP_IDS: frozenset[int] = frozenset({238, 297, 916})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    238: 55,
    297: 56,
    916: 57,
}

_BINDING = "launch57_phase4_smart_money_batch3"
_MODULE = "launch57.smart_money_batch3"


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
        return attach_smart_money_envelope(body, spine=spine), None
    return None, spine


async def pump_dump_manipulation_alerts(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #55 / CAP-0238 — pump & dump / manipulation pattern alerts."""
    from sentiment_manipulation_guard import assess_sentiment_item, detect_pump_dump_phrases
    from whale_tracker import get_latest_whale_alerts

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=238,
        launch_item_id=55,
        surface="pump_dump_detection",
        entrypoint="pump_dump_manipulation_alerts",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    sample_text = str(p.get("text") or f"{spine['symbol']} guaranteed 100x pump moon shot gem alert")
    assessment = assess_sentiment_item(
        asset=spine["symbol"],
        source=str(p.get("source") or "twitter"),
        raw_text=sample_text,
    )
    phrase_hits = detect_pump_dump_phrases(sample_text)
    alerts = await get_latest_whale_alerts(limit=int(p.get("limit") or 15))
    manipulation_rows = [
        a for a in (alerts or []) if float((a.get("manipulation_score") or 0)) > 0 or "manipulation" in str(a).lower()
    ]

    body = stamp_decision_batch(
        {
            "surface": "pump_dump_detection",
            "symbol": spine["symbol"],
            "success": bool(phrase_hits or manipulation_rows or not assessment.accepted),
            "pump_dump_detection": {
                "sentiment_assessment": {
                    "accepted": assessment.accepted,
                    "rejected_reason": assessment.rejected_reason,
                    "manipulation_flags": assessment.manipulation_flags,
                    "pump_phrases": phrase_hits,
                },
                "whale_manipulation_alerts": manipulation_rows[:10],
                "pattern_alert_fired": bool(phrase_hits) or not assessment.accepted,
            },
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=238,
        launch_item_id=55,
        entrypoint="pump_dump_manipulation_alerts",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_smart_money_envelope(body, spine=spine)


async def suspicious_activity_flags(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #56 / CAP-0297 — suspicious activity flags (mini AML, not full platform)."""
    from bd_platform.derivatives_onchain_intelligence_layer import fraud_suspicious_activity_297

    p = dict(params or {})
    blocked, spine = await _gated(
        capability_id=297,
        launch_item_id=56,
        surface="fraud_suspicious_activity_intelligence",
        entrypoint="suspicious_activity_flags",
        symbol=symbol,
        params=p,
    )
    if blocked:
        return blocked

    raw = fraud_suspicious_activity_297(seed=p.get("seed"))
    flags = raw.get("flags") or []
    body = stamp_decision_batch(
        {
            "surface": "fraud_suspicious_activity_intelligence",
            "symbol": spine["symbol"],
            "success": bool(flags),
            "suspicious_activity_flags": flags,
            "mini_aml_scope": mini_aml_footer(),
            "full_aml_platform": False,
            "sar_auto_filing": False,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=297,
        launch_item_id=56,
        entrypoint="suspicious_activity_flags",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_smart_money_envelope(body, spine=spine)


async def exchange_transparency_risk_indicators(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #57 / CAP-0916 — cautious exchange transparency / risk indicators only."""
    from bd_platform.institutional_b2b_layer import build_exchange_health_with_counterparty_92

    p = dict(params or {})
    exchange = str(p.get("exchange") or "binance")
    blocked, spine = await _gated(
        capability_id=916,
        launch_item_id=57,
        surface="exchange_transparency_risk_indicators",
        entrypoint="exchange_transparency_risk_indicators",
        symbol=symbol,
        params={**p, "exchange": exchange},
    )
    if blocked:
        return blocked

    health = build_exchange_health_with_counterparty_92(
        exchange=exchange,
        withdrawal_latency_hours=float(p.get("withdrawal_latency_hours") or 12.0),
        seed=p.get("seed"),
    )
    indicators = {
        "exchange": exchange,
        "withdrawal_latency_status": (health.get("counterparty_risk") or {}).get("withdrawal_latency_status"),
        "abnormal_flow_pattern": (health.get("counterparty_risk") or {}).get("abnormal_flow_pattern"),
        "alert_trigger": health.get("alert_trigger"),
        "cautious_disclaimer": cautious_exchange_footer(),
        "solvency_certificate_claim": "FORBIDDEN",
        "reserve_guarantee_claim": "FORBIDDEN",
        "indicators_only": True,
    }
    body = stamp_decision_batch(
        {
            "surface": "exchange_transparency_risk_indicators",
            "symbol": spine["symbol"],
            "success": bool(health),
            "exchange_risk_indicators": indicators,
            "raw_health_preview": {
                k: health.get(k)
                for k in ("exchange", "health_score", "counterparty_risk", "alert_trigger")
                if k in health
            },
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=916,
        launch_item_id=57,
        entrypoint="exchange_transparency_risk_indicators",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_smart_money_envelope(body, spine=spine)


_DISPATCH: dict[int, str] = {
    238: "pump_dump_manipulation_alerts",
    297: "suspicious_activity_flags",
    916: "exchange_transparency_risk_indicators",
}


async def execute_launch57_smart_money_batch3(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in LAUNCH57_SMART_MONEY_BATCH3_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 smart money batch 3")
    fn = globals()[_DISPATCH[capability_id]]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
