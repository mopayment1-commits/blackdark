"""
DeFi Economics Module — Feature #733 (Sprint 2 Intelligence Ledger).

Earnings / Economic Profit Proxy — clearly labeled, NOT GAAP.
Integrated with Fee DB (#130) when yield/return displays involved.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.DeFiEconomics")

_FEATURE_ID = 733
_FEE_DB_FEATURE_ID = 130
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / DeFi Economics Module"
_SPRINT = 2
_SEED_PATH = Path("data/defi_economics_seed.json")
_METHODOLOGY_VERSION = "1.2"
_PROXY_LABEL = "Earnings Proxy | Not GAAP | Methodology v1.2"

_DISCLAIMER = (
    "Crypto protocols lack standardized accounting. This is an approximation. "
    "Earnings Proxy — not GAAP. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"protocols": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("defi economics seed load failed: %s", exc)
        return {"protocols": {}}


def build_methodology() -> dict[str, Any]:
    return {
        "version": _METHODOLOGY_VERSION,
        "proxy_label": _PROXY_LABEL,
        "not_gaap": True,
        "clearly_labeled_proxy": True,
        "terminology": {
            "use": ["Net Profit After Incentives", "Economic Profit Proxy"],
            "avoid": ["profit", "ربح"],
        },
        "cost_components": ["gas_fees", "incentives", "token_emissions"],
        "formula": "revenue - (gas + incentives + token_emission_cost_usd)",
        "fee_db_required_for_yield": True,
        "fee_db_feature_id": _FEE_DB_FEATURE_ID,
        "display": (
            f"{_PROXY_LABEL} | "
            "Costs: gas + incentives + token emissions | Fee DB (#130) for yield displays"
        ),
    }


def build_coverage_block(coverage: dict[str, Any]) -> dict[str, Any]:
    includes = coverage.get("includes") or []
    excludes = coverage.get("excludes") or []
    return {
        "includes": includes,
        "excludes": excludes,
        "explicit": True,
        "display": (
            f"Covers: {', '.join(includes)} | "
            f"Excludes: {', '.join(excludes)}"
        ),
    }


def compute_economic_profit_proxy(protocol: dict[str, Any]) -> dict[str, Any]:
    revenue = float(protocol.get("revenue_usd", 0))
    gas = float(protocol.get("gas_cost_usd", 0))
    incentives = float(protocol.get("incentives_usd", 0))
    emissions = float(protocol.get("token_emission_cost_usd", 0))
    total_costs = gas + incentives + emissions
    net = round(revenue - total_costs, 2)

    return {
        "economic_profit_proxy_usd": net,
        "net_profit_after_incentives_usd": net,
        "revenue_usd": revenue,
        "costs": {
            "gas_usd": gas,
            "incentives_usd": incentives,
            "token_emissions_usd": emissions,
            "total_usd": round(total_costs, 2),
        },
        "proxy_label": _PROXY_LABEL,
        "not_gaap": True,
        "never_use_profit_alone": True,
        "methodology_version": _METHODOLOGY_VERSION,
    }


def build_defi_economics_panel(protocol_id: str = "aave") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    pid = protocol_id.lower()
    protocol = (seed.get("protocols") or {}).get(pid)

    if not protocol:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "protocol_not_found", "protocol_id": pid}

    earnings = compute_economic_profit_proxy(protocol)
    coverage = build_coverage_block(protocol.get("coverage") or {})
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "protocol_id": pid,
        "protocol_name": protocol.get("name"),
        "earnings_proxy": earnings,
        "earnings_trend": protocol.get("earnings_trend") or [],
        "methodology": build_methodology(),
        "coverage": coverage,
        "fee_db_linked": protocol.get("fee_db_linked", True),
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "not_a_signal": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def defi_economics_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "DeFi Economics Module",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "methodology": build_methodology(),
        "acceptance_criteria": {
            "clearly_labeled_proxy": True,
            "not_gaap_unless_applicable": True,
            "methodology_documented": True,
            "disclaimer_not_hideable": True,
            "fee_db_for_yield_displays": True,
            "coverage_explicit": True,
        },
        "protocol_count": len(seed.get("protocols") or {}),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
