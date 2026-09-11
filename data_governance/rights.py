"""Usage rights enforcement (DIG-001 / DIG-045)."""

from __future__ import annotations

from typing import Any

from data_governance.registry import get_source


def usage_rights_status() -> dict[str, Any]:
    from data_governance.registry import list_sources

    return {
        "package": "data_governance",
        "enforcement": "admission_gate",
        "sources_registered": len(list_sources()),
    }


def assert_usage_allowed(source_id: str, *, purpose: str = "analytics") -> dict[str, Any]:
    record = get_source(source_id)
    if record is None:
        return {"allowed": False, "reason": "unknown_source", "source_id": source_id}
    if not record.live_allowed and purpose == "live_trading":
        return {"allowed": False, "reason": "live_not_licensed", "source_id": source_id}
    return {
        "allowed": True,
        "source_id": source_id,
        "authority_level": record.authority_level,
        "license_class": record.license_class,
        "purpose": purpose,
    }
