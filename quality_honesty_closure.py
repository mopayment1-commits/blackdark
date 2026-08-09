"""
BLACKDARK — Quality Honesty Closure (Soft Launch bar).

Strict inventory of Architecture → Acquisition DD capabilities.
Does NOT claim world-class 100% across the board.
Raises Soft Launch honesty to the highest truthful standard.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Soft Launch quality tiers (honest — not marketing grades)
TIER_SOFT_LAUNCH_STRONG = "soft_launch_strong"
TIER_PARTIAL_PROVENANCE = "partial_live_or_proxy"
TIER_PARKED = "parked_intentional"
TIER_NOT_WORLD_CLASS_100 = "not_world_class_100"


def _item(
    *,
    id: str,
    name: str,
    tier: str,
    soft_launch_ready: bool,
    world_class_100: bool,
    evidence: list[str],
    claim_boundary: str,
    next_honest_step: str,
) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "tier": tier,
        "soft_launch_ready": soft_launch_ready,
        "world_class_100": world_class_100,
        "evidence": evidence,
        "claim_boundary": claim_boundary,
        "next_honest_step": next_honest_step,
    }


def _onchain_mode() -> str:
    return str(os.getenv("ONCHAIN_DATA_SOURCE", getattr(__import__("config"), "ONCHAIN_DATA_SOURCE", "simulated"))).strip().lower()


def _sentiment_mode() -> str:
    import config

    return str(getattr(config, "SENTIMENT_DATA_SOURCE", "mixed") or "mixed").strip().lower()


async def build_quality_honesty_closure() -> dict[str, Any]:
    """Canonical Soft Launch quality matrix for the 16 capability areas."""
    import config
    from postgres_backend import use_postgres

    onchain_mode = _onchain_mode()
    sentiment_mode = _sentiment_mode()
    postgres = use_postgres()
    soft = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}
    billing = False
    try:
        from billing_service import billing_configured

        billing = billing_configured()
    except Exception:
        billing = False

    d5_bootstrap = True
    try:
        status_path = Path("data/models/regime/training_status.json")
        if status_path.exists():
            import json

            st = json.loads(status_path.read_text(encoding="utf-8") or "{}")
            live_only = st.get("trained_on_live_only") is True
            still_flagged = bool(st.get("bootstrap") or st.get("synthetic") or st.get("honesty_flag"))
            d5_bootstrap = (not live_only) or still_flagged
    except Exception:
        d5_bootstrap = True

    areas = [
        _item(
            id="architecture",
            name="Architecture",
            tier=TIER_SOFT_LAUNCH_STRONG,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["ARCHITECTURE.md", "/api/scale/readiness", "/api/viral/readiness", "production_guard"],
            claim_boundary="Soft Launch architecture OK; signed multi-worker HA is ops-proven only after Postgres+Redis+load log.",
            next_honest_step="Deploy with DATABASE_URL+REDIS_URL and sign LOAD_TEST_RUN_LOG.md before any HA claim.",
        ),
        _item(
            id="ai_financial_intelligence",
            name="AI Financial Intelligence",
            tier=TIER_SOFT_LAUNCH_STRONG if not d5_bootstrap else TIER_PARTIAL_PROVENANCE,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/d5-honesty", "docs/AI_FINANCIAL_MODEL_DESIGN.md", "oracle routes", "decision_certificate"],
            claim_boundary="Decision intelligence shipped with D5 honesty flags — not a fully calibrated institutional model farm.",
            next_honest_step="Accumulate live labeled decisions; keep /d5-honesty visible until bootstrap flags clear.",
        ),
        _item(
            id="market_radar",
            name="Market Radar",
            tier=TIER_SOFT_LAUNCH_STRONG,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/dashboard#radar", "/api/whale-activity", "Signal vs Noise surfaces"],
            claim_boundary="Operational radar for decisions — not Glassnode/Kaiko-scale market coverage.",
            next_honest_step="Keep Coverage Honesty page linked; do not market coverage breadth.",
        ),
        _item(
            id="opportunity_score",
            name="Opportunity Score",
            tier=TIER_SOFT_LAUNCH_STRONG,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["dashboard oracle card", "opportunity_score fields", "Net-Edge / Veto gates"],
            claim_boundary="Explainable opportunity for Act/Wait — not a guaranteed alpha score.",
            next_honest_step="Always pair score with Why + Ledger/Kill-Rate links in UX copy.",
        ),
        _item(
            id="portfolio_ai",
            name="Portfolio AI",
            tier=TIER_PARTIAL_PROVENANCE,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["POST /portfolio/analyze", "heroes_quality.build_portfolio_clarity"],
            claim_boundary="Plain-language portfolio risk helper (BTC-beta style heuristics) — not a full allocator OMS.",
            next_honest_step="Label responses as heuristic clarity; deepen only after live paid users ask.",
        ),
        _item(
            id="onchain_intelligence",
            name="On-chain intelligence",
            tier=TIER_PARTIAL_PROVENANCE,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/api/onchain/overview", "onchain_tracker.py", f"source={onchain_mode}"],
            claim_boundary=f"Current flow source mode: {onchain_mode}. Simulated/API-fallback is disclosed — not Nansen-scale entity graph.",
            next_honest_step="Set ONCHAIN_DATA_SOURCE=api with real keys before claiming live on-chain intel.",
        ),
        _item(
            id="sentiment",
            name="Sentiment",
            tier=TIER_PARTIAL_PROVENANCE,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/api/sentiment/overview", "sentiment_engine.py", f"source={sentiment_mode}"],
            claim_boundary="Mixed live RSS/CryptoCompare + optional mock social legs — not a full social firehose desk.",
            next_honest_step="Prefer SENTIMENT_DATA_SOURCE without mock for production marketing claims.",
        ),
        _item(
            id="macro",
            name="Macro",
            tier=TIER_PARTIAL_PROVENANCE,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/api/macro/overview", "oracle_data_hub.fetch_macro_mesh"],
            claim_boundary="Yahoo-extended macro mesh with safe fallbacks — not a Bloomberg macro terminal.",
            next_honest_step="Disclose proxy/fallback in UI; do not sell as institutional macro suite.",
        ),
        _item(
            id="risk_engine",
            name="Risk engine",
            tier=TIER_SOFT_LAUNCH_STRONG,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/api/risk/status", "risk_manager.py honest_scope", "slippage_guard"],
            claim_boundary="Execution safety gates (slippage/poison/freeze/stop-loss) — not institutional VaR/CVaR desk.",
            next_honest_step="Keep honest_scope in API responses; never market as full buy-side risk platform.",
        ),
        _item(
            id="research",
            name="Research",
            tier=TIER_PARTIAL_PROVENANCE,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/api/research/lab", "/api/research/moat", "research_lab.py"],
            claim_boundary="Research lab proxies + moat metrics — not a full research terminal.",
            next_honest_step="Frame as decision-support research aids under Trust OS, not sell-side research.",
        ),
        _item(
            id="institutional_apis",
            name="Institutional APIs",
            tier=TIER_SOFT_LAUNCH_STRONG,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/institutional", "/api/institutional/dd-closure", "org/SSO/MFA product surfaces"],
            claim_boundary="Product surfaces for emerging institutional path exist; external attestations (SOC2/pentest) are empty slots.",
            next_honest_step="Deposit real attestations only when earned; use Talk to us for From $3k.",
        ),
        _item(
            id="b2b",
            name="B2B",
            tier=TIER_SOFT_LAUNCH_STRONG,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/b2b", "/b2b/committee-one-pager", "allocator-receipt", "evidence pack APIs"],
            claim_boundary="B2B packaging ready for Soft Launch conversations — paid B2B revenue not yet proven.",
            next_honest_step="Run Emerging Desk pilots after live domain; do not claim B2B traction early.",
        ),
        _item(
            id="white_label",
            name="White-label",
            tier=TIER_PARKED,
            soft_launch_ready=False,
            world_class_100=False,
            evidence=["docs/INSTITUTIONAL_FEATURE_DD_AR.md (Park)"],
            claim_boundary="Intentionally parked until real B2B clients exist — not a Soft Launch deliverable.",
            next_honest_step="Reopen only after ≥1 paying B2B/Desk relationship requests branding.",
        ),
        _item(
            id="security",
            name="Security",
            tier=TIER_SOFT_LAUNCH_STRONG,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/api/security/status", "tests/test_security*.py", "docs/SECURITY_HARDENING.md", "Sonar/CodeQL gates"],
            claim_boundary="Engineering security posture + tests — not SOC2/ISO/pentest certification.",
            next_honest_step="Keep certificates false until third-party evidence is deposited.",
        ),
        _item(
            id="documentation",
            name="Documentation",
            tier=TIER_SOFT_LAUNCH_STRONG,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=[
                "docs/PRODUCT_COMPLETE_STATUS.md",
                "docs/QUALITY_HONESTY_SOFT_LAUNCH_AR.md",
                "/docs",
                "public developer OpenAPI strip",
            ],
            claim_boundary="Strong honesty documentation for Soft Launch — not a zero-defect LOI myth pack.",
            next_honest_step="Update this closure after each ops milestone; never erase claim boundaries.",
        ),
        _item(
            id="acquisition_dd_package",
            name="Acquisition DD package",
            tier=TIER_SOFT_LAUNCH_STRONG,
            soft_launch_ready=True,
            world_class_100=False,
            evidence=["/data-room", "/api/institutional/dd-closure", "/api/acquisition/assets", "corpus passport"],
            claim_boundary="DD surfaces + radical closure APIs ready; premium LOI readiness requires traction + attestations.",
            next_honest_step="Use Data Room for Soft Launch diligence; do not claim LOI-ready.",
        ),
    ]

    soft_ready = sum(1 for a in areas if a["soft_launch_ready"])
    world_100 = sum(1 for a in areas if a["world_class_100"])
    parked = sum(1 for a in areas if a["tier"] == TIER_PARKED)
    partial = sum(1 for a in areas if a["tier"] == TIER_PARTIAL_PROVENANCE)

    forbidden_claims = [
        "world_class_100_across_all_sixteen",
        "soc2_certified",
        "iso27001_certified",
        "glassnode_scale_coverage",
        "institutional_var_desk",
        "white_label_ready",
        "loi_ready_without_traction",
        "viral_ha_proven_on_soft_launch_sqlite",
    ]

    return {
        "surface": "quality_honesty_soft_launch_closure",
        "generated_at": datetime.now(UTC).isoformat(),
        "program": "Quality Honesty + Soft-Launch Hardening",
        "design_complete": True,
        "implementation_complete": True,
        "product_complete_for_soft_launch_honesty": True,
        "world_class_100_complete": False,
        "all_done_for_agreed_scope": True,
        "soft_launch_ready_count": soft_ready,
        "world_class_100_count": world_100,
        "partial_provenance_count": partial,
        "parked_count": parked,
        "total_areas": len(areas),
        "areas": areas,
        "runtime_context": {
            "soft_launch_env": soft,
            "postgres": postgres,
            "sqlite_ok_for_soft_launch": not postgres,
            "billing_configured": billing,
            "onchain_data_source": onchain_mode,
            "sentiment_data_source": sentiment_mode,
            "whitelist_assets": list(getattr(config, "WHITELIST_ASSETS", []) or [])[:12],
            "d5_bootstrap_suspected": d5_bootstrap,
        },
        "forbidden_claims": forbidden_claims,
        "allowed_public_claims": [
            "soft_launch_ready_decision_trust_os",
            "public_ledger_and_kill_rate_posture",
            "anti_hype_compliance_footer",
            "honest_partial_provenance_for_proxy_legs",
            "emerging_desk_path_without_fake_soc2",
        ],
        "pages": ["/data-room", "/d5-honesty", "/coverage-honesty", "/anti-hype", "/oracle-accuracy", "/kill-rate"],
        "api": "/api/public/quality-honesty-closure",
        "doc": "docs/QUALITY_HONESTY_SOFT_LAUNCH_AR.md",
        "strict_confirmation": {
            "agreed_scope_only": True,
            "no_white_label_ship": True,
            "no_fake_world_class_100": True,
            "provenance_labels_required_on_proxy_legs": True,
            "percent_complete_agreed_scope": 100,
            "percent_complete_world_class_myth": world_100 * 100 // max(len(areas), 1),
        },
        "quality_bar": "highest truthful Soft Launch bar — not fabricated institutional perfection",
    }


def provenance_block(
    *,
    surface: str,
    mode: str,
    live_legs: list[str] | None = None,
    proxy_or_mock_legs: list[str] | None = None,
    claim_boundary: str,
) -> dict[str, Any]:
    """Attach to overview APIs so UI/clients cannot mistake proxy for full desk."""
    mode_l = (mode or "unknown").strip().lower()
    is_live = mode_l in {"api", "live", "prod", "production"}
    is_mixed = mode_l in {"mixed", "hybrid"}
    return {
        "quality_provenance": {
            "surface": surface,
            "mode": mode_l,
            "live": is_live,
            "mixed": is_mixed,
            "proxy_or_simulated": (not is_live) or bool(proxy_or_mock_legs),
            "live_legs": live_legs or [],
            "proxy_or_mock_legs": proxy_or_mock_legs or [],
            "claim_boundary": claim_boundary,
            "soft_launch_ok": True,
            "world_class_100": False,
        }
    }
