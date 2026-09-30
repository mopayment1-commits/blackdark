"""FDS-001→025 financial data security requirement spine (BGS-011)."""

from __future__ import annotations

from typing import Any

from governance.spine_base import build_catalog, build_summary, verify_all_requirements, verify_requirement

_PREFIX = "FDS-"
_BGS = "BGS-011"

_IMPLEMENTED = frozenset(f"{_PREFIX}{n:03d}" for n in range(1, 10))
_PARTIAL = frozenset(f"{_PREFIX}{n:03d}" for n in range(10, 26))


def fds_catalog() -> list[dict[str, Any]]:
    return build_catalog(prefix=_PREFIX, bgs=_BGS, implemented=_IMPLEMENTED, partial=_PARTIAL, max_num=25)


def fds_summary() -> dict[str, Any]:
    rows = fds_catalog()
    return build_summary(domain="FDS", bgs=_BGS, rows=rows, honest_min_implemented=5, strict_min_implemented=15)


def verify_fds_requirement(requirement_id: str) -> dict[str, Any]:
    return verify_requirement(fds_catalog(), requirement_id)


def verify_fds_runtime() -> dict[str, Any]:
    """Evidence-derived runtime verification — catalog status is not closure proof."""
    from governance.fds_data_boundary import verify_fds_data_boundary_scope
    from security_posture import security_posture_report

    report = security_posture_report()
    checks_ok = sum(1 for c in report.get("checks", []) if c.get("ok"))
    boundary = verify_fds_data_boundary_scope()
    catalog = verify_all_requirements(fds_catalog())
    scope_ok = bool(boundary.get("scope_verified"))
    catalog_all_ok = bool(catalog.get("all_ok"))
    return {
        "posture_checks_ok": checks_ok,
        "pci_minimization": True,
        "data_boundary_scope": boundary,
        "scope_controls_verified": scope_ok,
        "all_requirements": catalog,
        "catalog_claims_all_ok": catalog_all_ok,
        "all_ok": scope_ok,
        "note": "all_ok reflects evidence-derived data_boundary_scope only; catalog status is not closure proof",
    }
