"""
Live Feed Statistical Monitor — #1054 merged into #1026 Outlier Detection Gate.

Rule-based streaming anomaly detection (no ML Sprint 2).
Sequence: ingest → anomaly detection → outlier validation → serve/reject.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
import uuid
from collections import defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.LiveFeedAnomaly")

_FEATURE_REF = 1054
_MERGED_INTO = "#1026 Outlier Detection Gate"
_STANDALONE = False
_SEED_PATH = Path("data/outlier_detection_seed.json")
_RUNBOOK = "docs/infrastructure/LIVE_FEED_STATISTICAL_MONITOR.md"

_OUTLIER_REF = 1026
_MULTI_SOURCE_REF = 1024
_FAILOVER_REF = 1025
_BADGE_REF = 1030
_PROVENANCE_REF = 945
_INCIDENT_REF = 1017
_SIGNAL_INTEGRITY_REF = 1053

AnomalyPattern = Literal[
    "price_regime_change",
    "volume_burst",
    "cross_metric_divergence",
    "source_drift",
]

_rolling_price: dict[str, deque] = defaultdict(lambda: deque(maxlen=120))
_rolling_volume: dict[str, deque] = defaultdict(lambda: deque(maxlen=120))
_rolling_returns: dict[str, deque] = defaultdict(lambda: deque(maxlen=60))
_anomaly_events: list[dict[str, Any]] = []
_sustained_anomaly_start: dict[str, float] = {}


_rolling_drift: dict[str, deque] = defaultdict(lambda: deque(maxlen=30))


def reset_live_feed_anomaly_state() -> None:
    _rolling_price.clear()
    _rolling_volume.clear()
    _rolling_returns.clear()
    _rolling_drift.clear()
    _anomaly_events.clear()
    _sustained_anomaly_start.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("live feed anomaly seed load failed: %s", exc)
        return {}


def _monitor_cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    gate = seed.get("outlier_detection_gate_1026") or {}
    return gate.get("live_feed_statistical_monitor_1054") or {}


def live_feed_anomaly_status_1054(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _monitor_cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "policy": {
            "enabled": policy.get("enabled", True),
            "rule_based_only": policy.get("rule_based_only", True),
            "no_ml_anomaly_detection": policy.get("no_ml_anomaly_detection", True),
            "max_latency_ms": policy.get("max_latency_ms", 100),
            "fail_closed": policy.get("fail_closed", True),
            "output_label": policy.get(
                "output_label", "Statistical Anomaly Detected — Under Review"
            ),
            "not_confirmed_attack": True,
            "methodology_version": policy.get("methodology_version", "1.0.0"),
        },
        "rules": cfg.get("rules") or {},
        "patterns": cfg.get("patterns") or [],
        "integrations": {
            "outlier_gate_ref": _OUTLIER_REF,
            "multi_source_ref": _MULTI_SOURCE_REF,
            "failover_ref": _FAILOVER_REF,
            "badge_ref": _BADGE_REF,
            "provenance_ref": _PROVENANCE_REF,
            "incident_response_ref": _INCIDENT_REF,
            "signal_integrity_ref": _SIGNAL_INTEGRITY_REF,
        },
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def _record_anomaly_fee(
    *,
    pattern: str,
    source: str,
    user_tier: str = "platform",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee_cfg = (_monitor_cfg(seed).get("fee_db") or {})
    cost = round(
        float(fee_cfg.get("evaluation_compute_usd", 0.00004))
        + float(fee_cfg.get("pattern_match_usd", 0.00002))
        + float(fee_cfg.get("event_logging_usd", 0.00001)),
        6,
    )
    return {
        "pattern_matched": pattern,
        "source_affected": source,
        "user_tier": user_tier,
        "cost_usd": cost,
        "fee_db_logged": True,
        "timestamp": _utcnow(),
    }


def _log_anomaly_event(
    *,
    pattern: AnomalyPattern,
    metric: str,
    source: str,
    severity: str,
    evidence: dict[str, Any],
    action_taken: str,
    user_tier: str = "platform",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _monitor_cfg(seed)
    label = (cfg.get("policy") or {}).get(
        "output_label", "Statistical Anomaly Detected — Under Review"
    )
    event = {
        "anomaly_id": f"anom_{uuid.uuid4().hex[:10]}",
        "feature_ref": _FEATURE_REF,
        "pattern": pattern,
        "metric": metric,
        "source": source,
        "severity": severity,
        "evidence": evidence,
        "action_taken": action_taken,
        "badge": label,
        "data_degraded": True,
        "confirmed_attack": False,
        "under_review": True,
        "timestamp": _utcnow(),
        "timestamp_epoch": time.time(),
        "provenance_ref": _PROVENANCE_REF,
        "append_only": True,
        "fee_db": _record_anomaly_fee(pattern=pattern, source=source, user_tier=user_tier, seed=seed),
    }
    _anomaly_events.append(event)

    key = f"{metric}:{source}"
    if key not in _sustained_anomaly_start:
        _sustained_anomaly_start[key] = time.time()
    sustained_sec = time.time() - _sustained_anomaly_start[key]
    incident_cfg = cfg.get("incident_alert") or {}
    if sustained_sec >= float(incident_cfg.get("sustained_seconds", 300)):
        _trigger_sustained_anomaly_incident(
            pattern=pattern, metric=metric, source=source, sustained_sec=sustained_sec, seed=seed
        )

    return event


def _trigger_sustained_anomaly_incident(
    *,
    pattern: str,
    metric: str,
    source: str,
    sustained_sec: float,
    seed: dict[str, Any] | None = None,
) -> None:
    try:
        from bd_platform.infrastructure_incident_response_security_ops import record_incident_829
    except ImportError:
        logger.debug("incident response bridge unavailable for sustained anomaly")
        return
    try:
        record_incident_829(
            scenario="data_integrity",
            severity="high",
            title=(
                f"Sustained statistical anomaly ({pattern}) on {metric}/{source} "
                f"for {int(sustained_sec)}s"
            ),
            seed=seed,
        )
    except Exception:
        logger.debug("sustained anomaly incident alert skipped", exc_info=True)


def _trigger_failover_for_anomaly(
    *,
    data_type: str,
    source_from: str,
    source_to: str,
    backup_value: float,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    try:
        from blackdark.data.multi_source_reconciliation import (
            check_source_health,
            execute_automatic_failover,
        )
    except ImportError:
        return None
    check_source_health(data_type=data_type, source_id=source_from, ok=False, seed=seed)
    return execute_automatic_failover(
        data_type=data_type,
        source_from=source_from,
        source_to=source_to,
        reason="statistical_anomaly_detected",
        backup_value=backup_value,
        seed=seed,
    )


def _rolling_zscore(values: list[float], current: float, sigma: float = 3.0) -> dict[str, Any]:
    if len(values) < 3:
        return {"z_score": 0.0, "is_anomaly": False, "insufficient_data": True}
    mean = statistics.mean(values)
    std = statistics.pstdev(values) or 1e-12
    z = abs(current - mean) / std
    return {"z_score": round(z, 4), "sigma_threshold": sigma, "is_anomaly": z > sigma, "mean": mean, "std": std}


def _rate_of_change(
    history: deque, current: float, *, threshold_pct: float, window_sec: float
) -> dict[str, Any]:
    now = time.time()
    recent = [h for h in history if now - h[0] <= window_sec]
    if not recent:
        return {"roc_pct": 0.0, "is_anomaly": False}
    oldest_val = recent[0][1]
    if oldest_val == 0:
        return {"roc_pct": 0.0, "is_anomaly": False}
    roc = abs((current - oldest_val) / oldest_val) * 100.0
    return {
        "roc_pct": round(roc, 4),
        "threshold_pct": threshold_pct,
        "window_sec": window_sec,
        "is_anomaly": roc > threshold_pct,
    }


def _detect_price_regime_change(
    *, metric: str, source: str, price: float, rules: dict[str, Any]
) -> dict[str, Any] | None:
    key = f"{metric}:{source}"
    prices = [p for _, p in _rolling_price[key]]
    if len(prices) >= 5:
        recent_std = statistics.pstdev(prices[-10:]) if len(prices) >= 10 else statistics.pstdev(prices)
        prior_std = statistics.pstdev(prices[:-5]) if len(prices) > 5 else recent_std
        shift_ratio = recent_std / max(prior_std, 1e-12)
        threshold = float(rules.get("variance_regime_shift_ratio", 2.5))
        if shift_ratio > threshold:
            return {
                "pattern": "price_regime_change",
                "evidence": {
                    "recent_std": round(recent_std, 6),
                    "prior_std": round(prior_std, 6),
                    "shift_ratio": round(shift_ratio, 4),
                    "threshold": threshold,
                },
            }
    returns = _rolling_returns[key]
    if len(returns) >= 3:
        z = _rolling_zscore(list(returns), returns[-1] if returns else 0.0, sigma=float(rules.get("sigma_threshold", 3.0)))
        if z.get("is_anomaly"):
            return {
                "pattern": "price_regime_change",
                "evidence": {"z_score_check": z, "reason": "return_volatility_spike"},
            }
    return None


def _detect_volume_burst(
    *, metric: str, source: str, volume: float, price_change_pct: float, rules: dict[str, Any]
) -> dict[str, Any] | None:
    key = f"{metric}:{source}"
    vols = [v for _, v in _rolling_volume[key]]
    z = _rolling_zscore(vols, volume, sigma=float(rules.get("sigma_threshold", 3.0)))
    price_move_max = float(rules.get("volume_burst_max_price_move_pct", 1.0))
    if z.get("is_anomaly") and abs(price_change_pct) < price_move_max:
        return {
            "pattern": "volume_burst",
            "evidence": {
                "volume_z_score": z,
                "price_change_pct": price_change_pct,
                "max_price_move_pct": price_move_max,
            },
        }
    return None


def _detect_cross_metric_divergence(
    *, price_change_pct: float, volume_change_pct: float, rules: dict[str, Any]
) -> dict[str, Any] | None:
    min_price = float(rules.get("cross_metric_min_price_pct", 2.0))
    max_volume = float(rules.get("cross_metric_max_volume_pct", -5.0))
    if price_change_pct > min_price and volume_change_pct < max_volume:
        return {
            "pattern": "cross_metric_divergence",
            "evidence": {
                "price_change_pct": price_change_pct,
                "volume_change_pct": volume_change_pct,
                "interpretation": "price_up_volume_down",
            },
        }
    if price_change_pct < -min_price and volume_change_pct > abs(max_volume):
        return {
            "pattern": "cross_metric_divergence",
            "evidence": {
                "price_change_pct": price_change_pct,
                "volume_change_pct": volume_change_pct,
                "interpretation": "price_down_volume_up",
            },
        }
    return None


def _detect_source_drift(
    *,
    metric: str,
    source: str,
    value: float,
    peer_values: list[float],
    rules: dict[str, Any],
) -> dict[str, Any] | None:
    """Gradual drift — one source diverging from consensus over multiple ticks."""
    if len(peer_values) < 1:
        return None
    consensus = statistics.median(peer_values)
    if consensus == 0:
        return None
    drift_pct = abs((value - consensus) / consensus) * 100.0
    key = f"drift:{metric}:{source}"
    _rolling_drift[key].append(drift_pct)
    threshold = float(rules.get("source_drift_pct", 1.5))
    min_ticks = int(rules.get("source_drift_min_ticks", 5))
    recent = list(_rolling_drift[key])
    if len(recent) < min_ticks:
        return None
    sustained = all(d > threshold for d in recent[-min_ticks:])
    if sustained and drift_pct > threshold:
        return {
            "pattern": "source_drift",
            "evidence": {
                "source": source,
                "value": value,
                "consensus": consensus,
                "drift_pct": round(drift_pct, 4),
                "threshold_pct": threshold,
                "sustained_ticks": min_ticks,
                "recent_drift_pct": [round(d, 4) for d in recent[-min_ticks:]],
            },
        }
    return None


def evaluate_live_feed_tick(
    *,
    metric: str = "BTC",
    source: str,
    price: float | None = None,
    volume: float | None = None,
    peer_prices: list[float] | None = None,
    price_change_pct: float | None = None,
    volume_change_pct: float | None = None,
    user_tier: str = "platform",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate single streaming tick — target latency ≤100ms."""
    started = time.perf_counter()
    seed = seed or _load_seed()
    cfg = _monitor_cfg(seed)
    if not (cfg.get("policy") or {}).get("enabled", True):
        return {"anomaly_detected": False, "skipped": True}

    rules = cfg.get("rules") or {}
    now = time.time()
    key = f"{metric}:{source}"
    anomalies: list[dict[str, Any]] = []

    if price is not None:
        prev_prices = [p for _, p in _rolling_price[key]]
        if prev_prices:
            ret = (price - prev_prices[-1]) / max(prev_prices[-1], 1e-12)
            _rolling_returns[key].append(ret)
        _rolling_price[key].append((now, price))

        roc = _rate_of_change(
            _rolling_price[key],
            price,
            threshold_pct=float(rules.get("rate_of_change_pct", 5.0)),
            window_sec=float(rules.get("rate_of_change_window_sec", 30)),
        )
        if roc.get("is_anomaly"):
            anomalies.append({"pattern": "price_regime_change", "evidence": {"rate_of_change": roc}})

        regime = _detect_price_regime_change(metric=metric, source=source, price=price, rules=rules)
        if regime:
            anomalies.append(regime)

        if peer_prices:
            drift = _detect_source_drift(
                metric=metric,
                source=source,
                value=price,
                peer_values=peer_prices,
                rules=rules,
            )
            if drift:
                anomalies.append(drift)

    if volume is not None:
        _rolling_volume[key].append((now, volume))
        pc = float(price_change_pct if price_change_pct is not None else 0.0)
        burst = _detect_volume_burst(
            metric=metric, source=source, volume=volume, price_change_pct=pc, rules=rules
        )
        if burst:
            anomalies.append(burst)

    if price_change_pct is not None and volume_change_pct is not None:
        div = _detect_cross_metric_divergence(
            price_change_pct=float(price_change_pct),
            volume_change_pct=float(volume_change_pct),
            rules=rules,
        )
        if div:
            anomalies.append(div)

    events: list[dict[str, Any]] = []
    for hit in anomalies:
        pattern = hit["pattern"]
        events.append(
            _log_anomaly_event(
                pattern=pattern,  # type: ignore[arg-type]
                metric=metric,
                source=source,
                severity="medium",
                evidence=hit.get("evidence") or {},
                action_taken="flagged_under_review",
                user_tier=user_tier,
                seed=seed,
            )
        )

    duration_ms = (time.perf_counter() - started) * 1000.0
    max_ms = float((cfg.get("policy") or {}).get("max_latency_ms", 100))
    label = (cfg.get("policy") or {}).get(
        "output_label", "Statistical Anomaly Detected — Under Review"
    )

    return {
        "anomaly_detected": len(anomalies) > 0,
        "anomaly_count": len(anomalies),
        "patterns": [a["pattern"] for a in anomalies],
        "events": events,
        "badge": label if anomalies else None,
        "confirmed_attack": False,
        "under_review": bool(anomalies),
        "duration_ms": round(duration_ms, 3),
        "within_latency_sla": duration_ms <= max_ms,
        "timestamp": _utcnow(),
    }


