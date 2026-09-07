"""dbt Connector provider contract (#649)."""

from __future__ import annotations

from typing import Any

from bd_platform.extension_providers.base import ProviderStatus, fail_closed_payload, validate_config_schema

PROVIDER_NAME = "dbt_connector"
REQUIRED_CONFIG_KEYS = ("provider_name", "project_ref")


def default_config() -> dict[str, Any]:
    return {
        "provider_name": PROVIDER_NAME,
        "project_ref": "",
        "enabled": False,
        "timeout_seconds": 60.0,
        "max_retries": 1,
        "credential_ref": None,
    }


def health_status(*, config: dict[str, Any] | None = None, external_reason: str = "") -> ProviderStatus:
    config = config or default_config()
    valid, errors = validate_config_schema(config, required=REQUIRED_CONFIG_KEYS)
    ready = bool(config.get("enabled")) and valid and bool(config.get("credential_ref")) and bool(config.get("project_ref"))
    return ProviderStatus(
        capability_id=649,
        provider_name=PROVIDER_NAME,
        ready=ready,
        dependency_status="ready" if ready else "blocked",
        blocker_type=None if ready else "vendor_license_or_infra",
        reason=external_reason or (";".join(errors) if errors else "external_dbt_deployment_required"),
        provenance={"config_valid": valid, "project_ref": config.get("project_ref")},
    )


def execute_local_contract(*, symbol: str = "BTC", config: dict[str, Any] | None = None, external_reason: str = "") -> dict[str, Any]:
    status = health_status(config=config, external_reason=external_reason)
    if status.ready:
        return {
            "ok": True,
            "capability_id": 649,
            "provider": PROVIDER_NAME,
            "symbol": symbol.upper(),
            "dependency_status": "ready",
            "project_ref": (config or default_config()).get("project_ref"),
            "analysis_only": True,
            "no_execution": True,
        }
    return fail_closed_payload(
        649,
        provider_name=PROVIDER_NAME,
        reason=status.reason,
        provenance=status.provenance,
    )
