#!/usr/bin/env python3
"""RBAS-001 — Risk-Based Audit Scoping for official batch audits (Run 011 permanent)."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parents[1]

import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WF027_DORMANT_LEGACY_IDS = frozenset({175, 214, 245, 584, 629, 630, 631, 642, 644, 646})
BATCH04_RANGE = range(151, 201)
BATCH05_RANGE = range(201, 251)
WF027_IN_BATCH05 = WF027_DORMANT_LEGACY_IDS & set(BATCH05_RANGE)

Tier = Literal["TIER1", "TIER2"]

# Explicit Tier-1 triggers (when in doubt → Tier1 is enforced in classify())
_TIER1_SCORE_INDEX_PATTERN = re.compile(
    r"\b(score|scoring|index|rating|actionability|confidence\s*score|alpha|momentum\s*score|"
    r"decision|recommend|verdict|copilot|copilot|buy.?sell|signal\s*engine)\b",
    re.I,
)
_TIER1_ENTITLEMENT_PATTERN = re.compile(
    r"\b(entitlement|pay.?per.?request|billing|authentication|sso|rbac|capacity\s*gate)\b",
    re.I,
)
_TIER1_ONCHAIN_PATTERN = re.compile(
    r"\b(whale|wallet|holder|address|inflow|outflow|netflow|transaction|on.?chain|"
    r"dormancy|nvt|mvrv|realized\s*cap)\b",
    re.I,
)
_TIER2_DELIVERY_PATTERN = re.compile(
    r"\b(registry|library|feed|delivery|api\s*data|provenance|knowledge\s*graph|"
    r"dashboard|monitoring\s*coverage|research\s*feed|historical|trend|volume\s*intelligence|"
    r"activity\s*intelligence|network\s*activity|circulation)\b",
    re.I,
)

# Manual overrides after pattern pass — conservative Tier1 where catalog name is ambiguous
_MANUAL_TIER1: dict[int, str] = {
    152: "Governance & proposal intelligence — user-facing governance decision support",
    154: "AI Crypto Copilot — AI decision/recommendation surface",
    155: "AI Deep Research — AI research output influences decisions",
    160: "Pay-Per-Request Data Access — entitlement/billing (WF-015 pattern)",
    161: "Institutional Data Delivery & Entitlements — entitlement spine",
    163: "Cross-Domain Research-to-Decision Intelligence — explicit decision output",
    164: "Token Unlock Actionability Score — SCORE-IDX surface",
    165: "Fundraising Momentum Score — SCORE-IDX surface",
    166: "Research Confidence Score — SCORE-IDX surface",
    174: "Alpha Narratives Intelligence — alpha/decision-adjacent narrative ranking",
    175: "WF-027 dormant legacy ID + sentiment index",
    176: "Weighted Social Sentiment — sentiment index/score",
    177: "Social Sentiment Balance — sentiment index",
    183: "Whale Transaction Intelligence — on-chain transaction/address (FATF R.16)",
    184: "Whale & Shark Holder Cohorts — wallet cohort addresses (FATF R.16)",
    185: "Top Holders Intelligence — holder addresses (FATF R.16)",
    186: "Historical Wallet Balance Tool — wallet address tool (FATF R.16)",
    187: "Exchange Inflow Intelligence — exchange flow transaction intelligence",
    188: "Exchange Outflow Intelligence — exchange flow transaction intelligence",
    189: "Exchange Netflow Intelligence — exchange flow transaction intelligence",
    190: "Exchange Supply / Balance Intelligence — exchange balance/on-chain supply",
}

_MANUAL_TIER2: dict[int, str] = {
    151: "Quarterly protocol performance report delivery — no direct trading score",
    153: "Project monitoring coverage registry — catalog/registry",
    156: "Crypto knowledge graph — reference data graph",
    157: "Research library — catalog/delivery",
    158: "Institutional research feed — feed delivery",
    159: "API data platform — data-delivery (duplicate_of=103 documented)",
    162: "Evidence & provenance layer — metadata/provenance delivery",
    167: "Social volume intelligence — raw social metric delivery",
    168: "Social dominance intelligence — social metric delivery",
    169: "Unique social volume — social metric delivery",
    170: "Trending words — lexical trend delivery",
    171: "Trending coins — market trend list delivery",
    172: "Historical crypto trends — historical data delivery",
    173: "Key narratives intelligence — narrative catalog delivery",
    178: "Social source breakdown — source attribution delivery",
    179: "Development activity intelligence — dev metric delivery",
    180: "Development activity contributors — contributor registry",
    181: "Ecosystem development dashboard — dashboard delivery",
    182: "Developer activity change detection — change feed (no score/decision)",
    191: "Exchange user activity — activity metric delivery",
    192: "Network activity intelligence — network metric delivery",
    193: "Transaction volume intelligence — volume metric delivery",
    194: "NVT intelligence — on-chain metric delivery (not user verdict score)",
    195: "MVRV intelligence — on-chain metric delivery",
    196: "Realized cap / realized value — metric delivery",
    197: "Daily active addresses — metric delivery",
    198: "Age consumed / dormancy — metric delivery",
    199: "Mean dollar invested age — metric delivery",
    200: "Token circulation intelligence — supply metric delivery",
}

_MANUAL_TIER1_BATCH05: dict[int, str] = {
    214: "WF-027 dormant legacy ID — Watchlists (T11); mandatory full audit",
    223: "Social-to-On-Chain Confirmation Engine — confirmation/decision output",
    224: "Narrative Actionability Score — SCORE-IDX surface",
    225: "Development-to-Market Divergence Detector — divergence signal influences decisions",
    226: "Cross-Domain Decision Intelligence Layer — explicit decision output",
    227: "Unified Trading Intelligence Workspace — trading decision workspace",
    229: "Cross-Exchange Funding Arbitrage Scanner — arbitrage/trading decision surface",
    230: "Spot-Perp Arbitrage Scanner — arbitrage/trading decision surface",
    237: "Token Risk Scoring — SCORE-IDX surface",
    238: "Pump & Dump Detection — detection verdict influences user action",
    240: "Sector Rotation Intelligence — portfolio allocation decision-adjacent",
    241: "Sentiment Intelligence — sentiment index (duplicate_of=129; SCORE-IDX pattern)",
    242: "Price Prediction / Multi-Signal Forecast — AI prediction (NIST AI RMF full path)",
    245: "WF-027 dormant legacy ID — Market Health & Freshness (T13); mandatory full audit",
}

_MANUAL_TIER2_BATCH05: dict[int, str] = {
    201: "Network growth intelligence — on-chain metric delivery (no user verdict score)",
    202: "Supply distribution intelligence — distribution metric delivery",
    203: "DEX trading intelligence — market data delivery",
    204: "DeFi protocol activity intelligence — activity metric delivery",
    205: "Open Interest Intelligence — derivatives metric delivery",
    206: "Funding Rate Intelligence — metric delivery (duplicate_of=86)",
    207: "Price / Volume / Market Metrics — market metric delivery",
    208: "Metric Correlation Workbench — analysis workbench (no score output)",
    209: "Custom Chart Builder — chart builder delivery",
    210: "Custom Dashboards / Layouts — dashboard delivery",
    211: "Screener — screening tool without scored verdict",
    212: "Smart Alerts — alert delivery (duplicate_of=17)",
    213: "Anomaly Detection Alerts — alert feed delivery",
    215: "Community Explorer — catalog/explorer delivery",
    216: "Research & Market Insights — research delivery",
    217: "SanAPI-Style Data Access — data access delivery",
    218: "Google Sheets Integration — integration delivery",
    219: "Metric Availability Registry — registry/catalog",
    220: "Data Stabilization & Mutability Metadata — metadata delivery",
    221: "Data Quality & Provenance Layer — provenance delivery (duplicate_of=63)",
    222: "Metric Methodology Registry — methodology registry",
    228: "Funding Rate Intelligence — metric delivery (duplicate_of=86)",
    231: "Futures Basis & Term Structure — term structure metric delivery",
    232: "Open Interest Intelligence — metric delivery (duplicate_of=205)",
    233: "Liquidation Intelligence — metric delivery (duplicate_of=88)",
    234: "CVD Intelligence — volume delta metric delivery",
    235: "Long/Short Ratio Intelligence — ratio metric delivery",
    236: "DEX Screener — screener delivery",
    239: "Narrative Tracking — narrative catalog tracking",
    243: "Correlation Matrix — correlation data tool",
    244: "New Listings Intelligence — listings feed delivery",
    246: "Coverage Metadata Registry — coverage registry",
    247: "Public REST API — API delivery surface",
    248: "MCP Server for AI Agents — platform delivery",
    249: "CLI Access — CLI delivery",
    250: "OpenAPI / SDK Generation — SDK generation delivery",
}


def classify_batch04_capability(
    capability_id: int,
    *,
    capability_name: str,
    track: str = "",
) -> tuple[Tier, str]:
    """Return (tier, reason). Default Tier1 when criteria overlap or uncertain."""
    if capability_id in _MANUAL_TIER1:
        return "TIER1", _MANUAL_TIER1[capability_id]
    if capability_id in _MANUAL_TIER2:
        return "TIER2", _MANUAL_TIER2[capability_id]
    if capability_id in WF027_DORMANT_LEGACY_IDS:
        return "TIER1", f"WF-027 dormant legacy ID {capability_id} — mandatory full audit"
    name = capability_name or ""
    if _TIER1_ENTITLEMENT_PATTERN.search(name):
        return "TIER1", "Entitlement/authentication/billing surface (WF-015 pattern)"
    if _TIER1_SCORE_INDEX_PATTERN.search(name):
        return "TIER1", "Score/index/decision/recommendation surface (SCORE-IDX-001 pattern)"
    if track in {"T09"} or _TIER1_ONCHAIN_PATTERN.search(name):
        if any(k in name.lower() for k in ("whale", "wallet", "holder", "inflow", "outflow", "netflow", "address")):
            return "TIER1", "On-chain address/transaction intelligence (FATF R.16)"
    if track in {"T12", "T14"} and "ai" in name.lower():
        return "TIER1", "AI surface — decision/research risk (NIST AI RMF full path)"
    if _TIER2_DELIVERY_PATTERN.search(name):
        return "TIER2", "Data-delivery/catalog/registry without direct user decision output"
    return "TIER1", "RBAS-001 default-on-doubt — no clear Tier2 delivery-only proof"


def batch04_tier_map() -> dict[int, dict[str, Any]]:
    from cap646.catalog import catalog_by_id

    catalog = catalog_by_id()
    out: dict[int, dict[str, Any]] = {}
    for cid in BATCH04_RANGE:
        row = catalog.get(cid, {})
        tier, reason = classify_batch04_capability(
            cid,
            capability_name=str(row.get("capability") or ""),
            track=str(row.get("track") or ""),
        )
        out[cid] = {
            "id": cid,
            "capability": row.get("capability"),
            "track": row.get("track"),
            "rbas_tier": tier,
            "rbas_reason": reason,
        }
    return out


def write_tier_table(path: Path) -> dict[int, dict[str, Any]]:
    tiers = batch04_tier_map()
    rows = [tiers[cid] for cid in BATCH04_RANGE]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return tiers


def classify_batch05_capability(
    capability_id: int,
    *,
    capability_name: str,
    track: str = "",
) -> tuple[Tier, str]:
    """Return (tier, reason). Default Tier1 when criteria overlap or uncertain."""
    if capability_id in _MANUAL_TIER1_BATCH05:
        return "TIER1", _MANUAL_TIER1_BATCH05[capability_id]
    if capability_id in _MANUAL_TIER2_BATCH05:
        return "TIER2", _MANUAL_TIER2_BATCH05[capability_id]
    if capability_id in WF027_DORMANT_LEGACY_IDS:
        return "TIER1", f"WF-027 dormant legacy ID {capability_id} — mandatory full audit"
    name = capability_name or ""
    if _TIER1_ENTITLEMENT_PATTERN.search(name):
        return "TIER1", "Entitlement/authentication/billing surface (WF-015 pattern)"
    if _TIER1_SCORE_INDEX_PATTERN.search(name):
        return "TIER1", "Score/index/decision/recommendation surface (SCORE-IDX-001 pattern)"
    if track in {"T09"} or _TIER1_ONCHAIN_PATTERN.search(name):
        if any(k in name.lower() for k in ("whale", "wallet", "holder", "inflow", "outflow", "netflow", "address")):
            return "TIER1", "On-chain address/transaction intelligence (FATF R.16)"
    if track in {"T12", "T14"} and "ai" in name.lower():
        return "TIER1", "AI surface — decision/research risk (NIST AI RMF full path)"
    if _TIER2_DELIVERY_PATTERN.search(name):
        return "TIER2", "Data-delivery/catalog/registry without direct user decision output"
    return "TIER1", "RBAS-001 default-on-doubt — no clear Tier2 delivery-only proof"


def batch05_tier_map() -> dict[int, dict[str, Any]]:
    from cap646.catalog import catalog_by_id

    catalog = catalog_by_id()
    out: dict[int, dict[str, Any]] = {}
    for cid in BATCH05_RANGE:
        row = catalog.get(cid, {})
        tier, reason = classify_batch05_capability(
            cid,
            capability_name=str(row.get("capability") or ""),
            track=str(row.get("track") or ""),
        )
        out[cid] = {
            "id": cid,
            "capability": row.get("capability"),
            "track": row.get("track"),
            "rbas_tier": tier,
            "rbas_reason": reason,
        }
    return out


def write_batch05_tier_table(path: Path) -> dict[int, dict[str, Any]]:
    tiers = batch05_tier_map()
    rows = [tiers[cid] for cid in BATCH05_RANGE]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return tiers


if __name__ == "__main__":
    out = ROOT / "institutional_due_diligence_2026" / "batch04_independent_audit" / "RBAS001_TIER_CLASSIFICATION.json"
    tiers = write_tier_table(out)
    t1 = sum(1 for r in tiers.values() if r["rbas_tier"] == "TIER1")
    t2 = sum(1 for r in tiers.values() if r["rbas_tier"] == "TIER2")
    print(f"Wrote {out}")
    print(f"TIER1={t1} TIER2={t2}")
