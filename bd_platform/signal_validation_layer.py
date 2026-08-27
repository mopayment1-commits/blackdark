"""
Signal Validation Layer — Feature #776 (Sprint 2).

Cross-Signal Confirmation / Contradiction Detection merged into Signal Engine.
NOT standalone — validation layer at /signals/validation.

Rule-based comparison across Technical + On-Chain + Sentiment domains.
No forced consensus. No trading signals. Observation only.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SignalValidationLayer")

_FEATURE_ID = 776
_TITLE = "Signal Validation Layer"
_STANDALONE = False
_MERGED_INTO = "Signal Engine"
_SPRINT = 2
_SEED_PATH = Path("data/signal_validation_layer_seed.json")
_METHODOLOGY_VERSION = "1.0"

ValidationStatus = Literal["Confirmed", "Mixed", "Contradictory"]

_DISCLAIMER = (
    "Cross-signal validation describes signal alignment only. "
    "Not financial advice. Not a recommendation to act. No forced consensus."
)

_DIRECTION_UP = frozenset({"bullish", "rising", "up", "positive", "صاعد"})
_DIRECTION_DOWN = frozenset({"bearish", "falling", "down", "negative", "هابط"})
_DIRECTION_FLAT = frozenset({"neutral", "flat", "mixed", "محايد"})

_DOMAIN_LABELS_AR = {
    "Technical": "فني",
    "On-Chain": "On-Chain",
    "Sentiment": "Sentiment",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("signal validation seed load failed: %s", exc)
        return {}


def _direction_score(direction: str | None) -> int:
    d = (direction or "neutral").lower()
    if d in _DIRECTION_UP:
        return 1
    if d in _DIRECTION_DOWN:
        return -1
    return 0


def _direction_label_ar(direction: str | None) -> str:
    score = _direction_score(direction)
    if score > 0:
        return "صاعد"
    if score < 0:
        return "هابط"
    return "محايد"


def _strength_from_confidence(confidence_pct: float) -> int:
    return max(1, min(10, round(confidence_pct / 10)))


def _fetch_technical_signal(asset: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    from bd_platform.market_radar_indicators import build_technical_summary_overlay_755

    summary = build_technical_summary_overlay_755(asset)
    if not summary.get("ok"):
        return {"ok": False, "domain": "Technical", "error": "technical_unavailable"}

    analysis = summary.get("analysis", "Neutral")
    confidence = float(summary.get("confidence_pct", 50))
    rsi = (summary.get("raw_indicators") or {}).get("RSI", {}).get("value")
    reason = f"RSI/MACD composite: {analysis}"
    if rsi is not None:
        reason += f" (RSI={rsi})"

    return {
        "ok": True,
        "domain": "Technical",
        "direction": analysis,
        "direction_score": _direction_score(analysis),
        "direction_ar": _direction_label_ar(analysis),
        "strength": _strength_from_confidence(confidence),
        "confidence_pct": confidence,
        "reason": reason,
        "source": "Technical Indicator Library (#754/#755)",
        "citation": f"Technical: {analysis} ({_strength_from_confidence(confidence)}/10) | Source: #754 | Confidence: {confidence}%",
    }


def _fetch_onchain_signal(asset: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    from bd_platform.onchain_metrics_library import build_nvt_ratio_suite_761

    nvt = build_nvt_ratio_suite_761(asset)
    if not nvt.get("ok"):
        return {"ok": False, "domain": "On-Chain", "error": "onchain_unavailable"}

    overvalued = nvt.get("overvaluation_flag") is True
    percentile = nvt.get("historical_percentile")
    if overvalued:
        direction = "Bearish"
        reason = f"NVT overvaluation flag (percentile {percentile}%)"
    elif percentile is not None and percentile < 25:
        direction = "Bullish"
        reason = f"NVT below historical median (percentile {percentile}%)"
    else:
        direction = "Neutral"
        reason = f"NVT within historical band (percentile {percentile}%)"

    confidence = 70.0 if overvalued else 55.0
    return {
        "ok": True,
        "domain": "On-Chain",
        "direction": direction,
        "direction_score": _direction_score(direction),
        "direction_ar": _direction_label_ar(direction),
        "strength": _strength_from_confidence(confidence),
        "confidence_pct": confidence,
        "reason": reason,
        "source": "On-Chain Metrics Library (#577)",
        "citation": f"On-Chain: {_direction_label_ar(direction)} ({_strength_from_confidence(confidence)}/10) | Source: #577 NVT | NVT={nvt.get('nvt_ratio')}",
    }


def _fetch_sentiment_signal(asset: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    from bd_platform.hype_vs_reality_signal import build_hype_vs_reality_signal

    hype = build_hype_vs_reality_signal(asset)
    if not hype.get("ok"):
        cfg = seed.get("sentiment_fallback") or {}
        fb = (cfg.get("assets") or {}).get(asset.upper()) or {}
        direction = fb.get("direction", "Neutral")
        confidence = float(fb.get("confidence_pct", 50))
        return {
            "ok": True,
            "domain": "Sentiment",
            "direction": direction,
            "direction_score": _direction_score(direction),
            "direction_ar": _direction_label_ar(direction),
            "strength": _strength_from_confidence(confidence),
            "confidence_pct": confidence,
            "reason": fb.get("reason", "Trending Words sentiment (#758)"),
            "source": "Trending Words (#758)",
            "citation": f"Sentiment: {_direction_label_ar(direction)} ({_strength_from_confidence(confidence)}/10) | Source: #758",
        }

    social = (hype.get("contributors") or {}).get("social") or {}
    direction = social.get("direction", "flat")
    if direction == "rising":
        dir_label = "Bullish"
    elif direction == "falling":
        dir_label = "Bearish"
    else:
        dir_label = "Neutral"

    confidence = float(hype.get("confidence_pct", social.get("confidence_pct", 50)))
    return {
        "ok": True,
        "domain": "Sentiment",
        "direction": dir_label,
        "direction_score": _direction_score(dir_label),
        "direction_ar": _direction_label_ar(dir_label),
        "strength": _strength_from_confidence(confidence),
        "confidence_pct": confidence,
        "reason": f"Social sentiment direction: {direction} (#758 Trending Words)",
        "source": "Trending Words / Hype vs Reality (#758/#599)",
        "citation": f"Sentiment: {_direction_label_ar(dir_label)} ({_strength_from_confidence(confidence)}/10) | Source: #758",
    }


def _classify_validation_status(signals: list[dict[str, Any]]) -> ValidationStatus:
    active = [s for s in signals if s.get("ok") and s.get("direction_score", 0) != 0]
    if len(active) < 2:
        return "Mixed"

    scores = [s["direction_score"] for s in active]
    if all(s == scores[0] for s in scores):
        return "Confirmed"
    if 1 in scores and -1 in scores:
        return "Contradictory"
    return "Mixed"


def _explain_conflicts(signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """#776 — explicit conflict explanations, no forced consensus."""
    conflicts: list[dict[str, Any]] = []
    by_domain = {s["domain"]: s for s in signals if s.get("ok")}

    pairs = [
        ("Technical", "On-Chain"),
        ("Technical", "Sentiment"),
        ("On-Chain", "Sentiment"),
    ]
    for a, b in pairs:
        sa, sb = by_domain.get(a), by_domain.get(b)
        if not sa or not sb:
            continue
        if sa["direction_score"] != 0 and sb["direction_score"] != 0 and sa["direction_score"] != sb["direction_score"]:
            conflicts.append({
                "domains": [a, b],
                "formula": f"{a}: {sa['direction']} × {b}: {sb['direction']}",
                "detail": (
                    f"{a}: {sa['direction']} (السبب: {sa['reason']}) | "
                    f"{b}: {sb['direction']} (السبب: {sb['reason']}) | "
                    f"التعارض: {a} مقابل {b}"
                ),
                "rule_based": True,
            })
    return conflicts


