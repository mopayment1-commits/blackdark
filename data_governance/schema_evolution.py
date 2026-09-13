"""Schema evolution controls (DIG-031)."""

from __future__ import annotations

from typing import Any

_SCHEMA_VERSION = "1.0"


def validate_schema_version(payload: dict[str, Any], *, surface: str) -> None:
    version = str(payload.get("schema_version") or _SCHEMA_VERSION)
    if version.split(".")[0] != _SCHEMA_VERSION.split(".")[0]:
        from blackdark.data_governance.runtime import GovernanceViolationError

        raise GovernanceViolationError(f"schema_version_incompatible:{version}")
