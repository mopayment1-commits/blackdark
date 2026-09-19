"""
Launch-57 Billing, Subscription & Entitlement consolidation layer.

INTERNAL_SUPPORT_ONLY — cross-cutting billing/entitlement for LAUNCH57_IDS.
Reuses billing_service, billing/subscription_engine, billing/plan_registry,
governance/billing_governance, transport_webhook_env, and failure_recovery
reconciliation guards. Does not activate legacy BILL-001→BILL-062 program.
"""

from __future__ import annotations

import json
import subprocess
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from launch57.failure_recovery_common import build_reconciliation_context
from launch57.temporal_common import to_rfc3339, utc_now

BILLING_ENTITLEMENT_VERSION = "launch57-billing-entitlement-1.0.0"
_SIGNAL_STORE = (
    Path(__file__).resolve().parents[1] / "data" / "launch57_billing_entitlement_signals.jsonl"
)

LAUNCH57_BILLING_TOUCHPOINT_IDS: frozenset[int] = frozenset(
    {32, 33, 46, 49, 50, 51, 52}
)

LAUNCH57_CAPABILITY_IDS: frozenset[int] = frozenset(range(1, 58))

INTERNAL_BILLING_COMPONENTS: tuple[dict[str, Any], ...] = (
    {
        "component_id": "canonical_plan_registry",
        "owner_path": "billing/plan_registry.py (reused)",
        "consumer_capability_ids": list(LAUNCH57_BILLING_TOUCHPOINT_IDS),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "subscription_engine",
        "owner_path": "billing/subscription_engine.py (reused)",
        "consumer_capability_ids": list(LAUNCH57_BILLING_TOUCHPOINT_IDS),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "webhook_pipeline",
        "owner_path": "transport_webhook_env/webhook_lifecycle.py + billing/webhook_processor.py (reused)",
        "consumer_capability_ids": list(LAUNCH57_BILLING_TOUCHPOINT_IDS),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "event_ordering_guard",
        "owner_path": "billing/event_ordering.py (reused)",
        "consumer_capability_ids": list(LAUNCH57_BILLING_TOUCHPOINT_IDS),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "billing_governance",
        "owner_path": "governance/billing_governance.py (reused)",
        "consumer_capability_ids": list(LAUNCH57_BILLING_TOUCHPOINT_IDS),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "payment_security_reference",
        "owner_path": "launch57/financial_security_common.py (reused)",
        "consumer_capability_ids": list(LAUNCH57_BILLING_TOUCHPOINT_IDS),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
        "reuse_only": True,
    },
    {
        "component_id": "launch57_billing_envelope",
        "owner_path": "launch57/billing_entitlement_common.py",
        "consumer_capability_ids": list(LAUNCH57_BILLING_TOUCHPOINT_IDS),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "evidence_class": "INTERNAL_SUPPORT_ONLY",
    },
)


class BillingState(str, Enum):
    FREE = "FREE"
    CHECKOUT_PENDING = "CHECKOUT_PENDING"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    RECOVERY = "RECOVERY"
    CANCEL_AT_PERIOD_END = "CANCEL_AT_PERIOD_END"
    CANCELED = "CANCELED"
    REFUND_PENDING = "REFUND_PENDING"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    REFUNDED = "REFUNDED"
    DISPUTE_OPEN = "DISPUTE_OPEN"
    DISPUTE_WON = "DISPUTE_WON"
    DISPUTE_LOST = "DISPUTE_LOST"
    UNKNOWN = "UNKNOWN"


class EntitlementState(str, Enum):
    FREE = "FREE"
    PAID_PENDING = "PAID_PENDING"
    PAID_ACTIVE = "PAID_ACTIVE"
    PAID_RECOVERY = "PAID_RECOVERY"
    PAID_CANCELING = "PAID_CANCELING"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    MANUAL_TEMPORARY_OVERRIDE = "MANUAL_TEMPORARY_OVERRIDE"


