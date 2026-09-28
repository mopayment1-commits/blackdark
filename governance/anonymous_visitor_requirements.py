"""AV-001→030 anonymous visitor requirement spine (BGS-012)."""

from __future__ import annotations

from typing import Any

from governance.anonymous_visitor_governance import anonymous_visitor_status
from governance.spine_base import build_catalog, build_summary, verify_all_requirements, verify_requirement

_PREFIX = "AV-"
_BGS = "BGS-012"

_IMPLEMENTED = frozenset(f"{_PREFIX}{n:03d}" for n in range(1, 10))
_PARTIAL = frozenset(f"{_PREFIX}{n:03d}" for n in range(10, 31))


def av_catalog() -> list[dict[str, Any]]:
    return build_catalog(prefix=_PREFIX, bgs=_BGS, implemented=_IMPLEMENTED, partial=_PARTIAL, max_num=30)


def av_summary() -> dict[str, Any]:
    rows = av_catalog()
    return build_summary(domain="AV", bgs=_BGS, rows=rows, honest_min_implemented=5, strict_min_implemented=15)


def verify_av_requirement(requirement_id: str) -> dict[str, Any]:
    return verify_requirement(av_catalog(), requirement_id)


def verify_av_runtime() -> dict[str, Any]:
    status = anonymous_visitor_status()
    return {
        "public_readiness": status.get("public_readiness"),
        "rate_limits": status.get("rate_limits"),
        "all_requirements": verify_all_requirements(av_catalog()),
    }
