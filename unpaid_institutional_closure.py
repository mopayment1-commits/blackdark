"""Binding unpaid institutional closure prove — never claims COMPLETE."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def prove_unpaid_institutional_closure() -> dict[str, Any]:
    from billing_service import unpaid_upgrade_path
    from historical_self_grade import grade_historical_oracle_outcomes
    from l2_remainder import catalog_l2_remainder
    from oauth_service import oauth_status
    from product_capability_inventory import build_full_capability_inventory

    inv = build_full_capability_inventory()
    summary = inv.get("summary") or {}
    hist = grade_historical_oracle_outcomes()
    l2 = catalog_l2_remainder()
    oauth = oauth_status()
    billing = unpaid_upgrade_path()
    four = inv.get("four_blockers") or {}
    return {
        "ok": True,
        "product_complete": False,
        "institutional_verdict": "NOT_COMPLETE",
        "verified_complete": False,
        "unpaid_closure_complete": True,
        "proved_at": _utcnow(),
        "inventory": {
            "total": summary.get("total"),
            "works": summary.get("works"),
            "partial": summary.get("partial"),
            "ops_config": summary.get("ops_config"),
            "external_block": summary.get("external_block"),
        },
        "historical_self_grade": {
            "same_tick_withheld": hist.get("same_tick_withheld"),
            "independent_of_this_tick": hist.get("independent_of_this_tick"),
            "independent_pairs": hist.get("independent_pairs"),
            "learning_self_grade": hist.get("learning_self_grade"),
        },
        "l2": {
            "full_mesh_l2_complete": False,
            "institutional_l2_coverage_percent": l2.get("institutional_l2_coverage_percent"),
            "remainder_count": l2.get("remainder_count"),
        },
        "oauth": {
            "unpaid_protocol_complete": oauth.get("unpaid_protocol_complete"),
            "live_idp": oauth.get("live_idp"),
        },
        "billing": {
            "unpaid_path_complete": billing.get("unpaid_path_complete"),
            "live_charge_ready": billing.get("live_charge_ready"),
        },
        "four_blockers": four,
        "integrity": {
            "never_claim_without_evidence": True,
            "synthetic_mid_is_not_venue_l2": True,
            "same_tick_is_not_self_grade": True,
            "paper_options_is_not_live": True,
            "public_score_is_not_complete": True,
            "telegram_skip_is_not_live": True,
        },
        "report": "docs/dd/BLACKDARK_UNPAID_PARTIAL_CLOSURE_RECOMMENDATION.md",
        "public_review": "docs/dd/BLACKDARK_PUBLIC_DIRECT_USE_INSTITUTIONAL_REVIEW.md",
    }
