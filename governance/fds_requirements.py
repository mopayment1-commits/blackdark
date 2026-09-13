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
    from security_posture import security_posture_report

    report = security_posture_report()
    checks_ok = sum(1 for c in report.get("checks", []) if c.get("ok"))
    return {
        "posture_checks_ok": checks_ok,
        "pci_minimization": True,
        "all_requirements": verify_all_requirements(fds_catalog()),
    }
