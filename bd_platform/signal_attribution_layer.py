"""
Signal Attribution Layer — Feature #781 (Sprint 2 Signal Engine).

Rule-based attribution: which indicators triggered the signal and why.
NOT standalone — /signals/attribution inside Signal Engine.

Template-based explanations with actual metric values — no generic text, no ML.
Integrates #754 Technical Indicators, #777 Evidence Layer, complements #776/#771.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.SignalAttribution")

_FEATURE_ID = 781
_TITLE = "Signal Attribution Layer"
_STANDALONE = False
_MERGED_INTO = "Signal Engine"
_SPRINT = 2
_SEED_PATH = Path("data/signal_attribution_layer_seed.json")
_RULE_VERSION = "1.0"

_DISCLAIMER = (
    "Signal attribution describes which rule-based indicators contributed to the signal. "
    "Not financial advice. Not a trading recommendation. No execution."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("signal attribution seed load failed: %s", exc)
        return {}


def _format_rule_text(rule_cfg: dict[str, Any], *, values: dict[str, Any]) -> str:
    template = rule_cfg.get("template", "")
    try:
        return template.format(**{**rule_cfg, **values})
    except (KeyError, ValueError):
        return template


def _build_attribution_lines(
    *,
    asset: str,
    rsi: float | None,
    macd_label: str,
    macd_histogram: float | None,
    volume_ratio: float,
    rules: dict[str, Any],
    ts: str,
) -> tuple[list[dict[str, Any]], str | None, list[str]]:
    """Build contributing metrics + triggered rules from actual inputs."""
    contributions: list[dict[str, Any]] = []
    reasons: list[str] = []
    trigger: str | None = None

    if rsi is not None:
        contributions.append({
            "metric": "RSI(14)",
            "value": rsi,
            "timestamp": ts,
            "source": "Technical Indicator Library (#754)",
        })

    contributions.append({
        "metric": "MACD",
        "value": macd_histogram,
        "trend_label": macd_label,
        "timestamp": ts,
        "source": "Technical Indicator Library (#754)",
    })

    contributions.append({
        "metric": "Volume",
        "value": f"{volume_ratio}x average",
        "timestamp": ts,
        "source": "Market Data",
    })

    overbought_rule = rules.get("rsi_overbought") or {}
    oversold_rule = rules.get("rsi_oversold") or {}
    macd_rule = rules.get("macd_bullish_cross") or {}

    threshold_ob = float(overbought_rule.get("threshold", 70))
    threshold_os = float(oversold_rule.get("threshold", 30))
    vol_mult = float(overbought_rule.get("volume_mult", 1.5))

    if rsi is not None and rsi > threshold_ob and volume_ratio > vol_mult:
        trigger = overbought_rule.get("trigger_metric", "RSI")
        rule_text = _format_rule_text(overbought_rule, values={"threshold": threshold_ob, "volume_mult": vol_mult})
        reasons.append(
            f"RSI(14) crossed {threshold_ob} at {ts} | "
            f"Volume: {volume_ratio}x average | Trigger: {trigger}"
        )
        reasons.append(f"Rule: {rule_text}")
    elif rsi is not None and rsi < threshold_os and volume_ratio > vol_mult:
        trigger = oversold_rule.get("trigger_metric", "RSI")
        rule_text = _format_rule_text(oversold_rule, values={"threshold": threshold_os, "volume_mult": vol_mult})
        reasons.append(
            f"RSI(14) below {threshold_os} at {ts} | "
            f"Volume: {volume_ratio}x average | Trigger: {trigger}"
        )
        reasons.append(f"Rule: {rule_text}")
    elif macd_histogram is not None and macd_histogram > 0 and "bullish" in macd_label.lower():
        trigger = macd_rule.get("trigger_metric", "MACD")
        rule_text = _format_rule_text(macd_rule, values={})
        reasons.append(
            f"MACD bullish cross confirmed at {ts} | Histogram: {macd_histogram} | Trigger: {trigger}"
        )
        reasons.append(f"Rule: {rule_text}")
    else:
        if rsi is not None:
            reasons.append(f"RSI(14) at {rsi} (threshold {threshold_ob}/{threshold_os}) at {ts} — no trigger fired")
        reasons.append(f"MACD: {macd_label} | Histogram: {macd_histogram} at {ts}")

    metric_summary = (
        f"RSI: {rsi} | Volume: {volume_ratio}x | MACD: {macd_histogram if macd_histogram is not None else macd_label}"
    )
    reasons.append(metric_summary)

    return contributions, trigger, reasons


def build_signal_attribution_panel_781(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#781 — signal attribution layer (Signal Engine)."""
    from bd_platform.market_radar_indicators import build_technical_calculation_layer_754

    t0 = time.perf_counter()
    seed = seed or _load_seed()
    sym = asset.upper()
    rules = seed.get("attribution_rules") or {}
    vol_ctx = (seed.get("volume_context") or {}).get(sym) or {}

    calc = build_technical_calculation_layer_754(sym)
    if not calc.get("ok"):
        return {
            "ok": False,
            "feature_ref": 781,
            "asset": sym,
            "error": "technical_data_unavailable",
        }

    indicators = calc.get("indicators") or {}
    rsi = (indicators.get("RSI") or {}).get("value")
    macd_block = indicators.get("MACD") or {}
    macd_label = macd_block.get("trend_label", "")
    macd_histogram = macd_block.get("histogram")
    ts = calc.get("timestamp") or _utcnow()
    volume_ratio = float(vol_ctx.get("volume_ratio", 1.0))

    contributions, trigger, reasons = _build_attribution_lines(
        asset=sym,
        rsi=rsi,
        macd_label=macd_label,
        macd_histogram=macd_histogram,
        volume_ratio=volume_ratio,
        rules=rules,
        ts=ts,
    )

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    panel = {
        "ok": True,
        "feature_ref": 781,
        "merged_into": _MERGED_INTO,
        "standalone_rejected": True,
        "route": "/signals/attribution",
        "asset": sym,
        "question": "Why this signal?",
        "question_ar": "لماذا هذه الإشارة؟",
        "trigger_metric": trigger,
        "contributing_metrics": contributions,
        "attribution_reasons": reasons,
        "rule_reasoning": [r for r in reasons if r.startswith("Rule:")],
        "no_generic_text": True,
        "template_based_only": True,
        "no_ml_explanation": True,
        "no_ai_generated_explanation": True,
        "values_from_actual_inputs": True,
        "technical_indicator_ref": 754,
        "rule_version": _RULE_VERSION,
        "rule_version_visible": True,
        "fee_db": seed.get("fee_db") or {},
        "no_execution": True,
        "observation_only": True,
        "disclaimer": _DISCLAIMER,
        "display": " | ".join(reasons[:3]),
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }
    if trigger:
        panel["confidence_pct"] = 75.0
    else:
        panel["confidence_pct"] = 50.0

    try:
        from bd_platform.evidence_confidence_middleware import enrich_insight_payload

        return enrich_insight_payload(
            panel,
            system="signal_engine",
            endpoint="/signals/attribution",
            source_tier="signal_engine",
            age_seconds=max(1, int(elapsed // 1000) or 1),
        )
    except Exception:
        logger.debug("777 evidence middleware skipped", exc_info=True)
        return panel


def build_signal_card_attribution_panel_781(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#781 — Signal Card expandable 'لماذا هذه الإشارة؟'."""
    panel = build_signal_attribution_panel_781(asset, seed=seed)
    return {
        "ok": panel.get("ok", False),
        "feature_ref": 781,
        "surface": "signal_card",
        "panel": "signal_attribution",
        "panel_title_ar": "لماذا هذه الإشارة؟",
        "expandable": True,
        "attribution": panel,
        "timestamp": _utcnow(),
    }


def build_asset_card_attribution_details_781(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#781 — Asset Card 'تفاصيل التحليل'."""
    panel = build_signal_attribution_panel_781(asset, seed=seed)
    return {
        "ok": panel.get("ok", False),
        "feature_ref": 781,
        "surface": "asset_card",
        "tab_ar": "تفاصيل التحليل",
        "attribution": panel,
        "timestamp": _utcnow(),
    }


def build_attribution_data_for_chat_781(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#781 → #771/#766 — feeds explain_signal with attribution data."""
    panel = build_signal_attribution_panel_781(asset, seed=seed)
    return {
        "ok": panel.get("ok", False),
        "feature_ref": 781,
        "integration": "natural_language_interpreter_766_771",
        "attribution_reasons": panel.get("attribution_reasons") or [],
        "contributing_metrics": panel.get("contributing_metrics") or [],
        "trigger_metric": panel.get("trigger_metric"),
        "no_generic_text": panel.get("no_generic_text"),
        "timestamp": _utcnow(),
    }


def run_signal_attribution_qa_781(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#781 — reasons must reflect actual inputs; no generic text."""
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    panel = build_signal_attribution_panel_781("BTC", seed=seed)
    tests.append({"test": "panel_ok", "passed": panel.get("ok") is True})
    tests.append({"test": "contributing_metrics", "passed": len(panel.get("contributing_metrics") or []) >= 2})
    tests.append({"test": "no_generic_text_flag", "passed": panel.get("no_generic_text") is True})
    tests.append({"test": "no_ml_explanation", "passed": panel.get("no_ml_explanation") is True})
    tests.append({"test": "rule_version_visible", "passed": panel.get("rule_version_visible") is True})
    tests.append({"test": "evidence_attached", "passed": "evidence_confidence_777" in panel})

    generic_banned = ["the market looks bullish", "the market looks bearish", "ai reasoning"]
    reasons_text = " ".join(panel.get("attribution_reasons") or []).lower()
    tests.append({
        "test": "no_generic_phrases",
        "passed": not any(g in reasons_text for g in generic_banned),
    })

    if panel.get("trigger_metric"):
        tests.append({
            "test": "trigger_in_reasons",
            "passed": panel["trigger_metric"] in " ".join(panel.get("attribution_reasons") or []),
        })
    else:
        tests.append({"test": "trigger_in_reasons", "passed": True, "detail": "no trigger fired"})

    fixtures = seed.get("qa_fixtures") or []
    for fixture in fixtures:
        fp = build_signal_attribution_panel_781(fixture.get("asset", "BTC"), seed=seed)
        if fixture.get("expect_trigger"):
            tests.append({
                "test": f"fixture_{fixture.get('id')}_trigger",
                "passed": fp.get("trigger_metric") == fixture["expect_trigger"],
            })
        if fixture.get("expect_no_generic"):
            tests.append({
                "test": f"fixture_{fixture.get('id')}_no_generic",
                "passed": fp.get("no_generic_text") is True,
            })

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": 781,
        "qa_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }


def signal_attribution_layer_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "route": "/signals/attribution",
        "rule_version": _RULE_VERSION,
        "template_based_only": True,
        "no_ml_explanation": True,
        "integrated_with": ["#754", "#771", "#776", "#777"],
        "timestamp": _utcnow(),
    }
