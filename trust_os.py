"""
BLACKDARK — Trust OS valuation layers (honest acquisition framing).

Do NOT present 16/21 independent P&Ls. Present four value layers over one product.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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
            "Secrets vault + admin MFA + Postgres/Redis production guard",
        ],
        "status": "shipped_with_limits",
        "honest_limits": [
            "Engineering compliance posture ≠ SEC/MiCA license or SOC2/ISO certificate",
            "Counsel letter and entity packaging remain human steps",
        ],
    },
]

# Claims that must NOT be marketed as shipped product facts.
OVERCLAIM_DENYLIST: list[dict[str, str]] = [
    {"claim": "SOR / Smart Order Routing", "truth": "Not shipped — stealth advisor is advisory only"},
    {"claim": "TWAP / VWAP execution algorithms", "truth": "Not shipped"},
    {"claim": "Institutional TCA (Transaction Cost Analysis)", "truth": "Not shipped"},
    {"claim": "IFRS 13 certification", "truth": "Decimal money helpers ≠ IFRS 13 certification"},
    {"claim": "SOC 2 / ISO 27001 certificate", "truth": "Engineering controls exist; no external certificate"},
    {"claim": "16 or 21 independently valued platforms", "truth": "One product, four value layers"},
    {"claim": "Expected Shortfall / full VaR risk desk", "truth": "Kill-switch + drawdown + simple proxies only"},
    {"claim": "Knowledge Graph / semantic search platform", "truth": "Not shipped"},
]


def trust_os_manifest() -> dict[str, Any]:
    return {
        "product": "BLACKDARK",
        "framing": "Decision Intelligence / Trust OS — not a feature dump",
        "thesis": "Don't trust us. Verify us.",
        "value_layers": VALUE_LAYERS,
        "overclaim_denylist": OVERCLAIM_DENYLIST,
        "acquisition_posture": {
            "honest_fit": "decision-trust layer / acqui-hire / bolt-on to larger data or OMS stack",
            "not_a_fit_claim": "16 independent institutional platforms with separate P&Ls",
        },
        "primary_entry_points": {
            "retail_proof": "/oracle-accuracy",
            "decision": "/dashboard",
            "funds": "/b2b#fund-terminal",
            "compliance": "/compliance",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
