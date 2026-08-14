"""Honest 6-persona capability matrix for trial launch (unpaid ceiling).

Never claims live_fill / Jupiter VC / Full Mesh L2 100% / cloud multi-AZ.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _cap(
    *,
    name: str,
    status: str,
    surfaces: list[str],
    note: str,
    unpaid_block: str | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,  # works | partial | gated | external_block | na
        "surfaces": surfaces,
        "note": note,
        "unpaid_block": unpaid_block,
    }


def persona_capability_matrix() -> dict[str, Any]:
    """Binding inventory for the six trial personas."""
    from auth_service import TIER_FEATURES
    from audience_routing import all_audiences

    four: dict[str, Any] = {}
    try:
        from pathlib import Path
        import json

        p = Path("docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json")
        if p.is_file():
            four = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        four = {}
    b1 = four.get("blocker_1_live_venue_fill") or {}
    b2 = four.get("blocker_2_jupiter_live_signature") or {}
    b3 = four.get("blocker_3_full_mesh_100") or {}
    b4 = four.get("blocker_4_cloud_multi_az_ha") or {}

    personas = {
        "retail": {
            "label": "Small retail user",
            "tier": "free",
            "tier_label": TIER_FEATURES["free"]["label"],
            "entry": "/?audience=retail",
            "gets": [
                _cap(
                    name="Single-sentence Oracle (3/day)",
                    status="works",
                    surfaces=["/oracle/{symbol}", "/"],
                    note="Quota-capped Proof Pass; watermarked certificates.",
                ),
                _cap(
                    name="Public accuracy ledger + proof arena",
                    status="works",
                    surfaces=["/oracle-accuracy", "/proof-arena", "/public/accuracy-ledger"],
                    note="Read-only public proof surfaces.",
                ),
                _cap(
                    name="Journal",
                    status="works",
                    surfaces=["/api/journal"],
                    note="CRUD enabled on free tier.",
                ),
                _cap(
                    name="Alerts / arb desk / live execution",
                    status="gated",
                    surfaces=["/api/alerts/subscribe", "/api/arbitrage"],
                    note="Requires Pro+.",
                ),
            ],
        },
        "pro": {
            "label": "Professional trader",
            "tier": "pro",
            "tier_label": TIER_FEATURES["pro"]["label"],
            "entry": "/dashboard?audience=pro",
            "gets": [
                _cap(
                    name="Unlimited oracle + Opportunity Score + radar",
                    status="works",
                    surfaces=["/dashboard?audience=pro", "/api/oracle"],
                    note="Decision Pro desk.",
                ),
                _cap(
                    name="Arbitrage catalog + research lab + AI chat",
                    status="works",
                    surfaces=["/api/arbitrage", "/api/research", "/api/chat"],
                    note="Gated by Pro feature flags.",
                ),
                _cap(
                    name="Alerts subscribe (Telegram/email)",
                    status="partial",
                    surfaces=["/api/alerts/subscribe"],
                    note="Code path works; live Telegram channel needs bot token (ops, unpaid if already owned).",
                ),
                _cap(
                    name="Paper/sim execution",
                    status="works",
                    surfaces=["/api/simulate", "/api/execution"],
                    note="Live venue fill is whale+ and still geo-blocked.",
                ),
                _cap(
                    name="Self-serve paid upgrade",
                    status="partial",
                    surfaces=["/api/billing/checkout"],
                    note="Checkout code ready; live PSP charge needs owner Stripe/Lemon secrets.",
                    unpaid_block="psp_credentials",
                ),
            ],
        },
        "whale": {
            "label": "Whale / large capital",
            "tier": "whale",
            "tier_label": TIER_FEATURES["whale"]["label"],
            "entry": "/dashboard?audience=whale#stealth",
            "gets": [
                _cap(
                    name="Stealth advisor + whale radar + voice",
                    status="works",
                    surfaces=["/api/whale", "/api/voice/command"],
                    note="Desk features gated by whale tier.",
                ),
                _cap(
                    name="OMS lifecycle (paper / dry-run)",
                    status="works",
                    surfaces=["/api/institutional/oms"],
                    note="INTENT→RECONCILE works in-process.",
                ),
                _cap(
                    name="Live venue FILL",
                    status="external_block",
                    surfaces=["/api/execution", "venue_fill_proof"],
                    note="HMAC path armed; order hosts HTTP 451 from this egress.",
                    unpaid_block="binance_order_host_geo_451",
                ),
                _cap(
                    name="Jupiter on-chain swap VC",
                    status="external_block",
                    surfaces=["jupiter_dex_adapter"],
                    note="Local wallet sign works; broadcast needs funded wallet.",
                    unpaid_block="wallet_unfunded_zero_cost_constraint",
                ),
                _cap(
                    name="Evidence pack (whale)",
                    status="works",
                    surfaces=["/api/due-diligence/evidence-pack"],
                    note="JSON pack; does not claim COMPLETE.",
                ),
            ],
        },
        "fund": {
            "label": "Fund / allocator",
            "tier": "institutional_sales",
            "tier_label": "Emerging Fund Terminal (sales-led)",
            "entry": "/b2b?audience=fund#fund-terminal",
            "gets": [
                _cap(
                    name="Fund terminal + data room + model card",
                    status="works",
                    surfaces=["/b2b", "/data-room", "/api/institutional/model-card"],
                    note="Pack assembly in-process.",
                ),
                _cap(
                    name="Org tenancy + MFA policy + RBAC",
                    status="works",
                    surfaces=["/api/institutional/orgs"],
                    note="JSON org store; Postgres optional.",
                ),
                _cap(
                    name="SSO / SCIM",
                    status="partial",
                    surfaces=["/api/institutional/sso", "/api/institutional/scim"],
                    note="Crypto paths exist; live IdP/SCIM bearer is operator config.",
                ),
                _cap(
                    name="Cloud multi-AZ HA",
                    status="external_block",
                    surfaces=["ops_recovery"],
                    note="Local streaming HA is separate VC.",
                    unpaid_block="zero_cost_no_paid_cloud_multi_az",
                ),
            ],
        },
        "b2b": {
            "label": "B2B / white-label tenant",
            "tier": "whale_or_org",
            "tier_label": "B2B feed + in-process white-label",
            "entry": "/b2b",
            "gets": [
                _cap(
                    name="Institutional feed (env or org API key)",
                    status="works",
                    surfaces=["/api/b2b/feed", "/ws/b2b/feed"],
                    note="Env key plus hashed org-scoped keys.",
                ),
                _cap(
                    name="White-label portal / terminal / exports",
                    status="partial",
                    surfaces=[
                        "/api/institutional/orgs/{id}/portal",
                        "/api/institutional/orgs/{id}/terminal",
                    ],
                    note="In-process branding; hosted custom domain is unpaid SaaS.",
                ),
                _cap(
                    name="Hosted multi-tenant custom domain",
                    status="external_block",
                    surfaces=["white_label.hosted_custom_domain"],
                    note="Not claimed as SaaS hosting.",
                    unpaid_block="hosted_custom_domain_requires_paid_infra",
                ),
            ],
        },
        "acquirer": {
            "label": "Acquisition / DD manager",
            "tier": "admin_or_whale",
            "tier_label": "Due-diligence room",
            "entry": "/data-room",
            "gets": [
                _cap(
                    name="Evidence pack + four-blockers honesty",
                    status="works",
                    surfaces=[
                        "/api/due-diligence/evidence-pack",
                        "docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json",
                    ],
                    note="Pack embeds NOT_COMPLETE verdict.",
                ),
                _cap(
                    name="Launch checklist + plan/roadmap audits",
                    status="works",
                    surfaces=["/admin/launch", "/api/plan/audit", "/api/roadmap/audit"],
                    note="Checklist may show pending domain/golive (ops).",
                ),
                _cap(
                    name="Clean-room COMPLETE claim",
                    status="external_block",
                    surfaces=["docs/dd/BLACKDARK_INSTITUTIONAL_COMPLETION_REGISTER.md"],
                    note="Binding: NOT COMPLETE while four blockers remain.",
                ),
            ],
        },
    }

    return {
        "ok": True,
        "surface": "persona_capability_matrix",
        "product_complete": False,
        "institutional_verdict": "NOT_COMPLETE",
        "trial_ready_unpaid": True,
        "live_money_ready": False,
        "proved_at": _utcnow(),
        "audiences": all_audiences(),
        "four_blockers": {
            "live_fill": bool(b1.get("live_fill")),
            "live_fill_block": b1.get("external_block"),
            "jupiter_vc": bool(b2.get("verified_complete")),
            "jupiter_block": b2.get("external_block"),
            "institutional_l2_percent": b3.get("institutional_l2_coverage_percent"),
            "full_mesh_l2_complete": bool(b3.get("full_mesh_l2_complete")),
            "cloud_multi_az": bool(b4.get("cloud_multi_az")),
            "cloud_block": b4.get("external_block"),
        },
        "personas": personas,
        "integrity": {
            "synthetic_mid_is_not_institutional_l2": True,
            "local_sign_is_not_rpc_vc": True,
            "local_ha_is_not_cloud_multi_az": True,
            "paper_fill_is_not_live_fill": True,
        },
        "note": (
            "Each persona receives every unpaid capability gated to their tier. "
            "Paid/geo/wallet/cloud blockers stay EXTERNAL and are never advertised as PASS."
        ),
    }
