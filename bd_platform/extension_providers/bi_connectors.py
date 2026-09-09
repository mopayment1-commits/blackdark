"""BI Connectors provider contract (#650)."""

from __future__ import annotations

from typing import Any

from bd_platform.extension_providers.base import ProviderStatus, fail_closed_payload, validate_config_schema

PROVIDER_NAME = "bi_connectors"
REQUIRED_CONFIG_KEYS = ("provider_name", "connector_type")


def default_config() -> dict[str, Any]:
    return {
        "provider_name": PROVIDER_NAME,
        "connector_type": "tableau",
        "enabled": False,
        "timeout_seconds": 30.0,
        "max_retries": 2,
        "credential_ref": None,
    }


def health_status(*, config: dict[str, Any] | None = None, external_reason: str = "") -> ProviderStatus:
    config = config or default_config()
    valid, errors = validate_config_schema(config, required=REQUIRED_CONFIG_KEYS)
    ready = bool(config.get("enabled")) and valid and bool(config.get("credential_ref"))
    return ProviderStatus(
        capability_id=650,
        provider_name=PROVIDER_NAME,
        ready=ready,
        dependency_status="ready" if ready else "blocked",
        blocker_type=None if ready else "vendor_license_or_infra",
        reason=external_reason or (";".join(errors) if errors else "bi_connector_licenses_required"),
        provenance={"config_valid": valid, "connector_type": config.get("connector_type")},
    )


def execute_local_contract(*, symbol: str = "BTC", config: dict[str, Any] | None = None, external_reason: str = "") -> dict[str, Any]:
    status = health_status(config=config, external_reason=external_reason)
    if status.ready:
        return {
            "ok": True,
            "capability_id": 650,
            "provider": PROVIDER_NAME,
            "symbol": symbol.upper(),
            "dependency_status": "ready",
            "connector_type": (config or default_config()).get("connector_type"),
            "analysis_only": True,
            "no_execution": True,
        }
    return fail_closed_payload(
        650,
        provider_name=PROVIDER_NAME,
        reason=status.reason,
        provenance=status.provenance,
    )
