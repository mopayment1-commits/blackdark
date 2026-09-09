"""SEO/indexing policy — AV §23."""

from __future__ import annotations

from typing import Any

PUBLIC_INDEXABLE: frozenset[str] = frozenset(
    {
        "/",
        "/markets",
        "/methodology",
        "/accuracy",
        "/status",
        "/oracle-accuracy",
        "/capabilities",
        "/compliance",
        "/docs",
        "/docs/public",
        "/proof-arena",
        "/kill-rate",
    }
)

PRIVATE_NOINDEX_PREFIXES: tuple[str, ...] = (
    "/dashboard",
    "/account",
    "/billing",
    "/portfolio",
    "/settings",
    "/admin",
    "/api/",
)


def seo_policy_for_path(path: str) -> dict[str, Any]:
    p = path.split("?", 1)[0]
    if any(p == pref or p.startswith(pref) for pref in PRIVATE_NOINDEX_PREFIXES if pref != "/api/"):
        return {
            "path": p,
            "indexable": False,
            "robots": "noindex, nofollow",
            "canonical": None,
            "structured_data": None,
        }
    if p.startswith("/api/"):
        return {
            "path": p,
            "indexable": False,
            "robots": "noindex, nofollow",
            "canonical": None,
            "structured_data": "gated_api",
        }
    indexable = p in PUBLIC_INDEXABLE
    return {
        "path": p,
        "indexable": indexable,
        "robots": "index, follow" if indexable else "noindex, nofollow",
        "canonical": p if indexable else None,
        "structured_data": "WebPage" if indexable else None,
    }


def seo_policy_export() -> dict[str, Any]:
    return {
        "public_indexable": sorted(PUBLIC_INDEXABLE),
        "private_noindex_prefixes": list(PRIVATE_NOINDEX_PREFIXES),
        "server_side_gating": True,
        "no_cloaking": True,
    }
