"""Cached public evidence-pack teaser (static JSON, no DB)."""

from __future__ import annotations

import copy
import os
import time
from typing import Any

EVIDENCE_PUBLIC_SUMMARY_CACHE_TTL_SEC = float(
    os.getenv("EVIDENCE_PUBLIC_SUMMARY_CACHE_SEC", "60")
)

_EVIDENCE_PUBLIC_SUMMARY_BODY: dict[str, Any] = {
    "product_thesis": (
        "Decision Intelligence + Proven Predictive Accuracy + "
        "Proprietary Labeled Market Corpus"
    ),
    "differentiators": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"],
    "public_endpoints": {
        "accuracy": "/api/oracle/accuracy/public",
        "accuracy_page": "/oracle-accuracy",
        "persona_demo": "/api/oracle/persona-clarity/demo",
        "half_life": "/api/oracle/half-life",
        "net_edge": "/api/oracle/net-edge-truth",
        "kill_rate": "/api/public/kill-rate",
        "committee_teaser": "/b2b/committee-one-pager",
    },
    "full_pack": "/api/due-diligence/evidence-pack",
    "access": "whale_or_admin",
    "constitution": "docs/PRODUCT_CONSTITUTION_AR.md",
}

_cache: tuple[float, dict[str, Any]] | None = None


def build_evidence_public_summary() -> dict[str, Any]:
    """Return a deep copy of the static public-summary payload."""
    return copy.deepcopy(_EVIDENCE_PUBLIC_SUMMARY_BODY)


def get_cached_evidence_public_summary() -> dict[str, Any]:
    global _cache
    now = time.monotonic()
    if _cache and (now - _cache[0]) < EVIDENCE_PUBLIC_SUMMARY_CACHE_TTL_SEC:
        return copy.deepcopy(_cache[1])
    body = build_evidence_public_summary()
    _cache = (now, body)
    return copy.deepcopy(body)


def warm_evidence_public_summary_cache() -> None:
    """Prime in-process cache at startup so first visitor avoids cold assembly."""
    get_cached_evidence_public_summary()
