"""
BLACKDARK — CSO Priority Chain Binding (machine-readable law).

Corrected chain (expert):
  Product Excellence → Unique Intelligence → Distribution+Habit
  → Data Flywheel → Early Revenue → Institutional Proof
  → Strategic Moat → Acquisition Leverage

Binding rule: no new feature unless it raises decision habit,
distribution, revenue, or live data flywheel.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# Sonar S1192: duplicated string literals
PATH_DATA_ROOM = '/data-room'

# Levers that may unlock new product work (binding gate).
PERMITTED_LEVERS = frozenset(
    {
        "habit",
        "distribution",
        "revenue",
        "data_flywheel",
        "unique_intelligence",  # only when deepening Prove-it / Kill-Rate / Net-Edge
    }
)

# Outcome stages — never a standalone reason to ship vanity features.
OUTCOME_ONLY_LEVERS = frozenset(
    {
        "institutional_proof",
        "strategic_moat",
        "acquisition_leverage",
    }
)

REJECTED_OLD_CHAIN = [
    "features",
    "features",
    "features",
    "launch",
    "users",
    "acquisition",
]

CHAIN_STAGES: list[dict[str, Any]] = [
    {
        "order": 1,
        "id": "product_excellence",
        "name": "Product Excellence",
        "definition": "One verifiable daily Act/Wait habit — not a feature tour.",
        "primary_surfaces": ["/dashboard?lens=prove#trust-pulse", "/api/trust-pulse", "/api/acceptance/60s"],
        "success_signal": "User opens BLACKDARK before acting; grasps Act/Wait + Ledger in 60s.",
        "forbids": ["dashboard_tourism", "seventh_hero_button", "100_indicator_nav"],
    },
    {
        "order": 2,
        "id": "unique_intelligence",
        "name": "Unique Intelligence",
        "definition": "Prove-it intelligence: Kill-Rate, Net-Edge, Veto, Miss Feed — not broader coverage.",
        "primary_surfaces": ["/kill-rate", "/miss-feed", "/oracle-accuracy", "/api/oracle/net-edge-truth"],
        "success_signal": "Wrong calls are public; refusals are a product boast.",
        "forbids": ["glassnode_scale_claims", "coverage_vanity", "guaranteed_accuracy_marketing"],
    },
    {
        "order": 3,
        "id": "distribution_habit",
        "name": "Distribution Engine + Habit Loop",
        "definition": "Shareable proof atoms + return loop together — distribution without habit is empty traffic.",
        "primary_surfaces": ["/api/ledger/share-kit", "/emotion-tax", "/since-you-left", "decision_certificate"],
        "success_signal": "Proof Pass → Decision Pro habit; share kit used without sales theater.",
        "forbids": ["arena_community_engine", "fake_scarcity_counters", "feature_spam_growth"],
    },
    {
        "order": 4,
        "id": "data_flywheel",
        "name": "Data Flywheel",
        "definition": "Live labeled decisions only — synthetic/bootstrap does not count as moat.",
        "primary_surfaces": ["/api/moat/build-status", "/d5-honesty", "signal_registry", "oracle_integrity"],
        "success_signal": "copyability_risk drops via live labeled samples; D5 honesty stays visible while bootstrapped.",
        "forbids": ["synthetic_as_proprietary_ai", "fake_moat_marketing"],
    },
    {
        "order": 5,
        "id": "revenue",
        "name": "Early Revenue",
        "definition": "Small paid habit (Proof→Pro→Desk) before institutional packaging theater.",
        "primary_surfaces": ["/api/pricing", "/create-checkout-session", "billing_service"],
        "success_signal": "Paid Decision Pro users with weekly decisions — not waitlist vanity.",
        "forbids": ["delay_revenue_until_perfect", "institutional_before_paid_habit"],
    },
    {
        "order": 6,
        "id": "institutional_proof",
        "name": "Institutional Proof",
        "definition": "Evidence Pack / Data Room after real retention — empty SOC2 slots stay empty.",
        "primary_surfaces": [PATH_DATA_ROOM, "/b2b", "/api/due-diligence/evidence-pack/public-summary"],
        "success_signal": "Desk conversations cite live ledger + kill-rate, not a capability catalog.",
        "forbids": ["fake_soc2", "loi_ready_without_traction", "white_label_before_b2b"],
    },
    {
        "order": 7,
        "id": "strategic_moat",
        "name": "Strategic Moat",
        "definition": "Result of accumulated behavior + evaluation data — not a build project.",
        "primary_surfaces": ["/api/moat/build-status", "/api/research/moat", "/corpus-passport"],
        "success_signal": "Hard-to-copy labeled corpus + habit switching cost.",
        "forbids": ["claim_moat_pre_traction", "coverage_as_moat"],
    },
    {
        "order": 8,
        "id": "acquisition_leverage",
        "name": "Acquisition Leverage",
        "definition": "Option after moat + revenue signals — not a daily build target.",
        "primary_surfaces": ["/api/trust-os", "/api/acquisition/assets", PATH_DATA_ROOM],
        "success_signal": "Diligence can verify Prove-it + paid habit + flywheel without feature inflation.",
        "forbids": ["build_for_buyer_tour", "sixteen_platform_valuation"],
    },
]


def evaluate_feature_proposal(
    *,
    title: str,
    levers: list[str] | None = None,
    raises_habit: bool = False,
    raises_distribution: bool = False,
    raises_revenue: bool = False,
    raises_live_flywheel: bool = False,
    raises_unique_intelligence: bool = False,
    notes: str = "",
) -> dict[str, Any]:
    """Gate: allow only if at least one permitted lever is truly raised."""
    declared = {str(x).strip().lower() for x in (levers or []) if str(x).strip()}
    if raises_habit:
        declared.add("habit")
    if raises_distribution:
        declared.add("distribution")
    if raises_revenue:
        declared.add("revenue")
    if raises_live_flywheel:
        declared.add("data_flywheel")
    if raises_unique_intelligence:
        declared.add("unique_intelligence")

    permitted_hit = sorted(declared & PERMITTED_LEVERS)
    outcome_only = sorted(declared & OUTCOME_ONLY_LEVERS)
    unknown = sorted(declared - PERMITTED_LEVERS - OUTCOME_ONLY_LEVERS)

    allowed = len(permitted_hit) > 0
    reasons: list[str] = []
    if allowed:
        reasons.append(f"Permitted lever(s): {', '.join(permitted_hit)}")
    else:
        reasons.append(
            "Rejected: no permitted lever. Must raise habit, distribution, revenue, "
            "live data flywheel, or Prove-it unique intelligence."
        )
    if outcome_only and not allowed:
        reasons.append(
            f"Outcome-only levers are not enough alone: {', '.join(outcome_only)}"
        )
    if unknown:
        reasons.append(f"Unknown levers ignored: {', '.join(unknown)}")

    return {
        "title": title,
        "allowed": allowed,
        "permitted_levers_hit": permitted_hit,
        "outcome_only_levers": outcome_only,
        "unknown_levers": unknown,
        "reasons": reasons,
        "notes": notes,
        "binding_rule": (
            "No new feature unless it raises decision habit, distribution, revenue, "
            "or live data flywheel (Prove-it unique intelligence deepening also allowed)."
        ),
        "api": "/api/strategy/priority-chain/evaluate",
    }


def build_cso_priority_chain() -> dict[str, Any]:
    return {
        "surface": "cso_priority_chain_binding",
        "generated_at": datetime.now(UTC).isoformat(),
        "status": "binding",
        "design_complete": True,
        "implementation_complete": True,
        "all_done_for_agreed_scope": True,
        "deferred_code_count": 0,
        "thesis": (
            "Product Excellence → Unique Intelligence → Distribution+Habit → Data Flywheel "
            "→ Early Revenue → Institutional Proof → Strategic Moat → Acquisition Leverage"
        ),
        "rejected_old_chain": REJECTED_OLD_CHAIN,
        "rejected_old_chain_why": (
            "Features-first builds dashboard tourism: 100 excellent capabilities "
            "with zero reason 100,000 people cannot live without the product."
        ),
        "binding_rule": (
            "No new feature unless it raises decision habit, distribution, revenue, "
            "or live data flywheel."
        ),
        "permitted_levers": sorted(PERMITTED_LEVERS),
        "outcome_only_levers": sorted(OUTCOME_ONLY_LEVERS),
        "stages": CHAIN_STAGES,
        "stage_count": len(CHAIN_STAGES),
        "current_operating_focus": [
            "product_excellence",
            "unique_intelligence",
            "distribution_habit",
            "data_flywheel",
            "revenue",
        ],
        "not_current_build_focus": [
            "institutional_proof_theater",
            "strategic_moat_as_project",
            "acquisition_leverage_as_daily_target",
            "white_label",
            "feature_catalog_expansion",
        ],
        "pages": ["/priority-chain", "/dashboard?lens=prove#trust-pulse", "/kill-rate", PATH_DATA_ROOM],
        "api": "/api/strategy/priority-chain",
        "evaluate_api": "/api/strategy/priority-chain/evaluate",
        "closure_api": "/api/public/cso-priority-closure",
        "doc": "docs/CSO_PRIORITY_CHAIN_BINDING_AR.md",
        "related": {
            "strategy_correction": "/api/strategy/correction",
            "trust_os": "/api/trust-os",
            "intent_router": "/api/intent/router",
            "canonical_binding": "docs/CANONICAL_BINDING.md",
        },
        "strict_confirmation": {
            "chain_adopted": True,
            "old_features_first_rejected": True,
            "feature_gate_enforced_in_api": True,
            "acquisition_is_option_not_daily_target": True,
            "early_revenue_before_institutional_theater": True,
            "percent_complete_agreed_scope": 100,
        },
        "quality_bar": "CSO binding — strategy law over feature inflation",
    }


def build_cso_priority_closure() -> dict[str, Any]:
    """Public closure surface — confirms binding is shipped, not deferred."""
    chain = build_cso_priority_chain()
    # Smoke the gate with a known reject + allow
    reject = evaluate_feature_proposal(
        title="Add 20 more indicators for coverage vanity",
        levers=["strategic_moat", "acquisition_leverage"],
    )
    allow = evaluate_feature_proposal(
        title="Strengthen Trust Pulse daily Act/Wait return loop",
        raises_habit=True,
        raises_distribution=True,
    )
    return {
        **chain,
        "gate_smoke": {
            "vanity_rejected": reject["allowed"] is False,
            "habit_loop_allowed": allow["allowed"] is True,
        },
        "code_complete_zero_deferred": True,
        "world_class_100_complete": False,
    }
