"""
Launch-57 Phase 4 — Smart Money Batch 3 (Instant risk surfaces).

Build order: #55 CAP-0238 → #56 CAP-0297 → #57 CAP-0916
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from launch57.smart_money_common import (
    attach_smart_money_envelope,
    cautious_exchange_footer,
    load_decision_spine,
    mini_aml_footer,
    stale_gate_body,
    stamp_decision_batch,
)
from launch57.trust_adaptive_common import (
    apply_exchange_transparency_risk_guard,
    apply_manipulation_pattern_qualification_filter,
    apply_suspicious_activity_evidence_filter,
    attach_adaptive_disclosure,
    build_exchange_transparency_disclosure,
    build_level1_decision_disclosure,
    build_manipulation_alert_disclosure,
    build_suspicious_activity_disclosure,
)

LAUNCH57_SMART_MONEY_BATCH3_CAP_IDS: frozenset[int] = frozenset({238, 297, 916})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    238: 55,
    297: 56,
    916: 57,
}

_BINDING = "launch57_phase4_smart_money_batch3"
_MODULE = "launch57.smart_money_batch3"


def _stamp_risk_flag_timestamps(flags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preserve B12 temporal envelope compatibility for decision-driving risk flags."""
    now = datetime.now(UTC).isoformat()
    stamped: list[dict[str, Any]] = []
    for flag in flags:
        row = dict(flag)
        if not row.get("last_update_time"):
            row["last_update_time"] = now
        stamped.append(row)
    return stamped


def _attach_live_adaptive(
    wrapped: dict[str, Any],
    *,
    p: dict[str, Any],
    launch_item_id: int,
    surface: str,
    answer_state: str,
    disclosure_key: str,
    disclosure: dict[str, Any],
    uncertainty: str = "qualified",
) -> dict[str, Any]:
    wrapped[disclosure_key] = disclosure
    level1 = build_level1_decision_disclosure(
        p,
        launch_item_id=launch_item_id,
        surface=surface,
        answer_state=answer_state,
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
        return attach_smart_money_envelope(body, spine=spine, params=params), None
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

    sample_text = str(p.get("text") or f"{spine['symbol']} market update with normal volume")
    assessment = assess_sentiment_item(
        asset=spine["symbol"],
        source=str(p.get("source") or "twitter"),
        raw_text=sample_text,
    )
    phrase_hits = detect_pump_dump_phrases(sample_text)
    alerts = await get_latest_whale_alerts(limit=int(p.get("limit") or 15))
    qualified = apply_manipulation_pattern_qualification_filter(
        assessment=assessment,
        phrase_hits=phrase_hits,
        whale_alerts=list(alerts or []),
    )
    alert_fired = bool(qualified.get("manipulation_alert_fired"))

    body = stamp_decision_batch(
        {
            "surface": "pump_dump_detection",
            "symbol": spine["symbol"],
            "success": alert_fired,
            "pump_dump_detection": {
                "sentiment_assessment": {
                    "accepted": assessment.accepted,
                    "rejected_reason": assessment.rejected_reason,
                    "manipulation_flags": assessment.manipulation_flags,
                    "pump_phrases": phrase_hits,
                },
                "whale_alerts_observable": alerts,
                "manipulation_qualification": qualified,
                "pattern_alert_fired": alert_fired,
                "pattern_evidence": qualified.get("pattern_evidence"),
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
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_manipulation_alert_disclosure(qualified, assessment=assessment)
    answer_state = "MANIPULATION_ALERT" if alert_fired else "NO_QUALIFYING_PATTERN"
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=55,
        surface="pump_dump_detection",
        answer_state=answer_state,
        disclosure_key="manipulation_alert_disclosure",
        disclosure=disclosure,
        uncertainty="qualified" if not alert_fired else "standard",
    )


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
    filtered = apply_suspicious_activity_evidence_filter(raw.get("flags") or [])
    decision_flags = _stamp_risk_flag_timestamps(list(filtered.get("decision_driving_flags") or []))
    body = stamp_decision_batch(
        {
            "surface": "fraud_suspicious_activity_intelligence",
            "symbol": spine["symbol"],
            "success": bool(filtered.get("suspicion_eligible")),
            "suspicious_activity_flags": decision_flags,
            "suspicious_activity_observable": filtered.get("observable_only_flags"),
            "suspicious_activity_filter": filtered,
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
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_suspicious_activity_disclosure(filtered)
    answer_state = "SUSPICION_FLAGGED" if filtered.get("suspicion_eligible") else "INSUFFICIENT_EVIDENCE"
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=56,
        surface="fraud_suspicious_activity_intelligence",
        answer_state=answer_state,
        disclosure_key="suspicious_activity_disclosure",
        disclosure=disclosure,
        uncertainty="qualified" if filtered.get("observable_only_flags") else "standard",
    )


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
    guarded = apply_exchange_transparency_risk_guard(health, spine=spine)
    indicators = {
        **dict(guarded.get("risk_indicators") or {}),
        "cautious_disclaimer": cautious_exchange_footer(),
        "solvency_certificate_claim": guarded.get("solvency_certificate_claim"),
        "reserve_guarantee_claim": guarded.get("reserve_guarantee_claim"),
        "exchange_safety_certification": guarded.get("exchange_safety_certification"),
        "indicators_only": guarded.get("indicators_only"),
        "decision_driving_solvency_assurance": guarded.get("decision_driving_solvency_assurance"),
    }
    body = stamp_decision_batch(
        {
            "surface": "exchange_transparency_risk_indicators",
            "symbol": spine["symbol"],
            "success": bool(health),
            "exchange_risk_indicators": indicators,
            "exchange_transparency_guard": guarded,
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
    wrapped = attach_smart_money_envelope(body, spine=spine, params=p)
    disclosure = build_exchange_transparency_disclosure(guarded, spine=spine)
    answer_state = "RISK_INDICATORS_ONLY"
    return _attach_live_adaptive(
        wrapped,
        p=p,
        launch_item_id=57,
        surface="exchange_transparency_risk_indicators",
        answer_state=answer_state,
        disclosure_key="exchange_transparency_disclosure",
        disclosure=disclosure,
        uncertainty="qualified" if guarded.get("conflicting_evidence_visible") else "standard",
    )


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
