"""Capability Explorer — discovery surface over cap646 SSOT (spec §9, AIE-008)."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.trust_dimensions import TrustDimensionVector


def _catalog_rows(limit: int = 50) -> list[dict[str, Any]]:
    from cap646.catalog import load_catalog

    return load_catalog()[:limit]


def explorer_card(row: dict[str, Any], *, tier: str = "free") -> dict[str, Any]:
    trust = TrustDimensionVector.from_payload(row)
    cap_id = int(row.get("id") or 0)
    return {
        "canonical_id": cap_id,
        "name": row.get("capability") or row.get("name") or f"cap-{cap_id}",
        "one_line_purpose": row.get("description") or row.get("purpose") or "",
        "when_to_use": row.get("when_to_use") or "Use when the decision context matches this capability.",
        "taxonomy": {
            "category": row.get("category") or row.get("domain") or "general",
            "asset": row.get("asset") or "*",
            "chain": row.get("chain") or "*",
            "horizon": row.get("horizon") or "intraday",
        },
        "tier": tier,
        "api_availability": row.get("api_availability") or "catalog",
        "freshness": trust.freshness,
        "coverage": trust.coverage,
        "assurance": trust.assurance,
        "methodology_maturity": trust.methodology_maturity,
        "limitations": row.get("limitations") or [],
        "lineage_ref": f"cap646:{cap_id}",
        "actions": ["open", "add_to_my_stack", "use_in_playbook", "create_alert"],
        "trust_dimensions": trust.to_dict(),
        "ssot_source": "cap646/catalog.py",
    }


def list_explorer_cards(limit: int = 24) -> list[dict[str, Any]]:
    return [explorer_card(r) for r in _catalog_rows(limit=limit)]


def search_explorer(
    *,
    query: str = "",
    category: str | None = None,
    limit: int = 24,
) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    cards = list_explorer_cards(limit=200)
    if category:
        cards = [c for c in cards if str(c["taxonomy"].get("category", "")).lower() == category.lower()]
    if q:
        cards = [
            c
            for c in cards
            if q in c["name"].lower() or q in c["one_line_purpose"].lower() or q in c["when_to_use"].lower()
        ]
    return cards[:limit]