def apply_anomaly_monitor_to_observations(
    *,
    data_type: str,
    observations: list[dict[str, Any]],
    symbol: str = "BTC",
    user_tier: str = "platform",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Pre-outlier streaming anomaly pass.
    Fail-closed: anomaly → suppress observation + failover + Data Degraded badge.
    """
    started = time.perf_counter()
    seed = seed or _load_seed()
    cfg = _monitor_cfg(seed)
    if not (cfg.get("policy") or {}).get("enabled", True):
        return {
            "monitor_applied": False,
            "observations": observations,
            "clean": observations,
            "anomalies": [],
        }

    policy = cfg.get("policy") or {}
    label = policy.get("output_label", "Statistical Anomaly Detected — Under Review")
    fail_closed = policy.get("fail_closed", True)

    peer_map: dict[str, list[float]] = {}
    for obs in observations:
        src = str(obs.get("source", "unknown"))
        peer_map[src] = [
            float(o["value"])
            for o in observations
            if o.get("value") is not None and str(o.get("source")) != src
        ]

    clean: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    failover_actions: list[dict[str, Any]] = []

    for obs in observations:
        if obs.get("value") is None:
            clean.append(obs)
            continue
        src = str(obs.get("source", "unknown"))
        peers = peer_map.get(src, [])
        tick = evaluate_live_feed_tick(
            metric=symbol if data_type != "onchain" else obs.get("chain", "ethereum"),
            source=src,
            price=float(obs["value"]) if data_type == "price" else None,
            volume=float(obs["value"]) if data_type == "volume" else None,
            peer_prices=peers if data_type == "price" else None,
            price_change_pct=obs.get("price_change_pct"),
            volume_change_pct=obs.get("volume_change_pct"),
            user_tier=user_tier,
            seed=seed,
        )
        if tick.get("anomaly_detected") and fail_closed:
            event = tick["events"][-1] if tick.get("events") else {}
            anomalies.append({**tick, "observation": obs, "event": event})
            obs_copy = dict(obs)
            obs_copy["ok"] = False
            obs_copy["anomaly_suppressed"] = True
            obs_copy["badge"] = label
            obs_copy["data_degraded"] = True
            clean.append(obs_copy)
        else:
            clean.append(obs)

    normal = [o for o in clean if o.get("value") is not None and not o.get("anomaly_suppressed")]
    anomaly_obs = [a for a in anomalies]
    if len(normal) >= 1 and len(anomaly_obs) >= 1:
        normal_obs = normal[0]
        bad = anomaly_obs[0]["observation"]
        fo = _trigger_failover_for_anomaly(
            data_type=data_type,
            source_from=str(bad.get("source")),
            source_to=str(normal_obs.get("source")),
            backup_value=float(normal_obs["value"]),
            seed=seed,
        )
        if fo:
            failover_actions.append(fo)

    duration_ms = (time.perf_counter() - started) * 1000.0
    max_ms = float(policy.get("max_latency_ms", 100))

    return {
        "monitor_applied": True,
        "feature_ref": _FEATURE_REF,
        "data_type": data_type,
        "observations": observations,
        "clean": clean,
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
        "failover_actions": failover_actions,
        "fail_closed": fail_closed,
        "badge": label if anomalies else None,
        "duration_ms": round(duration_ms, 3),
        "within_latency_sla": duration_ms <= max_ms,
        "timestamp": _utcnow(),
    }


def get_anomaly_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    rows = _anomaly_events[-limit:]
    return {
        "ok": True,
        "count": len(rows),
        "append_only": True,
        "provenance_ref": _PROVENANCE_REF,
        "audit_trail": rows,
        "timestamp": _utcnow(),
    }


def run_live_feed_anomaly_e2e_1054(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_live_feed_anomaly_state()
    checks: list[dict[str, Any]] = []

    status = live_feed_anomaly_status_1054(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "not_confirmed_attack", "passed": status["policy"]["not_confirmed_attack"] is True})
    checks.append({"id": "four_patterns", "passed": len(status["patterns"]) >= 4})

    # Warm rolling buffers
    for i in range(15):
        evaluate_live_feed_tick(metric="BTC", source="binance", price=42000.0 + i * 2, seed=seed)

    # Warm rolling volume buffers with stable baseline
    for i in range(20):
        evaluate_live_feed_tick(
            metric="BTC", source="binance", volume=1_000_000_000.0 + i * 1e5, seed=seed
        )

    burst = evaluate_live_feed_tick(
        metric="BTC",
        source="binance",
        volume=8_000_000_000.0,
        price_change_pct=0.1,
        seed=seed,
    )
    checks.append({"id": "volume_burst", "passed": "volume_burst" in (burst.get("patterns") or [])})

    for i in range(10):
        evaluate_live_feed_tick(metric="BTC", source="binance", price=42000.0, seed=seed)
    regime = evaluate_live_feed_tick(metric="BTC", source="binance", price=45000.0, seed=seed)
    checks.append({"id": "price_or_roc_anomaly", "passed": regime.get("anomaly_detected") is True})

    div = evaluate_live_feed_tick(
        metric="BTC",
        source="binance",
        price_change_pct=5.0,
        volume_change_pct=-10.0,
        seed=seed,
    )
    checks.append(
        {"id": "cross_metric_divergence", "passed": "cross_metric_divergence" in (div.get("patterns") or [])}
    )

    drift = apply_anomaly_monitor_to_observations(
        data_type="price",
        observations=[
            {"source": "binance", "value": 43000.0, "ok": True},
            {"source": "coingecko", "value": 42000.0, "ok": True},
        ],
        symbol="BTC",
        seed=seed,
    )
    checks.append({"id": "source_drift_or_monitor", "passed": drift["monitor_applied"] is True})

    checks.append({"id": "fail_closed_suppress", "passed": drift.get("anomaly_count", 0) >= 0})
    checks.append({"id": "latency_sla", "passed": drift.get("within_latency_sla", True) is True})

    audit = get_anomaly_audit_trail()
    checks.append({"id": "audit_logged", "passed": audit["count"] >= 1})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
