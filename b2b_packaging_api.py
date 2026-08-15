"""Institutional packaging surfaces — white-label / SCIM / super-terminal status.

Honest status APIs: product_complete for codepath, human_ops for live IdP/domain.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def white_label_status() -> dict[str, Any]:
    import os

    custom_domain = (os.getenv("WHITE_LABEL_CUSTOM_DOMAIN") or "").strip()
    brand = (os.getenv("WHITE_LABEL_BRAND_NAME") or "").strip()
    return {
        "surface": "white_label",
        "generated_at": _utcnow(),
        "product_complete": True,
        "configured": bool(brand or custom_domain),
        "brand_name": brand or None,
        "custom_domain": custom_domain or None,
        "hosted_custom_domain_live": False,
        "note": (
            "White-label codepath ready. Hosted custom domain requires DNS + "
            "WHITE_LABEL_CUSTOM_DOMAIN on supportive-enchantment — never claimed live here."
        ),
        "api": "/api/b2b/white-label",
        "page": "/b2b",
    }


def scim_status() -> dict[str, Any]:
    from enterprise_sso import sso_status

    sso = sso_status()
    return {
        "surface": "scim",
        "generated_at": _utcnow(),
        "product_complete": True,
        "scim_ready": bool(sso.get("scim_ready")),
        "org_configured": bool(sso.get("org_configured")),
        "users_endpoint": "/api/scim/v2/Users",
        "note": (
            "SCIM list/filter stub is available for integration tests. "
            "Live IdP provisioning requires enterprise SSO secrets (HUMAN_OPS)."
        ),
        "sso": {
            "protocols": sso.get("protocols"),
            "env_oidc_ready": sso.get("env_oidc_ready"),
        },
        "api": "/api/institutional/scim/status",
    }


def scim_users(*, start_index: int = 1, count: int = 50) -> dict[str, Any]:
    """RFC 7644-ish list response — empty until an org IdP is wired."""
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": 0,
        "startIndex": start_index,
        "itemsPerPage": count,
        "Resources": [],
        "note": "SCIM Users stub — no live IdP directory connected.",
    }


def super_terminal_status() -> dict[str, Any]:
    return {
        "surface": "super_terminal",
        "generated_at": _utcnow(),
        "product_complete": True,
        "href": "/b2b#fund-terminal",
        "related": {
            "fund_terminal": "/api/fund/emerging-terminal",
            "dd_closure": "/api/institutional/dd-closure",
            "ha": "/api/institutional/ha",
        },
        "note": "Super terminal packs institutional surfaces; not a separate live trading venue.",
        "api": "/api/b2b/super-terminal",
    }
