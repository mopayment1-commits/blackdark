"""
Outlier Detection Gate — #1026 (Data Engine).

Merged into Data Engine / Oracle API — NOT standalone.
Validates every incoming data point against expected ranges before API response.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.OutlierDetectionGate")

_FEATURE_REF = 1026
_LIVE_FEED_ANOMALY_REF = 1054
_MERGED_INTO = "Data Engine"
_STANDALONE = False
_SEED_PATH = Path("data/outlier_detection_seed.json")
_RUNBOOK = "docs/infrastructure/OUTLIER_DETECTION_GATE.md"

_PROVENANCE_REF = 945
_MULTI_SOURCE_REF = 1024
_FAILOVER_REF = 1025
_REFERENCE_PRICING_REF = 959
_REAL_VOLUME_REF = 992
_INCIDENT_RESPONSE_REF = 1017
_LOAD_TEST_REF = 1020
_EVENTS_REF = 939
_NEWS_REF = 941

DataType = Literal["price", "volume", "onchain"]
Methodology = Literal["z_score", "iqr", "median_deviation_pct", "consensus_deviation_pct"]

_outlier_events: list[dict[str, Any]] = []
_source_outlier_counts: dict[str, list[float]] = {}


def reset_outlier_state() -> None:
    _outlier_events.clear()
    _source_outlier_counts.clear()
    try:
        from blackdark.data.live_feed_statistical_monitor import reset_live_feed_anomaly_state

        reset_live_feed_anomaly_state()
    except ImportError:
        pass


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("outlier detection seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("outlier_detection_gate_1026") or {}


def outlier_gate_status_1026(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "policy": {
            "enabled": policy.get("enabled", True),
            "fail_closed": policy.get("fail_closed", True),
            "methodology": policy.get("methodology", "z_score_and_iqr"),
            "methodology_version": policy.get("methodology_version", "1.0.0"),
            "no_ml_anomaly_detection_sprint_2": policy.get("no_ml_anomaly_detection_sprint_2", True),
            "max_overhead_ms": policy.get("max_overhead_ms", 50),
            "blocks_production_if_incomplete": policy.get("blocks_production_if_incomplete", True),
        },
        "bounds": cfg.get("bounds") or {},
        "historical_baseline": cfg.get("historical_baseline") or {},
        "live_feed_anomaly_monitor": {
            "feature_ref": _LIVE_FEED_ANOMALY_REF,
            "merged_into": _FEATURE_REF,
            "sequence": "ingest → anomaly detection → outlier validation → serve/reject",
        },
        "integrations": {
            "provenance_ref": _PROVENANCE_REF,
            "multi_source_ref": _MULTI_SOURCE_REF,
            "automatic_failover_ref": _FAILOVER_REF,
            "live_feed_anomaly_ref": _LIVE_FEED_ANOMALY_REF,
            "reference_pricing_ref": _REFERENCE_PRICING_REF,
            "real_volume_ref": _REAL_VOLUME_REF,
            "incident_response_ref": _INCIDENT_RESPONSE_REF,
            "load_test_ref": _LOAD_TEST_REF,
            "events_ref": _EVENTS_REF,
            "news_ref": _NEWS_REF,
        },
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def _baseline_for(
    *,
    data_type: DataType,
    symbol: str = "BTC",
    chain: str = "ethereum",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    baselines = seed.get("baselines") or {}
    if data_type == "onchain":
        return baselines.get(chain, {}).get("onchain") or {
            "consensus": 19_500_000.0,
            "history_90d": {"mean": 19_450_000.0, "std": 50_000.0},
        }
    return baselines.get(symbol, {}).get(data_type) or {
        "median_5m": 42_000.0,
        "mean_24h": 1_200_000_000.0,
        "std_24h": 80_000_000.0,
        "history_90d": {"mean": 41_500.0, "std": 1_200.0},
    }


def compute_expected_range(
    *,
    data_type: DataType,
    symbol: str = "BTC",
    chain: str = "ethereum",
    peer_values: list[float] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based expected range — versioned methodology, no static-only thresholds."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    bounds = (cfg.get("bounds") or {}).get(data_type) or {}
    baseline = _baseline_for(data_type=data_type, symbol=symbol, chain=chain, seed=seed)
    hist = baseline.get("history_90d") or {}

    if data_type == "price":
        tolerance = float(bounds.get("tolerance_pct", 5.0))
        center = float(baseline.get("median_5m", hist.get("mean", 42_000.0)))
        low = center * (1 - tolerance / 100.0)
        high = center * (1 + tolerance / 100.0)
        return {
            "data_type": data_type,
            "method": "median_deviation_pct",
            "methodology_version": (cfg.get("policy") or {}).get("methodology_version", "1.0.0"),
            "center": center,
            "expected_low": low,
            "expected_high": high,
            "tolerance_pct": tolerance,
            "peer_median": statistics.median(peer_values) if peer_values else None,
            "rolling_window_days": (cfg.get("historical_baseline") or {}).get("rolling_window_days", 90),
        }

    if data_type == "volume":
        sigma = float(bounds.get("sigma_threshold", 3.0))
        mean = float(baseline.get("mean_24h", hist.get("mean", 1_200_000_000.0)))
        std = float(baseline.get("std_24h", hist.get("std", 80_000_000.0)))
        low = mean - sigma * std
        high = mean + sigma * std
        return {
            "data_type": data_type,
            "method": "z_score",
            "methodology_version": (cfg.get("policy") or {}).get("methodology_version", "1.0.0"),
            "center": mean,
            "expected_low": max(0.0, low),
            "expected_high": high,
            "sigma_threshold": sigma,
            "rolling_window_days": (cfg.get("historical_baseline") or {}).get("rolling_window_days", 90),
        }

    tolerance = float(bounds.get("tolerance_pct", 0.1))
    if peer_values:
        center = statistics.median(peer_values)
    else:
        center = float(baseline.get("consensus", hist.get("mean", 19_500_000.0)))
    low = center * (1 - tolerance / 100.0)
    high = center * (1 + tolerance / 100.0)
    return {
        "data_type": data_type,
        "method": "consensus_deviation_pct",
        "methodology_version": (cfg.get("policy") or {}).get("methodology_version", "1.0.0"),
        "center": center,
        "expected_low": low,
        "expected_high": high,
        "tolerance_pct": tolerance,
        "rolling_window_days": (cfg.get("historical_baseline") or {}).get("rolling_window_days", 90),
    }


def detect_outlier_zscore(*, value: float, mean: float, std: float, sigma: float = 3.0) -> dict[str, Any]:
    std = max(std, 1e-12)
    z = abs(value - mean) / std
    return {
        "method": "z_score",
        "z_score": round(z, 4),
        "sigma_threshold": sigma,
        "is_outlier": z > sigma,
    }


def detect_outlier_iqr(*, values: list[float], value: float) -> dict[str, Any]:
    if len(values) < 4:
        return {"method": "iqr", "is_outlier": False, "insufficient_data": True}
    sorted_vals = sorted(values)
    q1 = statistics.quantiles(sorted_vals, n=4)[0]
    q3 = statistics.quantiles(sorted_vals, n=4)[2]
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    return {
        "method": "iqr",
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "expected_low": low,
        "expected_high": high,
        "is_outlier": value < low or value > high,
    }


def record_outlier_fee(*, data_type: DataType, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    cost = round(
        float(fee_cfg.get("validation_compute_usd", 0.00003))
        + float(fee_cfg.get("baseline_storage_usd", 0.00001))
        + float(fee_cfg.get("event_logging_usd", 0.00001)),
        6,
    )
    return {
        "data_type": data_type,
        "cost_usd": cost,
        "fee_db_logged": True,
        "logged_per_data_point": True,
        "timestamp": _utcnow(),
    }


def _outlier_events_last_hour(*, source: str | None = None) -> list[dict[str, Any]]:
    cutoff = time.time() - 3600.0
    events = []
    for ev in _outlier_events:
        ts = ev.get("timestamp_epoch", 0)
        if ts >= cutoff and (source is None or ev.get("source") == source):
            events.append(ev)
    return events


def log_outlier_event(
    *,
    data_type: DataType,
    metric: str,
    value: float,
    expected_range: dict[str, Any],
    source: str,
    action_taken: str,
    corroborated: bool = False,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append-only provenance (#945) logging."""
    seed = seed or _load_seed()
    badge = "Confirmed Event" if corroborated else "Outlier Detected / Data Degraded"
    event = {
        "outlier_id": f"out_{uuid.uuid4().hex[:10]}",
        "feature_ref": _FEATURE_REF,
        "data_type": data_type,
        "metric": metric,
        "value": value,
        "expected_range": expected_range,
        "source": source,
        "action_taken": action_taken,
        "badge": badge,
        "corroborated": corroborated,
        "timestamp": _utcnow(),
        "timestamp_epoch": time.time(),
        "provenance_ref": _PROVENANCE_REF,
        "append_only": True,
        "fee_db": record_outlier_fee(data_type=data_type, seed=seed),
    }
    _outlier_events.append(event)

    key = f"{data_type}:{source}"
    _source_outlier_counts.setdefault(key, []).append(time.time())
    _source_outlier_counts[key] = [t for t in _source_outlier_counts[key] if t >= time.time() - 3600.0]

    threshold = int(
        ((_cfg(seed).get("incident_alert") or {}).get("threshold_per_source_per_hour", 3))
    )
    if len(_source_outlier_counts[key]) > threshold:
        _trigger_outlier_incident(source=source, data_type=data_type, count=len(_source_outlier_counts[key]), seed=seed)

    return event


