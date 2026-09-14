"""ID-001→072 identity requirement spine (BGS-006)."""

from __future__ import annotations

from typing import Any

from governance.identity_governance import identity_governance_status, verify_password_policy
from governance.spine_base import build_catalog, build_summary, verify_all_requirements, verify_requirement

_PREFIX = "ID-"
_BGS = "BGS-006"

_IMPLEMENTED = frozenset(f"{_PREFIX}{n:03d}" for n in range(1, 16))
_PARTIAL = frozenset(f"{_PREFIX}{n:03d}" for n in range(16, 73))


def id_catalog() -> list[dict[str, Any]]:
    return build_catalog(prefix=_PREFIX, bgs=_BGS, implemented=_IMPLEMENTED, partial=_PARTIAL, max_num=72)


def id_summary() -> dict[str, Any]:
    rows = id_catalog()
    return build_summary(domain="ID", bgs=_BGS, rows=rows, honest_min_implemented=10, strict_min_implemented=30)


def verify_id_requirement(requirement_id: str) -> dict[str, Any]:
    return verify_requirement(id_catalog(), requirement_id)


def verify_id_runtime() -> dict[str, Any]:
    status = identity_governance_status()
    return {
        "mfa_available": status.get("mfa_available"),
        "org_tenant_isolation": status.get("org_tenant_isolation"),
        "password_policy": verify_password_policy(),
        "all_requirements": verify_all_requirements(id_catalog()),
    }
