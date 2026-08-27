"""Tenant scope enforcement for institutional routes (D-06)."""

from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException, Request


def _tenant_enforcement_enabled() -> bool:
    return os.getenv("TENANT_SCOPE_ENFORCE", "true").lower() in {"1", "true", "yes"}


def resolve_tenant_id(request: Request) -> str | None:
    """Resolve tenant from header or org session (default public)."""
    header = (request.headers.get("X-Tenant-Id") or request.headers.get("X-Org-Id") or "").strip()
    if header:
        return header
    return request.headers.get("X-Blackdark-Tenant")


def assert_tenant_access(request: Request, resource_tenant: str | None) -> None:
    """Deny cross-tenant reads when enforcement enabled."""
    if not _tenant_enforcement_enabled():
        return
    caller = resolve_tenant_id(request)
    if not resource_tenant:
        return
    if not caller:
        return  # public read paths without tenant header
    if caller != resource_tenant:
        raise HTTPException(status_code=403, detail="tenant isolation violation")


def tenant_context(request: Request) -> dict[str, Any]:
    return {
        "tenant_id": resolve_tenant_id(request),
        "enforcement": _tenant_enforcement_enabled(),
    }