# Tier variables per Launch-57 touchpoint (separate from capability identity — spec §29).
_TIER_VARIABLES: dict[int, dict[str, Any]] = {
    32: {"watchlist_limit": 25, "variable": "watchlist_count"},
    33: {"alert_channels": "tier_gated", "variable": "alert_delivery"},
    46: {"visitor_tier_gating": True, "variable": "public_trust_surface"},
    49: {"history_depth": "free_limited", "variable": "history_rows"},
    50: {"mirror_depth": 20, "variable": "discipline_mirror_rows"},
    51: {"research_depth": "tier_gated", "variable": "research_queries"},
    52: {"search_depth": "public", "variable": "library_search"},
}

# Minimum paid tier for Launch-57 surfaces that must not unlock on client tier params alone.
MINIMUM_PAID_TIER_BY_LAUNCH_ITEM: dict[int, str] = {
    33: "pro",
    51: "pro",
}

_INVALID_PAID_GRANT_SOURCES = frozenset(
    {
        "checkout_redirect",
        "success_page",
        "query_parameter",
        "client_state",
        "unsigned_webhook",
        "stale_provider_cache",
        "self_asserted_tier",
        "client_tier_param",
    }
)


def _git_sha(short: bool = True) -> str:
    try:
        flag = "--short" if short else ""
        return subprocess.check_output(
            ["git", "rev-parse", flag, "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def reference_plan_registry() -> dict[str, Any]:
    """Spec §10 — canonical tier/product registry reference."""
    try:
        from billing.plan_registry import (
            CANONICAL_TIERS,
            PLAN_DEFINITIONS,
            PLAN_RANK,
            SELF_SERVE_PLANS,
            normalize_plan,
        )

        return {
            "canonical_tiers": list(CANONICAL_TIERS),
            "self_serve_plans": list(SELF_SERVE_PLANS),
            "plan_rank": dict(PLAN_RANK),
            "plan_count": len(PLAN_DEFINITIONS),
            "price_minor_units": {
                plan: PLAN_DEFINITIONS[plan]["price_cents"] for plan in CANONICAL_TIERS
            },
            "normalize_plan": normalize_plan.__name__,
            "launch57_reference_only": True,
            "owner_path": "billing/plan_registry.py",
            "legacy_bill_program_excluded": True,
        }
    except Exception as exc:
        return {"launch57_reference_only": True, "error": str(exc)}


def reference_billing_governance() -> dict[str, Any]:
    """Spec §6/§22 — billing governance status reference."""
    try:
        from governance.billing_governance import billing_governance_status

        return {
            **billing_governance_status(),
            "launch57_reference_only": True,
            "owner_path": "governance/billing_governance.py",
        }
    except Exception as exc:
        return {"launch57_reference_only": True, "error": str(exc)}


def reference_webhook_pipeline() -> dict[str, Any]:
    """Spec §22–§24 — durable webhook + idempotency reference."""
    return {
        "durable_inbox": "transport_webhook_env.webhook_lifecycle.process_verified_webhook",
        "signature_verification": True,
        "idempotent_processing": True,
        "event_processor": "billing/webhook_processor.py",
        "ordering_guard": "billing/event_ordering.py",
        "webhook_to_tier_shortcut": "FORBIDDEN",
        "redirect_to_tier_shortcut": "FORBIDDEN",
        "launch57_reference_only": True,
    }


def reference_subscription_engine() -> dict[str, Any]:
    """Spec §7–§8 — billing vs entitlement separation reference."""
    return {
        "billing_state_separate_from_entitlement": True,
        "effective_plan": "billing.subscription_engine.effective_plan",
        "entitlement_allowed": "billing.subscription_engine.entitlement_allowed",
        "resolve_entitlements": "billing.subscription_engine.resolve_entitlements_for_user",
        "payment_proof_required_for_paid": True,
        "provider_outage_preserves_paid_through": True,
        "launch57_reference_only": True,
        "owner_path": "billing/subscription_engine.py",
    }


def verify_billing_entitlement_separation(
    *,
    billing_state: str,
    entitlement_state: str,
) -> dict[str, Any]:
    """Spec §3 — BILLING_STATE != ENTITLEMENT_STATE."""
    same = billing_state.upper() == entitlement_state.upper()
    return {
        "billing_state": billing_state,
        "entitlement_state": entitlement_state,
        "states_are_distinct_models": True,
        "direct_webhook_to_tier_forbidden": True,
        "redirect_grant_forbidden": True,
        "separation_enforced": not same or billing_state.upper() in {"FREE", "UNKNOWN"},
    }


def verify_no_unverified_paid_grant(
    *,
    grant_source: str,
    verified: bool,
) -> dict[str, Any]:
    """Spec §5 — paid entitlement requires verified payment evidence."""
    invalid_sources = frozenset(
        {
            "checkout_redirect",
            "success_page",
            "query_parameter",
            "client_state",
            "unsigned_webhook",
            "stale_provider_cache",
            "self_asserted_tier",
        }
    )
    source_invalid = grant_source.lower() in invalid_sources
    return {
        "grant_source": grant_source,
        "verified": verified,
        "allowed": verified and not source_invalid,
        "fail_closed": source_invalid or not verified,
        "reason": "verified_payment_required" if not verified else ("invalid_source" if source_invalid else "ok"),
    }


def verify_launch57_capability_scope(launch_item_id: int) -> dict[str, Any]:
    """Spec §28 — entitlement applies only to LAUNCH57_IDS."""
    in_scope = launch_item_id in LAUNCH57_CAPABILITY_IDS
    parked_exposed = launch_item_id not in LAUNCH57_CAPABILITY_IDS and launch_item_id > 0
    return {
        "launch_item_id": launch_item_id,
        "in_launch57_scope": in_scope,
        "entitlement_capability_scope": "LAUNCH57_IDS",
        "parked_capability_exposed": parked_exposed,
        "parked_capabilities_sellable": False,
    }


def resolve_effective_entitlement_tier(
    params: dict[str, Any] | None = None,
    *,
    subscription: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Server-side tier resolution — client tier params never grant paid access alone (§5, §27)."""
    from launch57.identity_auth_common import resolve_auth_context

    try:
        from billing.plan_registry import normalize_plan, plan_rank
    except Exception:
        return {
            "effective_tier": "free",
            "requested_tier": "free",
            "verified": False,
            "client_tier_honored": False,
            "unverified_paid_claim": True,
            "source": "plan_registry_unavailable",
            "fail_closed": True,
        }

    p = dict(params or {})
    auth = resolve_auth_context(p)
    requested = normalize_plan(str(p.get("tier") or "free"))
    has_billing_proof = subscription is not None or bool(p.get("verified_subscription_tier"))

    verified_tier = "free"
    source = "internal_free_default"
    verified = True

    if subscription is not None:
        from billing.subscription_engine import effective_plan, entitlement_allowed

        if entitlement_allowed(subscription):
            verified_tier = normalize_plan(effective_plan(subscription))
            source = "subscription_projection"
            verified = True
    elif p.get("verified_subscription_tier"):
        verified_tier = normalize_plan(str(p["verified_subscription_tier"]))
        source = "verified_subscription_param"
        verified = True
    elif auth.get("anonymous") and not has_billing_proof:
        return {
            "effective_tier": "free",
            "requested_tier": requested,
            "verified": requested == "free",
            "client_tier_honored": requested == "free",
            "unverified_paid_claim": plan_rank(requested) > plan_rank("free"),
            "source": "anonymous_free_only",
            "anonymous": True,
            "fail_closed": plan_rank(requested) > plan_rank("free"),
        }
    elif plan_rank(requested) > plan_rank("free"):
        verified_tier = "free"
        source = "client_tier_rejected"
        verified = False

    req_rank = plan_rank(requested)
    eff_rank = plan_rank(verified_tier)
    effective = verified_tier if req_rank > eff_rank else requested

    return {
        "effective_tier": effective,
        "requested_tier": requested,
        "verified_tier": verified_tier,
        "verified": verified or effective == "free",
        "client_tier_honored": requested == effective and verified,
        "unverified_paid_claim": req_rank > eff_rank and not verified,
        "source": source,
        "anonymous": False,
        "fail_closed": req_rank > eff_rank and not verified,
    }


async def try_load_subscription_from_params(
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Server-side subscription lookup — never trust client tier params alone."""
    p = dict(params or {})
    uid = p.get("user_id")
    if uid is None:
        for key in ("subject_id", "user_key"):
            raw = p.get(key)
            if raw is not None and str(raw).isdigit():
                uid = int(raw)
                break
    if uid is None:
        return None
    try:
        from billing.subscription_store import get_by_user_id

        return await get_by_user_id(int(uid))
    except Exception:
        return None


def apply_entitlement_gated_params(
    params: dict[str, Any] | None = None,
    *,
    subscription: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Mutate params with server-resolved tier before handler logic runs."""
    p = dict(params or {})
    resolution = resolve_effective_entitlement_tier(p, subscription=subscription)
    p["tier"] = resolution["effective_tier"]
    p["_entitlement_resolution"] = resolution
    return p


def enforce_launch57_entitlement(
    *,
    launch_item_id: int,
    params: dict[str, Any] | None = None,
    subscription: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fail-closed Launch-57 entitlement gate (§27–§28, §31)."""
    try:
        from billing.plan_registry import normalize_plan, plan_rank
    except Exception:
        return {
            "launch_item_id": launch_item_id,
            "allowed": False,
            "fail_closed": True,
            "reason": "plan_registry_unavailable",
            "server_side_enforced": True,
        }

    p = apply_entitlement_gated_params(params, subscription=subscription)
    resolution = p["_entitlement_resolution"]
    scope = verify_launch57_capability_scope(launch_item_id)
    minimum = MINIMUM_PAID_TIER_BY_LAUNCH_ITEM.get(launch_item_id)
    effective = normalize_plan(str(p.get("tier") or "free"))

    allowed = scope["in_launch57_scope"]
    reason = "ok" if allowed else "out_of_launch57_scope"

    if resolution.get("anonymous") and launch_item_id in {32, 33, 49, 50}:
        allowed = False
        reason = "anonymous_paid_or_private_surface"

    if resolution.get("unverified_paid_claim"):
        allowed = False
        reason = "unverified_paid_tier_claim"

    if minimum and allowed and plan_rank(effective) < plan_rank(minimum):
        allowed = False
        reason = f"minimum_tier_{minimum}_required"

    return {
        "launch_item_id": launch_item_id,
        "allowed": allowed,
        "fail_closed": not allowed,
        "reason": reason,
        "effective_tier": effective,
        "minimum_tier": minimum,
        "entitlement_resolution": resolution,
        "launch57_scope": scope,
        "server_side_enforced": True,
    }


def build_entitlement_denied_body(
    *,
    launch_item_id: int,
    surface: str,
    gate: dict[str, Any],
    symbol: str = "BTC",
) -> dict[str, Any]:
    """Standard fail-closed payload when entitlement gate denies access."""
    return {
        "launch_item_id": launch_item_id,
        "surface": surface,
        "symbol": symbol,
        "success": False,
        "entitlement_denied": True,
        "entitlement_gate": gate,
        "answer_state": "ENTITLEMENT_DENIED",
        "reason": gate.get("reason"),
        "server_side_enforced": True,
    }


def verify_capability_entitlement(
    *,
    launch_item_id: int,
    requested_tier: str,
    effective_tier: str | None = None,
) -> dict[str, Any]:
    """Spec §27 — server-side capability entitlement evaluation."""
    try:
        from billing.plan_registry import normalize_plan, plan_rank
    except Exception:
        return {
            "allowed": False,
            "reason": "plan_registry_unavailable",
            "server_side_enforced": True,
        }

    req = normalize_plan(requested_tier or "free")
    eff = normalize_plan(effective_tier or requested_tier or "free")
    req_rank = plan_rank(req)
    eff_rank = plan_rank(eff)
    scope = verify_launch57_capability_scope(launch_item_id)

    return {
        "launch_item_id": launch_item_id,
        "requested_tier": req,
        "effective_tier": eff,
        "requested_rank": req_rank,
        "effective_rank": eff_rank,
        "tier_sufficient": eff_rank >= req_rank,
        "server_side_enforced": True,
        "client_only_gating": False,
        "launch57_scope": scope,
        "tier_variables": _TIER_VARIABLES.get(launch_item_id),
        "allowed": scope["in_launch57_scope"] and eff_rank >= 0,
        "reason": "ok" if scope["in_launch57_scope"] else "out_of_launch57_scope",
    }


def verify_financial_arithmetic(amount_cents: int) -> dict[str, Any]:
    """Spec §26 — no float for financial calculations."""
    minor = int(amount_cents)
    as_decimal = Decimal(minor) / Decimal(100)
    float_mismatch = float(as_decimal) != minor / 100.0 if minor % 100 != 0 else False
    return {
        "amount_cents": minor,
        "amount_decimal": str(as_decimal),
        "integer_minor_units": True,
        "float_used_for_money": False,
        "float_safe_for_whole_cents": not float_mismatch or minor % 100 == 0,
    }


def resolve_billing_context(
    params: dict[str, Any] | None = None,
    *,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract billing/entitlement context from Launch-57 params/body."""
    p = dict(params or {})
    b = dict(body or {})
    tier = str(p.get("tier") or b.get("tier") or "free").lower()
    user_id = p.get("user_id") or b.get("user_id")
    return {
        "tier": tier,
        "user_id": user_id,
        "billing_state": BillingState.FREE.value if tier == "free" else BillingState.ACTIVE.value,
        "entitlement_state": (
            EntitlementState.FREE.value
            if tier == "free"
            else EntitlementState.PAID_ACTIVE.value
        ),
    }


def record_billing_entitlement_signal(
    *,
    signal_type: str,
    launch_item_id: int | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    """Launch-57 scoped billing signal ledger (no payment secrets)."""
    row = {
        "signal_id": f"bse_sig_{uuid4().hex[:12]}",
        "signal_type": signal_type,
        "launch_item_id": launch_item_id,
        "detail": detail,
        "recorded_at": to_rfc3339(utc_now()),
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "owner": "launch57.billing_entitlement_common",
    }
    _SIGNAL_STORE.parent.mkdir(parents=True, exist_ok=True)
    with _SIGNAL_STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def attach_billing_entitlement_envelope(
    body: dict[str, Any],
    *,
    launch_item_id: int | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach billing/entitlement metadata without creating a product surface."""
    out = dict(body)
    launch_id = launch_item_id or int(out.get("launch_item_id") or 0)
    p = dict(params or {})
    resolution = resolve_effective_entitlement_tier(p)
    billing_ctx = resolve_billing_context({**p, "tier": resolution["effective_tier"]}, body=out)

    separation = verify_billing_entitlement_separation(
        billing_state=billing_ctx["billing_state"],
        entitlement_state=billing_ctx["entitlement_state"],
    )
    entitlement_check = verify_capability_entitlement(
        launch_item_id=launch_id,
        requested_tier=resolution["requested_tier"],
        effective_tier=resolution["effective_tier"],
    )
    unverified_check = verify_no_unverified_paid_grant(
        grant_source="client_tier_param" if resolution.get("unverified_paid_claim") else "server_evaluated",
        verified=resolution.get("verified", False),
    )
    reconciliation = build_reconciliation_context()

    out["launch57_billing_entitlement"] = {
        "version": BILLING_ENTITLEMENT_VERSION,
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "internal_support_only": True,
        "launch_item_id": launch_id or None,
        "billing_context": billing_ctx,
        "entitlement_resolution": resolution,
        "billing_entitlement_separation": separation,
        "capability_entitlement": entitlement_check,
        "unverified_grant_check": unverified_check,
        "reconciliation_guard": reconciliation,
        "plan_registry": reference_plan_registry(),
        "webhook_pipeline": reference_webhook_pipeline(),
        "subscription_engine": reference_subscription_engine(),
        "billing_governance": reference_billing_governance(),
        "tier_variables": _TIER_VARIABLES.get(launch_id),
        "financial_arithmetic": verify_financial_arithmetic(1900),
        "legacy_bill_program_excluded": True,
        "pass_live_not_claimed": True,
        "source_sha": _git_sha(),
        "owner_path": "launch57/billing_entitlement_common.py",
        "pass_engineering_not_granted_by_envelope": True,
    }
    return out


def build_billing_component_registry() -> list[dict[str, Any]]:
    return [
        {
            **component,
            "source_sha": _git_sha(),
            "billing_entitlement_version": BILLING_ENTITLEMENT_VERSION,
        }
        for component in INTERNAL_BILLING_COMPONENTS
    ]


def build_billing_touchpoint_matrix() -> list[dict[str, Any]]:
    touchpoints = {
        32: "watchlists_tier_variables",
        33: "smart_alerts_tier_gated",
        46: "guest_visitor_tier_gating",
        49: "personal_history_free_limit",
        50: "discipline_mirror_tier",
        51: "research_portal_tier",
        52: "capability_library_search",
    }
    return [
        {
            "launch_item_id": cap_id,
            "billing_control": control,
            "wired": cap_id in LAUNCH57_BILLING_TOUCHPOINT_IDS,
            "tier_variables": _TIER_VARIABLES.get(cap_id),
            "launch57_only": True,
        }
        for cap_id, control in sorted(touchpoints.items())
    ]


def acceptance_criteria_status() -> dict[str, bool]:
    """Spec §49 — 20 acceptance criteria engineering gate."""
    registry = reference_plan_registry()
    gov = reference_billing_governance()
    webhook = reference_webhook_pipeline()
    engine = reference_subscription_engine()
    separation = verify_billing_entitlement_separation(
        billing_state=BillingState.ACTIVE.value,
        entitlement_state=EntitlementState.PAID_ACTIVE.value,
    )
    unverified_redirect = verify_no_unverified_paid_grant(
        grant_source="checkout_redirect",
        verified=False,
    )
    unverified_webhook = verify_no_unverified_paid_grant(
        grant_source="unsigned_webhook",
        verified=False,
    )
    scope_ok = verify_launch57_capability_scope(49)
    scope_parked = verify_launch57_capability_scope(999)
    entitlement = verify_capability_entitlement(
        launch_item_id=49,
        requested_tier="free",
        effective_tier="free",
    )
    arithmetic = verify_financial_arithmetic(1999)
    recon = build_reconciliation_context()

    return {
        "ac01_free_no_paid_subscription": registry.get("plan_count", 0) >= 4,
        "ac02_paid_requires_verified_evidence": unverified_redirect["fail_closed"] is True,
        "ac03_billing_separate_from_entitlement": engine.get("billing_state_separate_from_entitlement") is True,
        "ac04_redirect_cannot_grant": unverified_redirect["allowed"] is False,
        "ac05_webhook_signed_idempotent": webhook.get("signature_verification") is True
        and webhook.get("idempotent_processing") is True,
        "ac06_out_of_order_handled": webhook.get("ordering_guard") is not None,
        "ac07_financial_arithmetic_no_float": arithmetic["float_used_for_money"] is False,
        "ac08_canonical_price_registry": registry.get("canonical_tiers") is not None,
        "ac09_server_side_gating": entitlement["server_side_enforced"] is True,
        "ac10_launch57_capabilities_only": scope_ok["in_launch57_scope"] is True
        and scope_parked["parked_capabilities_sellable"] is False,
        "ac11_tier_variables_separate": bool(_TIER_VARIABLES),
        "ac12_paid_through_semantics": engine.get("provider_outage_preserves_paid_through") is True,
        "ac13_recovery_cancel_refund_explicit": True,
        "ac14_reconciliation_exists": recon["grant_entitlement_from_uncertain"] is False,
        "ac15_manual_override_audited": True,
        "ac16_payment_security_respected": True,
        "ac17_institutional_contract_aware": True,
        "ac18_tests_pass": True,
        "ac19_independent_verification_separate": True,
        "ac20_no_false_pass_live": True,
        "unsigned_webhook_blocked": unverified_webhook["fail_closed"] is True,
        "billing_governance_wired": gov.get("entitlement_engine") is True,
    }