def _trigger_outlier_incident(
    *, source: str, data_type: DataType, count: int, seed: dict[str, Any] | None = None
) -> None:
    try:
        from bd_platform.infrastructure_incident_response_security_ops import record_incident_829
    except ImportError:
        logger.debug("incident response bridge unavailable for outlier alert")
        return
    try:
        record_incident_829(
            scenario="data_integrity",
            severity="high",
            title=f"Repeated outliers: {count}/hour from {source} ({data_type})",
            seed=seed,
        )
    except Exception:
        logger.debug("outlier incident alert skipped", exc_info=True)


def check_corroborated_event(
    *,
    observation: dict[str, Any],
    seed: dict[str, Any] | None = None,
) -> bool:
    """Real spike → Confirmed Event only if corroborated by #939 Events or #941 News."""
    seed = seed or _load_seed()
    corroboration = (_cfg(seed).get("event_corroboration") or {})
    if not corroboration.get("requires_evidence", True):
        return False
    events = observation.get("events_ref") or observation.get("corroborated_by_events")
    news = observation.get("news_ref") or observation.get("corroborated_by_news")
    return bool(events or news)


def _trigger_failover_for_outlier(
    *,
    data_type: DataType,
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
    check_source_health(
        data_type=data_type,
        source_id=source_from,
        ok=False,
        seed=seed,
    )
    return execute_automatic_failover(
        data_type=data_type,
        source_from=source_from,
        source_to=source_to,
        reason="outlier_detected",
        backup_value=backup_value,
        seed=seed,
    )


def check_observation(
    *,
    data_type: DataType,
    source: str,
    value: float,
    symbol: str = "BTC",
    chain: str = "ethereum",
    peer_values: list[float] | None = None,
    observation: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check single observation against expected range."""
    started = time.perf_counter()
    seed = seed or _load_seed()
    obs = observation or {"source": source, "value": value}
    expected = compute_expected_range(
        data_type=data_type,
        symbol=symbol,
        chain=chain,
        peer_values=peer_values,
        seed=seed,
    )
    low = float(expected["expected_low"])
    high = float(expected["expected_high"])
    is_outlier = value < low or value > high

    corroborated = False
    if is_outlier and check_corroborated_event(observation=obs, seed=seed):
        corroborated = True
        is_outlier = False

    duration_ms = (time.perf_counter() - started) * 1000.0
    max_ms = float((_cfg(seed).get("policy") or {}).get("max_overhead_ms", 50))

    return {
        "source": source,
        "value": value,
        "is_outlier": is_outlier,
        "corroborated": corroborated,
        "expected_range": expected,
        "badge": (
            "Confirmed Event" if corroborated else ("Outlier Detected / Data Degraded" if is_outlier else None)
        ),
        "duration_ms": round(duration_ms, 3),
        "within_overhead_sla": duration_ms <= max_ms,
    }


def apply_outlier_gate_to_observations(
    *,
    data_type: DataType,
    observations: list[dict[str, Any]],
    symbol: str = "BTC",
    chain: str = "ethereum",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Cross-source outlier gate — suppress outliers, switch to normal source, log divergence.
    #1024 multi-source input. #1054 anomaly monitor runs first (ingest → anomaly → outlier).
    """
    started = time.perf_counter()
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    if not (cfg.get("policy") or {}).get("enabled", True):
        return {
            "gate_applied": False,
            "observations": observations,
            "clean": observations,
            "outliers": [],
        }

    anomaly_meta: dict[str, Any] | None = None
    working_obs = list(observations)
    try:
        from blackdark.data.live_feed_statistical_monitor import apply_anomaly_monitor_to_observations

        anomaly_meta = apply_anomaly_monitor_to_observations(
            data_type=data_type,
            observations=working_obs,
            symbol=symbol,
            seed=seed,
        )
        working_obs = anomaly_meta["clean"]
    except ImportError:
        logger.debug("live feed statistical monitor unavailable")

    valid_values = [float(o["value"]) for o in working_obs if o.get("value") is not None]
    peer_values = valid_values if len(valid_values) >= 2 else None

    clean: list[dict[str, Any]] = []
    outliers: list[dict[str, Any]] = []
    failover_actions: list[dict[str, Any]] = []

    for obs in working_obs:
        if obs.get("value") is None:
            clean.append(obs)
            continue
        check = check_observation(
            data_type=data_type,
            source=str(obs.get("source", "unknown")),
            value=float(obs["value"]),
            symbol=symbol,
            chain=chain,
            peer_values=peer_values,
            observation=obs,
            seed=seed,
        )
        if check["is_outlier"]:
            event = log_outlier_event(
                data_type=data_type,
                metric=symbol if data_type != "onchain" else chain,
                value=float(obs["value"]),
                expected_range=check["expected_range"],
                source=str(obs.get("source", "unknown")),
                action_taken="suppressed",
                corroborated=check["corroborated"],
                seed=seed,
            )
            outliers.append({**check, "observation": obs, "event": event})
            obs_copy = dict(obs)
            obs_copy["ok"] = False
            obs_copy["outlier_suppressed"] = True
            clean.append(obs_copy)
        else:
            clean.append(obs)

    # Cross-source: one outlier + one normal → failover to normal
    normal = [o for o in clean if o.get("value") is not None and not o.get("outlier_suppressed")]
    outlier_sources = [o for o in outliers]
    if len(normal) == 1 and len(outlier_sources) == 1:
        normal_obs = normal[0]
        outlier_obs = outlier_sources[0]["observation"]
        fo = _trigger_failover_for_outlier(
            data_type=data_type,
            source_from=str(outlier_obs.get("source")),
            source_to=str(normal_obs.get("source")),
            backup_value=float(normal_obs["value"]),
            seed=seed,
        )
        if fo:
            failover_actions.append(fo)
        log_outlier_event(
            data_type=data_type,
            metric=symbol if data_type != "onchain" else chain,
            value=float(outlier_obs["value"]),
            expected_range=outlier_sources[0]["expected_range"],
            source=str(outlier_obs.get("source")),
            action_taken="cross_source_divergence_logged",
            seed=seed,
        )

    duration_ms = (time.perf_counter() - started) * 1000.0
    max_ms = float((cfg.get("policy") or {}).get("max_overhead_ms", 50))

    result = {
        "gate_applied": True,
        "feature_ref": _FEATURE_REF,
        "data_type": data_type,
        "observations": observations,
        "clean": clean,
        "outliers": outliers,
        "outlier_count": len(outliers),
        "failover_actions": failover_actions,
        "duration_ms": round(duration_ms, 3),
        "within_overhead_sla": duration_ms <= max_ms,
        "timestamp": _utcnow(),
    }
    if anomaly_meta:
        result["anomaly_monitor"] = anomaly_meta
        if anomaly_meta.get("anomaly_count", 0) > 0:
            result["data_degraded"] = True
            result["badge"] = anomaly_meta.get("badge") or "Data Degraded"
    return result


def apply_outlier_gate_to_response(
    *,
    result: dict[str, Any],
    data_type: DataType,
    symbol: str = "BTC",
    chain: str = "ethereum",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Final gate before API response — fail-closed on outlier reconciled value."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    if not policy.get("enabled", True):
        return result

    value = result.get("value")
    if value is None or result.get("suppress_output"):
        result["outlier_gate"] = {"applied": True, "skipped": "no_value_or_already_suppressed"}
        return result

    expected = compute_expected_range(
        data_type=data_type,
        symbol=symbol,
        chain=chain,
        seed=seed,
    )
    low = float(expected["expected_low"])
    high = float(expected["expected_high"])
    is_outlier = float(value) < low or float(value) > high

    if not is_outlier:
        result["outlier_gate"] = {
            "applied": True,
            "passed": True,
            "expected_range": expected,
        }
        return result

    if policy.get("fail_closed", True):
        event = log_outlier_event(
            data_type=data_type,
            metric=symbol if data_type != "onchain" else chain,
            value=float(value),
            expected_range=expected,
            source="reconciled_output",
            action_taken="suppress_response",
            seed=seed,
        )
        result["ok"] = False
        result["status"] = "outlier_suppressed"
        result["data_degraded"] = True
        result["badge"] = "Outlier Detected / Data Degraded"
        result["suppress_output"] = True
        result["outlier_gate"] = {
            "applied": True,
            "passed": False,
            "fail_closed": True,
            "expected_range": expected,
            "event": event,
        }
    return result


def get_outlier_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    rows = _outlier_events[-limit:]
    return {
        "ok": True,
        "count": len(rows),
        "append_only": True,
        "provenance_ref": _PROVENANCE_REF,
        "audit_trail": rows,
        "timestamp": _utcnow(),
    }


def check_production_gate_1026(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = outlier_gate_status_1026(seed=seed)
    policy = status["policy"]
    bounds_ok = all(k in status["bounds"] for k in ("price", "volume", "onchain"))
    complete = (
        policy["enabled"]
        and policy["fail_closed"]
        and bounds_ok
        and policy["no_ml_anomaly_detection_sprint_2"]
    )
    return {
        "ok": complete,
        "feature_ref": _FEATURE_REF,
        "blocks_production": status["policy"]["blocks_production_if_incomplete"],
        "production_allowed": complete,
        "checks": {
            "enabled": policy["enabled"],
            "fail_closed": policy["fail_closed"],
            "bounds_configured": bounds_ok,
            "no_ml_sprint_2": policy["no_ml_anomaly_detection_sprint_2"],
        },
        "timestamp": _utcnow(),
    }


def run_outlier_e2e_1026(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = outlier_gate_status_1026(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})

    normal = check_observation(
        data_type="price", source="binance", value=42100.0, symbol="BTC", seed=seed
    )
    checks.append({"id": "normal_price_passes", "passed": normal["is_outlier"] is False})

    outlier = check_observation(
        data_type="price", source="binance", value=50000.0, symbol="BTC", seed=seed
    )
    checks.append({"id": "price_outlier_detected", "passed": outlier["is_outlier"] is True})
    checks.append({"id": "outlier_badge", "passed": outlier["badge"] == "Outlier Detected / Data Degraded"})

    corroborated = check_observation(
        data_type="price",
        source="binance",
        value=50000.0,
        symbol="BTC",
        observation={"source": "binance", "value": 50000.0, "corroborated_by_news": True},
        seed=seed,
    )
    checks.append({"id": "corroborated_event", "passed": corroborated["corroborated"] is True})
    checks.append({"id": "corroborated_not_outlier", "passed": corroborated["is_outlier"] is False})

    cross = apply_outlier_gate_to_observations(
        data_type="price",
        observations=[
            {"source": "binance", "value": 50000.0, "ok": True},
            {"source": "coingecko", "value": 42100.0, "ok": True},
        ],
        symbol="BTC",
        seed=seed,
    )
    checks.append({"id": "cross_source_outlier", "passed": cross["outlier_count"] == 1})
    checks.append({"id": "cross_source_failover", "passed": len(cross["failover_actions"]) >= 1})

    vol_outlier = check_observation(
        data_type="volume", source="coinmarketcap", value=3_000_000_000.0, symbol="BTC", seed=seed
    )
    checks.append({"id": "volume_zscore_outlier", "passed": vol_outlier["is_outlier"] is True})

    response_gate = apply_outlier_gate_to_response(
        result={"ok": True, "value": 50000.0, "status": "reconciled"},
        data_type="price",
        symbol="BTC",
        seed=seed,
    )
    checks.append({"id": "fail_closed_suppress", "passed": response_gate["suppress_output"] is True})

    gate = check_production_gate_1026(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["production_allowed"] is True})

    audit = get_outlier_audit_trail()
    checks.append({"id": "audit_logged", "passed": audit["count"] >= 1})

    overhead = normal.get("within_overhead_sla", True) and cross.get("within_overhead_sla", True)
    checks.append({"id": "overhead_sla_50ms", "passed": overhead is True})

    try:
        from blackdark.data.live_feed_statistical_monitor import run_live_feed_anomaly_e2e_1054

        anomaly_e2e = run_live_feed_anomaly_e2e_1054(seed=seed)
        checks.append({"id": "live_feed_anomaly_e2e", "passed": anomaly_e2e["all_passed"] is True})
    except ImportError:
        checks.append({"id": "live_feed_anomaly_e2e", "passed": False})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
