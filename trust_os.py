"""
BLACKDARK — Trust OS valuation layers (honest acquisition framing).

Do NOT present 16/21 independent P&Ls. Present four value layers over one product.
Strategic correction binding rejects inflated 15-section / 100-indicator pastes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# Sonar S1192: duplicated string literals
DOC_CSO_PRIORITY_CHAIN_BINDING_AR = 'docs/CSO_PRIORITY_CHAIN_BINDING_AR.md'
PATH_API_STRATEGY_PRIORITY_CHAIN = '/api/strategy/priority-chain'
STR_NOT_SHIPPED = 'Not shipped'

VALUE_LAYERS: list[dict[str, Any]] = [
    {
        "id": "decision_intelligence",
        "name": "Decision Intelligence",
        "priority": 1,
        "surfaces": [
            "/dashboard",
            "/oracle/{symbol}",
            "/discipline-mirror",
        ],
        "capabilities": [
            "Single-Sentence Oracle (ACT/WAIT)",
            "Dimension Conflict Guard",
            "Discipline Mirror",
            "Net-Edge Truth + Opportunity Half-Life",
            "Intent router (results over features)",
        ],
        "status": "shipped",
    },
    {
        "id": "transparency_evidence",
        "name": "Transparency & Evidence",
        "priority": 1,
        "surfaces": [
            "/oracle-accuracy",
            "/oracle-accuracy#glass-box-challenge",
            "/api/due-diligence/evidence-pack",
        ],
        "capabilities": [
            "Public Accuracy Ledger (hits + misses)",
            "Glass Box Challenge pack",
            "Decision Certificate + audit hash chain",
            "Acquirer Evidence Pack (D6)",
        ],
        "status": "shipped",
    },
    {
        "id": "market_execution_edge",
        "name": "Market / Execution Edge",
        "priority": 2,
        "surfaces": [
            "/dashboard#stealth",
            "/api/whale/signal-vs-noise",
            "/api/platform/arb/cex-dex",
        ],
        "capabilities": [
            "Arbitrage scanner (CEX cross / spot-futures / CEX↔DEX)",
            "Whale Signal vs Noise classifier",
            "Stealth Execution Advisor (advisory, not stealth routing)",
            "Slippage / net-edge truth gates",
        ],
        "status": "shipped_with_limits",
        "honest_limits": [
            "Not a Smart Order Router (SOR)",
            "Not TWAP/VWAP algo execution",
            "Not post-trade TCA suite",
        ],
    },
    {
        "id": "institutional_packaging",
        "name": "Institutional Packaging",
        "priority": 2,
        "surfaces": [
            "/b2b#fund-terminal",
            "/compliance",
            "/api/b2b/feed",
            "/capabilities",
        ],
        "capabilities": [
            "Emerging Fund Terminal (sub-$50M packaging)",
            "Anti-Hype / Legal Shield engineering posture",
            "B2B signed feed + WebSocket",
            "Secrets vault + admin TOTP MFA + OAuth2 scaffolding + Postgres/Redis production guard",
        ],
        "status": "shipped_with_limits",
        "honest_limits": [
            "Engineering compliance posture ≠ SEC/MiCA license or SOC2/ISO certificate",
            "Counsel letter and entity packaging remain human steps",
            "MFA/OAuth are engineering controls when configured — not a compliance certificate",
            "High concurrency requires Postgres+Redis multi-worker; Soft Launch SQLite is demo-only",
        ],
    },
]

# Claims that must NOT be marketed as shipped product facts.
OVERCLAIM_DENYLIST: list[dict[str, str]] = [
    {"claim": "SOR / Smart Order Routing", "truth": "Not shipped — stealth advisor is advisory only"},
    {"claim": "TWAP / VWAP execution algorithms", "truth": STR_NOT_SHIPPED},
    {"claim": "Institutional TCA (Transaction Cost Analysis)", "truth": STR_NOT_SHIPPED},
    {"claim": "IFRS 13 certification", "truth": "Decimal money helpers ≠ IFRS 13 certification"},
    {"claim": "Triple-Entry Ledger Reconciliation (live sat/wei)", "truth": "Not shipped as institutional reconciliation suite"},
    {"claim": "SOC 2 / ISO 27001 certificate", "truth": "Engineering controls exist; no external certificate"},
    {"claim": "16 or 21 independently valued platforms", "truth": "One product, four value layers"},
    {"claim": "15 separately marketed product sections", "truth": "Rejected — four value layers + six heroes only"},
    {"claim": "Expected Shortfall / full VaR 99% risk desk", "truth": "Kill-switch + drawdown + simple proxies only"},
    {"claim": "Knowledge Graph / semantic ontology platform", "truth": STR_NOT_SHIPPED},
    {"claim": "BLACKDARK ARENA / Viral Community Engine", "truth": "Not building — virality via Certificate share + Glass Box event"},
    {"claim": "Neuro-Design / Parametric Canvas OS", "truth": "Not a product surface — quiet UX depth only"},
    {"claim": "100 retail indicator product / Whale Gravity Map as 100-metric UI", "truth": "Engines stay quiet behind six heroes"},
    {"claim": "Kafka + Rust <50ms + 100 CEX WebSockets as shipped", "truth": "Future infra option — not a current ship claim"},
    {"claim": "Panic Button closes 100 venues in 100ms", "truth": STR_NOT_SHIPPED},
    {"claim": "Guaranteed 65–70% predictive accuracy", "truth": "Only live labeled Public Accuracy Ledger stats — never a guarantee"},
    {"claim": "Net profit <15% auto-cancel as CAO law", "truth": "Invalid arb threshold — use net-edge truth gates instead"},
    {"claim": "HashiCorp Vault + Trail of Bits + Big Four as completed", "truth": "Human / procurement steps — not claimed shipped"},
    {
        "claim": "FalconAI 16 institutional platforms + 120 capabilities valuation",
        "truth": "Rejected — one product, four value layers, six heroes (docs/CANONICAL_BINDING.md)",
    },
    {
        "claim": "FalconAI BD-DEC-0031 sole canonical product map",
        "truth": "Superseded by CANONICAL_BINDING hierarchy — Falcon inventories are engine appendices only",
    },
]

FIVE_OUTCOMES: list[str] = [
    "Discover opportunities",
    "Make a decision",
    "Reduce risk",
    "Save time",
    "Improve execution quality",
]

REPORT_CORRECTIONS: list[dict[str, str]] = [
    {
        "reject": "Expand to 15 sections / rename parade (Market Eye, Truth Vault…)",
        "keep": "Four value layers with English institutional names",
    },
    {
        "reject": "Viral ARENA / Neuro-Design as acquisition pillars",
        "keep": "Shareable Decision Certificates + one Glass Box public event",
    },
    {
        "reject": "100 indicators as the sellable surface",
        "keep": "Six heroes; engines quiet; Signal Registry kills unnamed signals",
    },
    {
        "reject": "HFT / Lambda Architecture as current valuation claim",
        "keep": "Prove-it ledger + decision trust as the acquirable asset",
    },
]


def trust_os_manifest() -> dict[str, Any]:
    return {
        "product": "BLACKDARK",
        "framing": "Decision Intelligence / Trust OS — not a feature dump",
        "thesis": "Don't trust us. Verify us.",
        "slogan": "The project is engineered for Institutional Trust before Institutional Scale.",
        "value_layers": VALUE_LAYERS,
        "overclaim_denylist": OVERCLAIM_DENYLIST,
        "five_outcomes": FIVE_OUTCOMES,
        "report_corrections": REPORT_CORRECTIONS,
        "success_metric": {
            "bar": "60_second_grasp",
            "definition": (
                "A new user understands Act/Wait and where to verify on the "
                "Public Accuracy Ledger without a guided tour."
            ),
        },
        "quiet_engines_policy": (
            "Microstructure, sentiment, macro, on-chain, storage, and stream kernels "
            "may deepen heroes silently — they are not retail platforms."
        ),
        "acquisition_posture": {
            "honest_fit": "decision-trust layer / acqui-hire / bolt-on to larger data or OMS stack",
            "not_a_fit_claim": "16 independent institutional platforms with separate P&Ls",
        },
        "ux_lenses": {
            "story": "Prove → Operate → Desk → Room",
            "api": "/api/lenses",
            "primary_entries": ["decide", "verify", "my_book", "alerts"],
            "viral_atom": "decision_certificate",
            "first_open": "trust_pulse",
            "doc": "docs/TRUST_OS_LENSES_UX.md",
        },
        "trust_pulse": {
            "api": "/api/trust-pulse",
            "stream": "/api/trust-pulse/stream",
            "ui": "/dashboard#trust-pulse",
            "doc": "docs/TRUST_PULSE.md",
            "role": "First-open live Act/Wait + Why + Ledger proof",
        },
        "primary_entry_points": {
            "retail_proof": "/dashboard?lens=prove#trust-pulse",
            "trust_pulse": "/dashboard#trust-pulse",
            "verify": "/oracle-accuracy",
            "decision": "/dashboard?lens=operate",
            "desk": "/dashboard?lens=desk",
            "funds": "/data-room?lens=room",
            "compliance": "/compliance",
            "strategy_correction": "/api/strategy/correction",
            "priority_chain": PATH_API_STRATEGY_PRIORITY_CHAIN,
            "priority_chain_page": "/priority-chain",
            "zero_tolerance": "/api/strategy/zero-tolerance",
            "zero_tolerance_page": "/zero-tolerance",
            "lenses": "/api/lenses",
        },
        "cso_priority_chain": {
            "api": PATH_API_STRATEGY_PRIORITY_CHAIN,
            "closure": "/api/public/cso-priority-closure",
            "page": "/priority-chain",
            "doc": DOC_CSO_PRIORITY_CHAIN_BINDING_AR,
            "binding_rule": (
                "No new feature unless it raises decision habit, distribution, revenue, "
                "or live data flywheel."
            ),
        },
        "zero_tolerance": {
            "api": "/api/strategy/zero-tolerance",
            "closure": "/api/public/zero-tolerance-closure",
            "page": "/zero-tolerance",
            "doc": "docs/ZERO_TOLERANCE_BINDING_AR.md",
            "defect_count": 7,
        },
        "binding_docs": [
            "docs/PRODUCT_CONSTITUTION_AR.md",
            "docs/CANONICAL_BINDING.md",
            "docs/TRUST_OS_VALUE_LAYERS.md",
            "docs/TRUST_OS_LENSES_UX.md",
            "docs/TRUST_PULSE.md",
            "docs/TRUST_OS_DESIGN_SYSTEM.md",
            "docs/HEROES_STRATEGY_BINDING.md",
            "docs/STRATEGIC_CORRECTION_BINDING.md",
            DOC_CSO_PRIORITY_CHAIN_BINDING_AR,
            "docs/ZERO_TOLERANCE_BINDING_AR.md",
        ],
        "design_system": {
            "css": "/static/css/trust-os.css",
            "doc": "docs/TRUST_OS_DESIGN_SYSTEM.md",
            "display_font": "Syne",
            "body_font": "IBM Plex Sans",
            "motions": ["pulseIn", "flipFlash", "sharePop"],
            "rejected": ["arena", "inter_font", "purple_gold_ai_defaults", "fake_scarcity_counters"],
            "landing_myth": {
                "asset": "/static/img/blackdark-sealed-hero.webp",
                "line": "We publish the miss.",
                "support": "Sealed forecasts before the event. Public proof after.",
                "ctas": ["Try Oracle Free", "Watch the Seal"],
                "live_surface": "trust_pulse",
            },
        },
        "generated_at": datetime.now(UTC).isoformat(),
    }


def strategy_correction_manifest() -> dict[str, Any]:
    """Expert correction of inflated strategy pastes — machine-readable."""
    from intent_router import intent_router_manifest

    return {
        "doc": "docs/STRATEGIC_CORRECTION_BINDING.md",
        "thesis": "Prove it. Four layers. Six heroes. No seventh button.",
        "value_layers_count": 4,
        "heroes_count": 6,
        "five_outcomes": FIVE_OUTCOMES,
        "report_corrections": REPORT_CORRECTIONS,
        "overclaim_denylist": OVERCLAIM_DENYLIST,
        "intent_router": intent_router_manifest(),
        "not_building": [
            "viral_arena",
            "neuro_design_canvas",
            "browser_extension_platform",
            "100_indicator_retail_surface",
            "fifteen_section_platform_map",
            "falconai_16_120_valuation",
            "sor_twap_tca_ifrs_soc2_as_shipped",
        ],
        "canonical_binding": "docs/CANONICAL_BINDING.md",
        "cso_priority_chain": {
            "api": PATH_API_STRATEGY_PRIORITY_CHAIN,
            "doc": DOC_CSO_PRIORITY_CHAIN_BINDING_AR,
            "rejects": "features_first_launch_users_acquisition",
        },
        "generated_at": datetime.now(UTC).isoformat(),
    }
