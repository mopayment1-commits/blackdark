"""Anonymous SSE/WebSocket policy — AV §20."""

from __future__ import annotations

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


def stream_policy(path: str) -> dict[str, Any] | None:
    return STREAM_POLICIES.get(path)


def validate_stream_path(path: str) -> dict[str, Any]:
    policy = stream_policy(path)
    if policy is None:
        return {"ok": False, "path": path, "allowed": False, "reason": "not_declared_public_stream"}
    return {"ok": True, "path": path, "allowed": True, "policy": policy}


def unsafe_anonymous_streams() -> list[str]:
    # All declared streams must have explicit policy entries.
    from anonymous_visitor.allowlist import ANONYMOUS_ROUTE_ALLOWLIST

    missing: list[str] = []
    for entry in ANONYMOUS_ROUTE_ALLOWLIST:
        if entry.data_class != "PUBLIC_STREAM":
            continue
        if entry.path not in STREAM_POLICIES:
            missing.append(entry.path)
    return missing