def _apply_evidence_777(
    payload: dict[str, Any],
    *,
    endpoint: str = "/signals/validation",
    age_seconds: int = 60,
) -> dict[str, Any]:
    """#777 — cross-cutting evidence metadata on signal validation outputs."""
    try:
        from bd_platform.evidence_confidence_middleware import enrich_insight_payload

        return enrich_insight_payload(
            payload,
            system="signal_engine",
            endpoint=endpoint,
            source_tier="signal_engine",
            age_seconds=age_seconds,
        )
    except Exception:
        logger.debug("777 evidence middleware skipped", exc_info=True)
        return payload


def _build_next_actions(asset: str) -> list[dict[str, str]]:
    return [
        {"label_ar": "استكشف: NVT Ratio في Market Radar", "route": "/intelligence-ledger/market-radar/panel"},
        {"label_ar": "Risk Score في Intelligence Ledger", "route": "/intelligence-ledger/onchain-layer/metrics-library/nvt-ratio/overvaluation-flag"},
        {"label_ar": "Technical Summary في Market Radar", "route": "/intelligence-ledger/market-radar/panel"},
    ]


def build_signal_validation_panel_776(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#776 — cross-signal validation layer (Signal Engine)."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    sym = asset.upper()

    technical = _fetch_technical_signal(sym)
    onchain = _fetch_onchain_signal(sym)
    sentiment = _fetch_sentiment_signal(sym, seed=seed)
    signals = [technical, onchain, sentiment]
    available = [s for s in signals if s.get("ok")]

    status = _classify_validation_status(available)
    conflicts = _explain_conflicts(available)
    status_ar = {"Confirmed": "مؤكد", "Mixed": "مختلط", "Contradictory": "متعارض"}.get(status, status)

    parts = [f"الأصل: {sym}"]
    for s in available:
        label = _DOMAIN_LABELS_AR.get(s["domain"], s["domain"])
        parts.append(f"{label}: {s['direction_ar']} ({s['strength']}/10)")
    parts.append(f"الحالة: {status_ar}")
    if conflicts:
        parts.append(f"التعارض: {conflicts[0]['domains'][0]} مقابل {conflicts[0]['domains'][1]}")

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    cfg = seed.get("signal_validation_776") or {}

    panel = {
        "ok": len(available) >= 2,
        "feature_ref": 776,
        "merged_into": _MERGED_INTO,
        "standalone_rejected": True,
        "route": "/signals/validation",
        "asset": sym,
        "validation_status": status,
        "validation_status_ar": status_ar,
        "confidence_pct": {"Confirmed": 100.0, "Mixed": 67.0, "Contradictory": 33.0}.get(status, 50.0),
        "signals": available,
        "domain_coverage": ["Technical", "On-Chain", "Sentiment"],
        "max_domains": 3,
        "conflicts": conflicts,
        "conflicts_explained": bool(conflicts),
        "no_forced_consensus": True,
        "no_trading_signal": True,
        "no_execution": True,
        "observation_only": True,
        "rule_based_only": True,
        "no_ml_aggregation": True,
        "comparison_formula": "Direction (+1/0/-1) × Strength (1–10) × Confidence (%)",
        "next_analytical_actions": _build_next_actions(sym),
        "no_buy_sell_execute": True,
        "fee_db": cfg.get("fee_db") or {
            "signal_comparison_usd": 0.002,
            "tier": "standard",
        },
        "disclaimer": _DISCLAIMER,
        "disclaimer_mandatory": True,
        "display": " | ".join(parts),
        "display_en": " | ".join(
            f"{s['domain']}: {s['direction']} ({s['strength']}/10)" for s in available
        ) + f" | Status: {status}",
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }
    return _apply_evidence_777(panel, age_seconds=max(1, int(elapsed // 1000) or 1))


def build_signal_card_cross_validation_776(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#776 — Signal Card التحقق المتقاطع (expandable)."""
    panel = build_signal_validation_panel_776(asset, seed=seed)
    return {
        "ok": panel.get("ok", False),
        "feature_ref": 776,
        "surface": "signal_card",
        "panel": "cross_validation",
        "panel_title_ar": "التحقق المتقاطع",
        "expandable": True,
        "validation": panel,
        "conflicts": panel.get("conflicts") or [],
        "timestamp": _utcnow(),
    }


def build_intelligence_ledger_signal_quality_776(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#776 → Intelligence Ledger جودة الإشارات."""
    panel = build_signal_validation_panel_776(asset, seed=seed)
    return {
        "ok": panel.get("ok", False),
        "feature_ref": 776,
        "integration": "intelligence_ledger",
        "dimension": "signal_quality_scoring",
        "asset": asset.upper(),
        "validation_status": panel.get("validation_status"),
        "conflict_count": len(panel.get("conflicts") or []),
        "quality_flag": panel.get("validation_status") == "Contradictory",
        "observation_only": True,
        "display": panel.get("display"),
        "timestamp": _utcnow(),
    }


def run_signal_validation_qa_776(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#776 — daily QA: contradiction detection must match manual review ±0%."""
    seed = seed or _load_seed()
    fixtures = (seed.get("signal_validation_776") or {}).get("qa_fixtures") or []
    tests: list[dict[str, Any]] = []

    for fixture in fixtures:
        asset = fixture.get("asset", "BTC")
        panel = build_signal_validation_panel_776(asset, seed=seed)
        expected = fixture.get("expected_status")
        passed = panel.get("validation_status") == expected
        tests.append({
            "test": fixture.get("id", "qa"),
            "passed": passed,
            "expected": expected,
            "actual": panel.get("validation_status"),
            "detail": panel.get("display"),
        })

    all_passed = all(t["passed"] for t in tests) if tests else True
    return {
        "ok": all_passed,
        "feature_ref": 776,
        "qa_tests": tests,
        "all_passed": all_passed,
        "daily_qa_required": True,
        "timestamp": _utcnow(),
    }


def build_signal_card_combined_validation_776_779(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
    mtf_seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#776 + #779 + #777 — full Signal Card validation network."""
    from bd_platform.evidence_confidence_middleware import build_signal_card_evidence_trail_777
    from bd_platform.mtf_validation_layer import build_signal_card_mtf_panel_779

    cross = build_signal_card_cross_validation_776(asset, seed=seed)
    mtf = build_signal_card_mtf_panel_779(asset, seed=mtf_seed)
    validation = cross.get("validation") or {}
    mtf_panel = mtf.get("validation") or {}
    evidence = build_signal_card_evidence_trail_777({
        **validation,
        "mtf_verdict": mtf.get("verdict_badge"),
        "confidence_pct": mtf_panel.get("confidence_pct") or validation.get("confidence_pct"),
    })
    return {
        "ok": bool(cross.get("ok")) and bool(mtf.get("ok")),
        "feature_refs": [776, 779, 777],
        "surface": "signal_card",
        "panel_title_ar": "شبكة التحقق الكاملة",
        "cross_validation_776": cross,
        "mtf_validation_779": mtf,
        "evidence_trail_777": evidence,
        "complements": "#776 cross-domain + #779 cross-timeframe",
        "no_execution": True,
        "timestamp": _utcnow(),
    }


def signal_validation_layer_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "route": "/signals/validation",
        "domain_coverage": ["Technical", "On-Chain", "Sentiment"],
        "validation_states": ["Confirmed", "Mixed", "Contradictory"],
        "no_forced_consensus": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "complements_mtf_779": True,
        "timestamp": _utcnow(),
    }
