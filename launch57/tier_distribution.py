"""
Launch-57 tier distribution SSOT — 57/57 capability → tier, surface, gating.

Binding: LAUNCH57_REGISTER.json names (literal) + approved launch pricing ladder.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

from billing.plan_registry import normalize_plan, plan_rank

_REGISTER_PATH = Path(__file__).resolve().parents[1] / "governance/launch57/LAUNCH57_REGISTER.json"

TIER_FLOOR = "floor"
TIER_FREE = "free"
TIER_PRO = "pro"
TIER_ELITE = "elite"
TIER_QUANT = "quant"
TIER_INSTITUTIONAL = "institutional"

TIER_RANK: dict[str, int] = {
    TIER_FLOOR: 0,
    TIER_FREE: 1,
    TIER_PRO: 2,
    TIER_ELITE: 3,
    TIER_QUANT: 4,
    TIER_INSTITUTIONAL: 5,
}

# Not sold as self-serve-ready on pricing cards (external dependency).
BLOCKED_EXTERNAL_LAUNCH_IDS: dict[int, str] = {
    33: "Telegram external push — local alerts only until TELEGRAM_BOT_TOKEN configured",
    38: "Licensed MVRV feed — reference/proxy only until vendor configured",
}

MOST_POPULAR_TIER: Final[str] = "elite"

# launch_number -> (minimum_tier, surface_path, button_or_route, gated, requires_auth)
_DISTRIBUTION: dict[int, tuple[str, str, str, bool, bool]] = {
    1: (TIER_FLOOR, "/", "Try Oracle Free / Command Home", False, False),
    2: (TIER_FREE, "/#try-oracle", "Get Decision", True, False),
    3: (TIER_PRO, "/dashboard?lens=prove", "Share Proof / Certificate", True, True),
    4: (TIER_FLOOR, "/oracle-accuracy", "Public Accuracy Ledger", False, False),
    5: (TIER_ELITE, "/api/launch57/net-edge", "Cost Autopsy / Net-Edge", True, True),
    6: (TIER_FLOOR, "/#trust-pulse", "Evidence class badge", False, False),
    7: (TIER_FLOOR, "/#trust-pulse", "Regime / Compass summary", False, False),
    8: (TIER_FLOOR, "/dashboard?lens=prove", "Beginner mode toggle", False, False),
    9: (TIER_PRO, "/dashboard?lens=operate", "Cross-signal confirmation", True, True),
    10: (TIER_PRO, "/dashboard?lens=operate", "Contradiction detection", True, True),
    11: (TIER_ELITE, "/dashboard?lens=desk", "Smart Money actionability", True, True),
    12: (TIER_ELITE, "/dashboard?lens=desk", "Conviction engine", True, True),
    13: (TIER_ELITE, "/dashboard?lens=desk", "Accumulation / distribution", True, True),
    14: (TIER_ELITE, "/dashboard?lens=desk", "Token screener (smart money)", True, True),
    15: (TIER_ELITE, "/dashboard?lens=desk", "Entity-aware wallet intel", True, True),
    16: (TIER_ELITE, "/dashboard?lens=desk", "Exchange flow intel", True, True),
    17: (TIER_ELITE, "/dashboard?lens=desk", "Whale ratio filter", True, True),
    18: (TIER_ELITE, "/dashboard?lens=desk", "Whale movement alerts", True, True),
    19: (TIER_ELITE, "/dashboard?lens=desk", "Inter-entity flow (limited)", True, True),
    20: (TIER_ELITE, "/dashboard?lens=desk", "Address labels & cohorts", True, True),
    21: (TIER_PRO, "/dashboard?lens=operate", "Spot metrics suite", True, True),
    22: (TIER_FLOOR, "/api/launch57/real-time-prices", "Live price + freshness badge", False, False),
    23: (TIER_PRO, "/dashboard?lens=operate", "OHLCV depth", True, True),
    24: (TIER_PRO, "/dashboard?lens=operate", "Quote + symbol metadata", True, True),
    25: (TIER_PRO, "/dashboard?lens=operate", "Futures OI", True, True),
    26: (TIER_PRO, "/dashboard?lens=operate", "Funding rate intel", True, True),
    27: (TIER_PRO, "/dashboard?lens=operate", "Liquidation heatmap (light)", True, True),
    28: (TIER_PRO, "/dashboard?lens=operate", "Taker buy/sell + leverage", True, True),
    29: (TIER_PRO, "/dashboard?lens=operate", "Derivatives sentiment", True, True),
    30: (TIER_ELITE, "/dashboard?lens=desk", "Order book L1+", True, True),
    31: (TIER_ELITE, "/dashboard?lens=desk", "Token screener (market)", True, True),
    32: (TIER_PRO, "/dashboard?lens=operate", "Watchlists", True, True),
    33: (TIER_PRO, "/dashboard?lens=operate", "Smart Alerts (local)", True, True),
    34: (TIER_PRO, "/dashboard?lens=operate", "Signal → explanation", True, True),
    35: (TIER_PRO, "/dashboard?lens=operate", "Price-move explanation", True, True),
    36: (TIER_ELITE, "/api/launch57/ai-copilot", "AI Research Copilot", True, True),
    37: (TIER_QUANT, "/api/launch57/cross-market", "Cross-market engine", True, True),
    38: (TIER_ELITE, "/api/launch57/mvrv-suite", "MVRV / Z-Score (licensed path)", True, True),
    39: (TIER_ELITE, "/dashboard?lens=desk", "Point-in-time metrics", True, True),
    40: (TIER_ELITE, "/dashboard?lens=desk", "Data provenance visible", True, True),
    41: (TIER_FLOOR, "/#trust-pulse", "Freshness / stale labels", False, False),
    42: (TIER_PRO, "/status", "Unified exchange connector status", True, False),
    43: (TIER_QUANT, "/api/launch57/spot-perp-arbitrage", "Spot–perp arbitrage (Net-Edge)", True, True),
    44: (TIER_PRO, "/dashboard?lens=prove", "Shareable decision card", True, True),
    45: (TIER_FLOOR, "/oracle-accuracy", "Shareable outcome sample", False, False),
    46: (TIER_FLOOR, "/status", "Guest trust surface", False, False),
    47: (TIER_FLOOR, "/#trust-pulse", "One-click risk disclosure", False, False),
    48: (TIER_FLOOR, "/#trust-pulse", "Abstain / reject reasons", False, False),
    49: (TIER_PRO, "/api/launch57/decision-history", "Personal decision history", True, True),
    50: (TIER_PRO, "/api/launch57/discipline-mirror", "Discipline mirror (light)", True, True),
    51: (TIER_FREE, "/dashboard?lens=operate", "Research brief (limited)", True, True),
    52: (TIER_FLOOR, "/api/launch57/capability-library", "Capability library (name/purpose)", False, False),
    53: (TIER_ELITE, "/api/launch57/wallet-due-diligence", "Instant Wallet DD", True, True),
    54: (TIER_ELITE, "/api/launch57/token-due-diligence", "Instant Token DD", True, True),
    55: (TIER_ELITE, "/dashboard?lens=desk", "Pump & dump alerts", True, True),
    56: (TIER_QUANT, "/api/launch57/suspicious-flags", "Suspicious activity flags", True, True),
    57: (TIER_QUANT, "/api/launch57/exchange-transparency", "Exchange transparency indicators", True, True),
}

_INSTITUTIONAL_ONLY: dict[int, tuple[str, str, str]] = {
    # B2B feed hero — institutional contract only (not on self-serve cards as purchasable SKU).
}


@lru_cache(maxsize=1)
def _register_names() -> dict[int, str]:
    if not _REGISTER_PATH.exists():
        return {i: f"Launch-{i}" for i in range(1, 58)}
    data = json.loads(_REGISTER_PATH.read_text(encoding="utf-8"))
    out: dict[int, str] = {}
    for row in data.get("launch57_register", []):
        n = row.get("launch_number")
        if isinstance(n, int):
            out[n] = str(row.get("launch_name") or f"Launch-{n}")
    return out


def launch57_distribution_row(launch_number: int) -> dict[str, Any]:
    if launch_number not in range(1, 58):
        raise ValueError(f"launch_number out of scope: {launch_number}")
    tier, surface, button, gated, requires_auth = _DISTRIBUTION[launch_number]
    name = _register_names().get(launch_number, f"Launch-{launch_number}")
    blocked = launch_number in BLOCKED_EXTERNAL_LAUNCH_IDS
    status = "BLOCKED_EXTERNAL" if blocked else "PENDING_VERIFICATION"
    return {
        "launch_number": launch_number,
        "launch_name": name,
        "surface_path": surface,
        "button_or_route": button,
        "tier": tier,
        "minimum_tier": tier if tier != TIER_FLOOR else TIER_FREE,
        "gated": gated,
        "requires_auth": requires_auth,
        "blocked_external": blocked,
        "blocked_external_reason": BLOCKED_EXTERNAL_LAUNCH_IDS.get(launch_number),
        "status": status,
        "pricing_card_eligible": tier != TIER_INSTITUTIONAL and not blocked,
        "not_sold_self_serve_label": (
            "غير مدرج في الإطلاق الذاتي" if blocked else None
        ),
    }


def build_launch57_distribution_table() -> list[dict[str, Any]]:
    return [launch57_distribution_row(i) for i in range(1, 58)]


def minimum_tier_for(launch_item_id: int) -> str:
    row = launch57_distribution_row(launch_item_id)
    return str(row["minimum_tier"])


def minimum_paid_tier_by_launch_item() -> dict[int, str]:
    out: dict[int, str] = {}
    for i in range(1, 58):
        mt = minimum_tier_for(i)
        if plan_rank(mt) >= plan_rank(TIER_PRO):
            out[i] = mt
    return out


def tier_satisfies(launch_item_id: int, effective_tier: str | None) -> bool:
    row = launch57_distribution_row(launch_item_id)
    required = str(row["minimum_tier"])
    effective = normalize_plan(effective_tier or "free")
    if row["tier"] == TIER_FLOOR:
        return True
    return plan_rank(effective) >= plan_rank(required)


def enforce_launch57_tier_access(
    *,
    launch_item_id: int,
    params: dict[str, Any] | None = None,
    subscription: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Server-side tier gate for Launch-57 distribution (extends billing entitlement)."""
    from launch57.billing_entitlement_common import apply_entitlement_gated_params

    p = apply_entitlement_gated_params(params, subscription=subscription)
    resolution = p.get("_entitlement_resolution") or {}
    row = launch57_distribution_row(launch_item_id)
    effective = normalize_plan(str(p.get("tier") or "free"))
    anonymous = bool(resolution.get("anonymous"))

    allowed = tier_satisfies(launch_item_id, effective)
    reason = "ok" if allowed else f"minimum_tier_{row['minimum_tier']}_required"

    if anonymous and row.get("requires_auth"):
        allowed = False
        reason = "authentication_required"

    if anonymous and row["tier"] not in (TIER_FLOOR,) and plan_rank(effective) < plan_rank(TIER_FREE):
        allowed = False
        reason = "anonymous_paid_or_private_surface"

    if resolution.get("unverified_paid_claim"):
        allowed = False
        reason = "unverified_paid_tier_claim"

    return {
        "launch_item_id": launch_item_id,
        "allowed": allowed,
        "fail_closed": not allowed,
        "reason": reason,
        "effective_tier": effective,
        "minimum_tier": row["minimum_tier"],
        "distribution_row": row,
        "entitlement_resolution": resolution,
        "server_side_enforced": True,
    }


