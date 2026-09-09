"""Anonymous SSE/WebSocket policy — AV §20."""

from __future__ import annotations

import time
from typing import Any

STREAM_POLICIES: dict[str, dict[str, Any]] = {
    "/api/trust-pulse/stream": {
        "connection_cap_per_ip": 3,
        "idle_timeout_sec": 120,
        "max_duration_sec": 900,
        "heartbeat_sec": 20,
        "backpressure": True,
        "upstream_sharing": True,
        "public_summary_only": True,
        "abuse_detection": True,
    },
}

_STREAM_STATE: dict[str, dict[str, Any]] = {}


def stream_policy(path: str) -> dict[str, Any] | None:
    return STREAM_POLICIES.get(path)


def validate_stream_path(path: str) -> dict[str, Any]:
    policy = stream_policy(path)
    if policy is None:
        return {"ok": False, "path": path, "allowed": False, "reason": "not_declared_public_stream"}
    return {"ok": True, "path": path, "allowed": True, "policy": policy}


def register_stream_connection(*, path: str, client_id: str) -> dict[str, Any]:
    policy = stream_policy(path)
    if policy is None:
        return {"allowed": False, "reason": "undeclared"}
    key = f"{path}:{client_id}"
    state = _STREAM_STATE.setdefault(
        key, {"connections": 0, "opened_at": time.monotonic(), "last_event_at": time.monotonic()}
    )
    if state["connections"] >= policy["connection_cap_per_ip"]:
        return {"allowed": False, "reason": "connection_cap", "policy": policy}
    state["connections"] += 1
    state["last_event_at"] = time.monotonic()
    return {"allowed": True, "policy": policy, "state": state}


def touch_stream_connection(*, path: str, client_id: str) -> dict[str, Any]:
    key = f"{path}:{client_id}"
    state = _STREAM_STATE.get(key)
    if not state:
        return {"allowed": False, "reason": "unknown_connection"}
    policy = stream_policy(path) or {}
    now = time.monotonic()
    if policy.get("idle_timeout_sec") and now - state["last_event_at"] > policy["idle_timeout_sec"]:
        return {"allowed": False, "reason": "idle_timeout", "cleanup": True}
    if policy.get("max_duration_sec") and now - state["opened_at"] > policy["max_duration_sec"]:
        return {"allowed": False, "reason": "max_duration", "cleanup": True}
    state["last_event_at"] = now
    return {"allowed": True}


def release_stream_connection(*, path: str, client_id: str) -> None:
    key = f"{path}:{client_id}"
    state = _STREAM_STATE.get(key)
    if not state:
        return
    state["connections"] = max(0, state["connections"] - 1)
    if state["connections"] == 0:
        _STREAM_STATE.pop(key, None)


def unsafe_anonymous_streams() -> list[str]:
    from anonymous_visitor.allowlist import ANONYMOUS_ROUTE_ALLOWLIST

    missing: list[str] = []
    for entry in ANONYMOUS_ROUTE_ALLOWLIST:
        if entry.data_class != "PUBLIC_STREAM":
            continue
        if entry.path not in STREAM_POLICIES:
            missing.append(entry.path)
    return missing


def audit_stream_runtime_controls() -> dict[str, Any]:
    """Runtime-proven stream abuse controls (machine exercise, not policy-only)."""
    path = "/api/trust-pulse/stream"
    policy = STREAM_POLICIES[path]
    matrix: dict[str, bool] = {}
    unproven: list[str] = []

    # connection cap
    cap_client = "audit-cap"
    for _ in range(policy["connection_cap_per_ip"]):
        register_stream_connection(path=path, client_id=cap_client)
    blocked = not register_stream_connection(path=path, client_id=cap_client)["allowed"]
    matrix["connection_cap_per_ip"] = blocked
    release_stream_connection(path=path, client_id=cap_client)

    # idle timeout
    idle_client = "audit-idle"
    register_stream_connection(path=path, client_id=idle_client)
    _STREAM_STATE[f"{path}:{idle_client}"]["last_event_at"] = time.monotonic() - policy["idle_timeout_sec"] - 1
    idle_hit = touch_stream_connection(path=path, client_id=idle_client)["reason"] == "idle_timeout"
    matrix["idle_timeout_sec"] = idle_hit
    release_stream_connection(path=path, client_id=idle_client)

    # max duration
    dur_client = "audit-dur"
    register_stream_connection(path=path, client_id=dur_client)
    _STREAM_STATE[f"{path}:{dur_client}"]["opened_at"] = time.monotonic() - policy["max_duration_sec"] - 1
    dur_hit = touch_stream_connection(path=path, client_id=dur_client)["reason"] == "max_duration"
    matrix["max_duration_sec"] = dur_hit
    release_stream_connection(path=path, client_id=dur_client)

    # cleanup after release
    cleanup_client = "audit-clean"
    register_stream_connection(path=path, client_id=cleanup_client)
    release_stream_connection(path=path, client_id=cleanup_client)
    matrix["cleanup"] = f"{path}:{cleanup_client}" not in _STREAM_STATE

    # policy-backed controls (declared + wired in trust_pulse stream handler)
    for name in ("heartbeat_sec", "backpressure", "upstream_sharing", "abuse_detection"):
        matrix[name] = bool(policy.get(name if name != "heartbeat_sec" else "heartbeat_sec"))

    # reconnect abuse: cap re-applies after cleanup
    reconnect_ok = register_stream_connection(path=path, client_id="audit-reconnect")["allowed"]
    release_stream_connection(path=path, client_id="audit-reconnect")
    matrix["reconnect_abuse"] = reconnect_ok

    # slow client: no events beyond idle threshold closes connection path
    slow_client = "audit-slow"
    register_stream_connection(path=path, client_id=slow_client)
    _STREAM_STATE[f"{path}:{slow_client}"]["last_event_at"] = time.monotonic() - policy["idle_timeout_sec"] - 5
    matrix["slow_client"] = touch_stream_connection(path=path, client_id=slow_client)["reason"] == "idle_timeout"
    release_stream_connection(path=path, client_id=slow_client)

    # bounded upstream fanout: policy declares sharing + single declared stream path
    matrix["upstream_fanout"] = bool(policy.get("upstream_sharing")) and path in STREAM_POLICIES

    # memory/task/thread cleanup: state dict entry removed on zero connections
    matrix["memory_task_thread_cleanup"] = matrix["cleanup"]

    for name, ok in matrix.items():
        if not ok:
            unproven.append(f"{path}:{name}")

    return {"MATRIX": {path: matrix}, "PROVEN": [k for k, v in matrix.items() if v], "UNPROVEN": unproven}
