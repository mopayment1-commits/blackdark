"""Base contract for Batch13 extension providers (647–650)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class ProviderConfig:
    capability_id: int
    provider_name: str
    enabled: bool = False
    timeout_seconds: float = 30.0
    max_retries: int = 2
    credential_ref: str | None = None


@dataclass
class ProviderStatus:
    capability_id: int
    provider_name: str
    ready: bool
    dependency_status: str
    blocker_type: str | None = None
    reason: str = ""
    provenance: dict[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


def validate_config_schema(config: dict[str, Any], *, required: tuple[str, ...]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for key in required:
        if key not in config:
            errors.append(f"missing:{key}")
    if "timeout_seconds" in config:
        try:
            if float(config["timeout_seconds"]) <= 0:
                errors.append("timeout_seconds_must_be_positive")
        except (TypeError, ValueError):
            errors.append("timeout_seconds_invalid")
    return not errors, errors


def fail_closed_payload(
    cap_id: int,
    *,
    provider_name: str,
    reason: str,
    blocker_type: str = "vendor_license_or_infra",
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "capability_id": cap_id,
        "provider": provider_name,
        "classification": "EXTERNAL_DEPENDENCY_BLOCKED",
        "blocker_type": blocker_type,
        "reason": reason,
        "dependency_status": "blocked",
        "internal_action": "none — requires external provisioning",
        "analysis_only": True,
        "no_execution": True,
        "provenance": provenance or {},
    }