def pricing_card_features_for_tier(plan_id: str) -> list[dict[str, Any]]:
    """Honest pricing bullets — only capabilities at or below plan with visible surface."""
    plan = normalize_plan(plan_id)
    rank = plan_rank(plan)
    feats: list[dict[str, Any]] = []
    for row in build_launch57_distribution_table():
        if plan_rank(str(row["minimum_tier"])) > rank:
            continue
        if row["blocked_external"]:
            feats.append(
                {
                    "launch_number": row["launch_number"],
                    "label": row["launch_name"],
                    "honesty": "not_in_self_serve_launch",
                    "blocked_external_reason": row["blocked_external_reason"],
                }
            )
            continue
        feats.append(
            {
                "launch_number": row["launch_number"],
                "label": row["launch_name"],
                "surface_path": row["surface_path"],
                "honesty": "visible_surface",
            }
        )
    return feats


def distribution_closure_report() -> dict[str, Any]:
    table = build_launch57_distribution_table()
    missing_surface = [r for r in table if not r.get("surface_path")]
    ungated_paid = [
        r
        for r in table
        if plan_rank(str(r["minimum_tier"])) >= plan_rank(TIER_PRO) and not r.get("gated")
    ]
    blocked = [
        {
            "launch_number": r["launch_number"],
            "launch_name": r["launch_name"],
            "reason": r["blocked_external_reason"],
        }
        for r in table
        if r.get("blocked_external")
    ]
    return {
        "MOST_POPULAR_TIER": MOST_POPULAR_TIER,
        "MISSING_SURFACE": missing_surface,
        "UNGATED_PAID_FEATURES": ungated_paid,
        "BLOCKED_EXTERNAL_NOT_SOLD_AS_READY": blocked,
        "launch57_rows": len(table),
        "table_complete": len(table) == 57 and len(missing_surface) == 0,
    }
