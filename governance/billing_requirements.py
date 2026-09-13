"""BILL-001→061 billing requirement spine (BGS-005)."""

from __future__ import annotations

from typing import Any

from governance.billing_governance import billing_governance_status
from governance.spine_base import build_catalog, build_summary, verify_all_requirements, verify_requirement

_PREFIX = "BILL-"
_BGS = "BGS-005"

_IMPLEMENTED = frozenset(f"{_PREFIX}{n:03d}" for n in range(1, 21))
_PARTIAL = frozenset(f"{_PREFIX}{n:03d}" for n in range(21, 63))


def bill_catalog() -> list[dict[str, Any]]:
    return build_catalog(prefix=_PREFIX, bgs=_BGS, implemented=_IMPLEMENTED, partial=_PARTIAL, max_num=62)


def bill_summary() -> dict[str, Any]:
    rows = bill_catalog()
    return build_summary(domain="BILL", bgs=_BGS, rows=rows, honest_min_implemented=10, strict_min_implemented=30)


def verify_bill_requirement(requirement_id: str) -> dict[str, Any]:
    return verify_requirement(bill_catalog(), requirement_id)


def verify_bill_runtime() -> dict[str, Any]:
    status = billing_governance_status()
    return {
        "billing_configured": status.get("billing_configured"),
        "webhook_dedup_durable": status.get("webhook_dedup_durable"),
        "plans_ok": status.get("plans_ok"),
        "all_requirements": verify_all_requirements(bill_catalog()),
    }
