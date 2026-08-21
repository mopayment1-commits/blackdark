"""
Institutional API Gateway — ID574.

Single canonical gateway: authN/Z, quotas, audit, routing to capability runtime.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from cap646.entitlements import entitlement_engine

logger = logging.getLogger("BLACKDARK.Cap646Gateway")

_AUDIT: list[dict[str, Any]] = []
_MAX_AUDIT = 5000


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _audit(entry: dict[str, Any]) -> None:
    _AUDIT.append(entry)
    if len(_AUDIT) > _MAX_AUDIT:
        del _AUDIT[: len(_AUDIT) - _MAX_AUDIT]


async def gateway_execute(
    capability_id: int,
    *,
    user: dict[str, Any] | None = None,
    org_id: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ent = entitlement_engine.check(capability_id, user=user, org_id=org_id)
    if not ent.get("allowed"):
        _audit(
            {
                "ts": _utcnow(),
                "capability_id": capability_id,
                "allowed": False,
                "reason": ent.get("reason"),
                "user": (user or {}).get("email"),
                "org_id": org_id,
            }
        )
        return {
            "success": False,
            "gateway": "institutional_api_gateway",
            "capability_id": 574,
            "error": "entitlement_denied",
            "entitlement": ent,
        }

    result = await __import__("cap646.runtime", fromlist=["execute_capability"]).execute_capability(
        capability_id, user=user, org_id=org_id, params=params or {}
    )
    _audit(
        {
            "ts": _utcnow(),
            "capability_id": capability_id,
            "allowed": True,
            "success": result.get("success", True),
            "user": (user or {}).get("email"),
            "org_id": org_id,
        }
    )
    result["gateway"] = {
        "id": 574,
        "surface": "institutional_api_gateway",
        "entitlement": ent,
        "audited": True,
    }
    return result


def gateway_audit_log(limit: int = 100) -> list[dict[str, Any]]:
    return list(reversed(_AUDIT[-limit:]))
