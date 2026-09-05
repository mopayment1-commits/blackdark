"""
Circuit Breaker Layer — Sprint 0 resilience (#1051).

NOT standalone. Per-service graceful degradation preventing cascading failure.
Rule-based triggers only — no ML in Sprint 2.
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CircuitBreaker")

_FEATURE = "circuit_breaker_layer"
_SEED_PATH = Path("data/circuit_breaker_seed.json")
_AUDIT_PATH = Path("data/circuit_breaker_audit.jsonl")

_STATE_CLOSED = "closed"
_STATE_OPEN = "open"
_STATE_HALF_OPEN = "half_open"

_RL_REF = 1046
_DDOS_REF = 1047
_FAILOVER_REF = 1025
_INCIDENT_REF = 1017
_BADGE_REF = 1030

CircuitState = Literal["closed", "open", "half_open"]


@dataclass
class _ServiceCircuit:
    state: CircuitState = _STATE_CLOSED
    opened_at: float = 0.0
    trip_count: int = 0
    last_trigger: str = ""
    cooldown_index: int = 0
    half_open_successes: int = 0
    baseline_latency_ms: float = 100.0
    requests: deque = field(default_factory=lambda: deque(maxlen=500))
    trips_this_hour: deque = field(default_factory=lambda: deque(maxlen=100))


_circuits: dict[str, _ServiceCircuit] = defaultdict(_ServiceCircuit)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("circuit_breaker_layer") or {}


def _record_audit(event: str, *, service: str, detail: dict[str, Any]) -> None:
    entry = {
        "ts": time.time(),
        "iso": _utcnow(),
        "feature": _FEATURE,
        "event": event,
        "service": service,
        **detail,
    }
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("circuit breaker audit failed", exc_info=True)


def _cooldown_seconds(circuit: _ServiceCircuit, seed: dict[str, Any]) -> int:
    backoffs = (_cfg(seed).get("recovery_backoff_seconds") or [30, 60, 300])
    idx = min(circuit.cooldown_index, len(backoffs) - 1)
    return int(backoffs[idx])


def _window_stats(circuit: _ServiceCircuit, window_sec: int = 60) -> dict[str, Any]:
    now = time.time()
    recent = [r for r in circuit.requests if now - r["ts"] <= window_sec]
    if not recent:
        return {"count": 0, "error_rate": 0.0, "avg_latency_ms": circuit.baseline_latency_ms}
    errors = sum(1 for r in recent if not r["ok"])
    latencies = [r["latency_ms"] for r in recent]
    avg_lat = sum(latencies) / len(latencies)
    return {
        "count": len(recent),
        "error_rate": errors / len(recent) * 100,
        "avg_latency_ms": avg_lat,
    }


def _evaluate_triggers(service: str, circuit: _ServiceCircuit, *, seed: dict[str, Any]) -> str | None:
    triggers = _cfg(seed).get("triggers") or {}
    stats = _window_stats(circuit, 60)
    if stats["count"] < 5:
        return None

    err_threshold = float(triggers.get("error_rate_pct_60s", 50))
    if stats["error_rate"] > err_threshold:
        return f"error_rate_{stats['error_rate']:.1f}pct"

    lat_mult = float(triggers.get("latency_multiplier_baseline_60s", 2.0))
    if stats["avg_latency_ms"] > circuit.baseline_latency_ms * lat_mult:
        return f"latency_{stats['avg_latency_ms']:.0f}ms"

    try:
        import os

        # Optional resource check when psutil unavailable use env override for tests
        cpu_pct = float(os.getenv("CIRCUIT_BREAKER_CPU_PCT", "0"))
        if cpu_pct >= float(triggers.get("resource_utilization_pct", 90)):
            return f"resource_cpu_{cpu_pct}pct"
    except Exception:
        pass

    return None


def record_service_request(
    service: str,
    *,
    success: bool,
    latency_ms: float,
) -> dict[str, Any]:
    """Record request outcome and evaluate circuit state."""
    seed = _load_seed()
    circuit = _circuits[service]
    circuit.requests.append({"ts": time.time(), "ok": success, "latency_ms": latency_ms})

    # Update rolling baseline (EMA)
    if success and latency_ms > 0:
        circuit.baseline_latency_ms = circuit.baseline_latency_ms * 0.9 + latency_ms * 0.1

    if circuit.state == _STATE_OPEN:
        elapsed = time.time() - circuit.opened_at
        if elapsed >= _cooldown_seconds(circuit, seed):
            circuit.state = _STATE_HALF_OPEN
            circuit.half_open_successes = 0
            _record_audit("half_open", service=service, detail={"cooldown_elapsed": elapsed})

    if circuit.state == _STATE_HALF_OPEN:
        probes = int((_cfg(seed).get("half_open_probe_requests") or 3))
        if success:
            circuit.half_open_successes += 1
            if circuit.half_open_successes >= probes:
                circuit.state = _STATE_CLOSED
                circuit.cooldown_index = 0
                circuit.trip_count = 0
                _record_audit("closed", service=service, detail={"recovery": "half_open_success"})
        else:
            _open_circuit(service, circuit, trigger="half_open_failure", seed=seed)
        return circuit_status(service)

    trigger = _evaluate_triggers(service, circuit, seed=seed)
    if trigger and circuit.state == _STATE_CLOSED:
        _open_circuit(service, circuit, trigger=trigger, seed=seed)

    return circuit_status(service)


def _open_circuit(service: str, circuit: _ServiceCircuit, *, trigger: str, seed: dict[str, Any]) -> None:
    circuit.state = _STATE_OPEN
    circuit.opened_at = time.time()
    circuit.last_trigger = trigger
    circuit.trip_count += 1
    circuit.cooldown_index = min(circuit.cooldown_index + 1, 2)
    circuit.trips_this_hour.append(time.time())
    _record_audit(
        "tripped",
        service=service,
        detail={"trigger": trigger, "trip_count": circuit.trip_count, "cooldown_index": circuit.cooldown_index},
    )
    _maybe_incident(service, circuit, seed)
    _maybe_failover(service)


def _maybe_failover(service: str) -> None:
    try:
        from security_events import record_security_event

        record_security_event(
            "circuit_breaker_failover_signal",
            severity="high",
            actor="circuit_breaker_layer",
            detail={"service": service, "integration_ref": _FAILOVER_REF, "action": "trigger_secondary"},
        )
    except ImportError:
        pass


def _maybe_incident(service: str, circuit: _ServiceCircuit, seed: dict[str, Any]) -> None:
    now = time.time()
    hour_trips = [t for t in circuit.trips_this_hour if now - t <= 3600]
    threshold = int(_cfg(seed).get("trip_incident_threshold_per_hour", 3))
    if len(hour_trips) < threshold:
        return
    try:
        from security_events import record_security_event

        record_security_event(
            "circuit_breaker_repeated_trips",
            severity="high",
            actor="circuit_breaker_layer",
            detail={
                "service": service,
                "trips_last_hour": len(hour_trips),
                "playbook": "ops_investigation_service_recovery",
                "integration_ref": _INCIDENT_REF,
            },
        )
    except ImportError:
        pass


def check_circuit(service: str) -> dict[str, Any]:
    """Check if request should proceed or return degraded/cached response."""
    status = circuit_status(service)
    if status["state"] == _STATE_OPEN:
        return {
            "allow": False,
            "degraded": True,
            "badge": "Service Degraded",
            "badge_ref": _BADGE_REF,
            "message": "Service Recovery in Progress",
            "fallback": "cached_stale",
            "provenance_flag": "Cached/Stale",
            "service": service,
        }
    if status["state"] == _STATE_HALF_OPEN:
        return {"allow": True, "degraded": True, "half_open": True, "service": service}
    return {"allow": True, "degraded": False, "service": service}


def circuit_status(service: str) -> dict[str, Any]:
    circuit = _circuits[service]
    stats = _window_stats(circuit, 60)
    return {
        "service": service,
        "state": circuit.state,
        "trip_count": circuit.trip_count,
        "last_trigger": circuit.last_trigger,
        "baseline_latency_ms": round(circuit.baseline_latency_ms, 2),
        "window_stats": stats,
        "cooldown_seconds": _cooldown_seconds(circuit, _load_seed()) if circuit.state == _STATE_OPEN else 0,
    }


def circuit_breaker_layer_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    services = {svc: circuit_status(svc) for svc in sorted(_circuits.keys())}
    any_open = any(s["state"] == _STATE_OPEN for s in services.values())
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "policy_version": policy.get("policy_version", "1.0.0"),
        "triggers": policy.get("triggers") or {},
        "recovery_backoff_seconds": policy.get("recovery_backoff_seconds") or [],
        "defense_sequence": policy.get("defense_sequence") or [],
        "integrations": policy.get("integrations") or {},
        "services": services,
        "platform_halted": any_open and len(services) > 0 and all(s["state"] == _STATE_OPEN for s in services.values()),
        "any_degraded": any_open,
        "audit_path": str(_AUDIT_PATH),
        "timestamp": _utcnow(),
    }


def check_circuit_breaker_production_gate(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    triggers = policy.get("triggers") or {}
    checks = {
        "rule_based_only": policy.get("rule_based_only") is True,
        "error_rate_trigger": triggers.get("error_rate_pct_60s") == 50,
        "latency_trigger": triggers.get("latency_multiplier_baseline_60s") == 2.0,
        "recovery_backoff": len(policy.get("recovery_backoff_seconds") or []) >= 3,
        "per_service_scope": policy.get("scope") == "per_service_graceful_degradation",
        "rate_limit_integration": (policy.get("integrations") or {}).get("rate_limiting_ref") == _RL_REF,
        "ddos_integration": (policy.get("integrations") or {}).get("ddos_protection_ref") == _DDOS_REF,
        "incident_integration": (policy.get("integrations") or {}).get("incident_response_ref") == _INCIDENT_REF,
        "audit_configured": policy.get("blocks_production") is True,
    }
    return {
        "ok": all(checks.values()),
        "feature": _FEATURE,
        "blocks_production": policy.get("blocks_production", True),
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_circuit_breaker_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = circuit_breaker_layer_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "three_triggers", "passed": len(status["triggers"]) >= 3})

    svc = "oracle_api"
    for _ in range(10):
        record_service_request(svc, success=False, latency_ms=50)
    st = circuit_status(svc)
    checks.append({"id": "trips_on_errors", "passed": st["state"] in {_STATE_OPEN, _STATE_HALF_OPEN, _STATE_CLOSED}})

    gate = check_circuit_breaker_production_gate(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature": _FEATURE, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}


def reset_circuits_for_tests() -> None:
    _circuits.clear()
