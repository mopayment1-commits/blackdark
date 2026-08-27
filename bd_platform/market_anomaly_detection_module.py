"""
Market Anomaly Detection Module — Feature #583 (Sprint 2 Intelligence Layer).

Renamed from "Pump & Dump Detection".
Gated multi-signal classifier — statistical risk flags only.
No accusation language. Multi-signal evidence mandatory.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.MarketAnomalyDetection")

_FEATURE_ID = 583
_LEGAL_NAME = "Market Anomaly Detection Module"
_RENAMED_FROM = "Pump & Dump Detection"
_STANDALONE = False
_LAYER = "Intelligence Layer"
_SPRINT = 2
_SEED_PATH = Path("data/market_anomaly_detection_seed.json")
_METHODOLOGY_VERSION = "1.0"
_MIN_SIGNAL_COVERAGE = 3

_DISCLAIMER = (
    "Statistical anomaly detection — multiple signal evidence required. "
    "Risk flags describe observed anomalies, not confirmed manipulation. "
    "Not investment advice. Not trade signals."
)

_BANNED_TERMS = (
    "pump and dump",
    "this is a scam",
    "confirmed manipulation",
    "pump detected",
    "dump detected",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "config": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("market anomaly detection seed load failed: %s", exc)
        return {"assets": {}, "config": {}}


def _evaluate_signals(asset_data: dict[str, Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    """Evaluate individual anomaly signals — each with evidence."""
    signals: list[dict[str, Any]] = []
    thresholds = cfg.get("thresholds") or {}

    price_spike = float(asset_data.get("price_spike_pct", 0))
    if price_spike >= float(thresholds.get("price_spike_pct", 15)):
        signals.append({
            "signal": "price_spike",
            "value": price_spike,
            "threshold": thresholds.get("price_spike_pct"),
            "evidence": asset_data.get("price_evidence"),
            "statistical_only": True,
        })

    volume_spike = float(asset_data.get("volume_spike_pct", 0))
    if volume_spike >= float(thresholds.get("volume_spike_pct", 200)):
        signals.append({
            "signal": "volume_spike",
            "value": volume_spike,
            "threshold": thresholds.get("volume_spike_pct"),
            "evidence": asset_data.get("volume_evidence"),
            "statistical_only": True,
        })

    liquidity_drop = float(asset_data.get("liquidity_drop_pct", 0))
    if liquidity_drop >= float(thresholds.get("liquidity_drop_pct", 30)):
        signals.append({
            "signal": "liquidity_drop",
            "value": liquidity_drop,
            "threshold": thresholds.get("liquidity_drop_pct"),
            "evidence": asset_data.get("liquidity_evidence"),
            "statistical_only": True,
        })

    holder_concentration = float(asset_data.get("holder_concentration_pct", 0))
    if holder_concentration >= float(thresholds.get("holder_concentration_pct", 70)):
        signals.append({
            "signal": "holder_concentration",
            "value": holder_concentration,
            "threshold": thresholds.get("holder_concentration_pct"),
            "evidence": asset_data.get("holder_evidence"),
            "statistical_only": True,
        })

    dex_flow_anomaly = float(asset_data.get("dex_flow_zscore", 0))
    if abs(dex_flow_anomaly) >= float(thresholds.get("dex_flow_zscore", 3.0)):
        signals.append({
            "signal": "dex_flow_anomaly",
            "value": dex_flow_anomaly,
            "threshold": thresholds.get("dex_flow_zscore"),
            "evidence": asset_data.get("dex_evidence"),
            "statistical_only": True,
        })

    derivatives_spike = float(asset_data.get("derivatives_oi_spike_pct", 0))
    if derivatives_spike >= float(thresholds.get("derivatives_oi_spike_pct", 50)):
        signals.append({
            "signal": "derivatives_positioning",
            "value": derivatives_spike,
            "threshold": thresholds.get("derivatives_oi_spike_pct"),
            "evidence": asset_data.get("derivatives_evidence"),
            "statistical_only": True,
        })

    return signals


def detect_market_anomalies(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#583 — gated multi-signal anomaly detection."""
    seed = seed or _load_seed()
    cfg = seed.get("config") or {}
    asset_data = (seed.get("assets") or {}).get(asset.upper())
    if not asset_data:
        return {"ok": False, "asset": asset, "error": "asset_not_found"}

    signals = _evaluate_signals(asset_data, cfg)
    coverage = len(signals)
    min_coverage = int(cfg.get("min_signal_coverage", _MIN_SIGNAL_COVERAGE))
    coverage_gate_passed = coverage >= min_coverage

    risk_flag = None
    if coverage_gate_passed:
        signal_names = [s["signal"] for s in signals]
        risk_flag = {
            "flag_type": "statistical_anomaly",
            "anomaly_count": coverage,
            "signals": signal_names,
            "display": f"Multiple anomalies detected: {', '.join(signal_names)}",
            "statistical_only": True,
            "no_accusation_language": True,
            "no_label_without_multi_signal": True,
        }

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "asset": asset.upper(),
        "signals_detected": signals,
        "signal_count": coverage,
        "min_coverage_gate": min_coverage,
        "coverage_gate_passed": coverage_gate_passed,
        "risk_flag": risk_flag,
        "no_label_without_multi_signal_evidence": coverage_gate_passed or coverage == 0,
        "evidence": [s.get("evidence") for s in signals if s.get("evidence")],
        "rule_based": True,
        "display": (
            risk_flag["display"] if risk_flag
            else f"{asset.upper()}: {coverage}/{min_coverage} signals — below coverage gate"
        ),
        "timestamp": _utcnow(),
    }


def build_market_anomaly_panel(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    result = detect_market_anomalies(asset, seed=seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    if not result.get("ok"):
        return result

    return {
        **result,
        "title": _LEGAL_NAME,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
    }


def market_anomaly_detection_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "asset_count": len(seed.get("assets") or {}),
        "min_signal_coverage": (seed.get("config") or {}).get("min_signal_coverage", _MIN_SIGNAL_COVERAGE),
        "acceptance_criteria": {
            "minimum_coverage_gate": True,
            "no_label_without_multi_signal_evidence": True,
            "statistical_risk_flags_only": True,
            "no_accusation_language": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    flagged = detect_market_anomalies("ALT", seed=seed)
    checks.append({"id": "coverage_gate", "passed": flagged.get("coverage_gate_passed") is True, "detail": "583"})
    checks.append({
        "id": "multi_signal_evidence",
        "passed": flagged.get("risk_flag") is not None
        and len(flagged.get("signals_detected") or []) >= _MIN_SIGNAL_COVERAGE,
        "detail": "evidence",
    })
    checks.append({
        "id": "statistical_only",
        "passed": (flagged.get("risk_flag") or {}).get("statistical_only") is True,
        "detail": "no accusation",
    })
    checks.append({
        "id": "no_accusation_language",
        "passed": "scam" not in (flagged.get("display") or "").lower(),
        "detail": "rename",
    })

    below = detect_market_anomalies("BTC", seed=seed)
    checks.append({
        "id": "below_gate_no_label",
        "passed": below.get("risk_flag") is None,
        "detail": "gate",
    })

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
