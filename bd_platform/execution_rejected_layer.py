"""
Execution Rejected Layer — registry and E2E for insight-only alternatives.

NOT standalone execution modules — rejected features return status stubs
and point to rule-based insight alternatives across existing layers.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ExecutionRejected")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")

REJECTED_EXECUTION_FEATURES: dict[int, dict[str, Any]] = {
    78: {"alternative_route": "/intelligence/impact-analysis", "layer": "whales_institutional"},
    119: {"alternative_route": "/radar/on-chain/gas-alert", "layer": "advanced_ta_risk"},
    126: {"alternative_route": "/oracle/on-chain/dex-risk", "layer": "advanced_ta_risk"},
    127: {"alternative_route": "/radar/technical/orderbook-inefficiency", "layer": "advanced_ta_risk"},
    130: {"alternative_route": "/oracle/on-chain/tx-risk", "layer": "onchain_platform"},
    131: {"alternative_route": "/portfolio/dust-analysis", "layer": "onchain_platform"},
    139: {"alternative_route": "/portfolio/stress-alert", "layer": "onchain_platform"},
    147: {"alternative_route": "/signal-engine/status", "layer": "data_sources"},
    152: {"alternative_route": "/alerts/execution-status", "layer": "data_sources"},
    155: {"alternative_route": "/intelligence/stat-arb", "layer": "intelligence_analysis"},
    164: {"alternative_route": "/portfolio/liquidity-impact", "layer": "risk_infrastructure"},
    166: {"alternative_route": "/brokerage/status", "layer": "risk_infrastructure"},
    188: {"alternative_route": "/portfolio/risk-alert", "layer": "arbitrage_portfolio_ux"},
    193: {"alternative_route": "/intelligence/arbitrage", "layer": "derivatives_ta_research"},
    195: {"alternative_route": "/intelligence/strategy-simulator", "layer": "derivatives_ta_research"},
    211: {"alternative_route": "/portfolio/cross-margin-risk", "layer": "onchain_defi_sources"},
    212: {"alternative_route": "/portfolio/hedge-analysis", "layer": "onchain_defi_sources"},
    213: {"alternative_route": "/portfolio/capital-allocation", "layer": "onchain_defi_sources"},
    214: {"alternative_route": "/intelligence/arbitrage", "layer": "onchain_defi_sources"},
    215: {"alternative_route": "/oracle/on-chain/gas-profile", "layer": "onchain_defi_sources"},
    216: {"alternative_route": "/oracle/on-chain/whale/behavior-analysis", "layer": "onchain_defi_sources"},
    217: {"alternative_route": "/intelligence/best-venue-analysis", "layer": "intelligence_market_extensions"},
    221: {"alternative_route": "/radar/technical/slippage-analysis", "layer": "intelligence_market_extensions"},
    226: {"alternative_route": "/radar/events/launch-analysis", "layer": "intelligence_market_extensions"},
    227: {"alternative_route": "/intelligence/etf-premium", "layer": "intelligence_market_extensions"},
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("execution rejected seed load failed: %s", exc)
        return {}


def execution_rejected_registry(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Registry of rejected execution features and their insight-only alternatives."""
    seed = seed or _load_seed()
    return {
        "ok": True,
        "insight_only_platform": True,
        "no_execution_modules": True,
        "no_trade_api_keys": True,
        "no_wallet_connection": True,
        "feature_count": len(REJECTED_EXECUTION_FEATURES),
        "features": [
            {"feature_ref": ref, **meta}
            for ref, meta in sorted(REJECTED_EXECUTION_FEATURES.items())
        ],
        "disclosure_ref": 57,
        "timestamp": _utcnow(),
    }


def whale_behavior_analysis_216(
    *,
    wallet: str = "0x1234...5678",
    buy_usd: float = 2_000_000,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#216 alternative — multi-angle whale behavior insight (counter-trading rejected)."""
    from bd_platform.onchain_defi_sources_layer import whale_contrarian_insight_216

    result = whale_contrarian_insight_216(wallet=wallet, buy_usd=buy_usd, seed=seed)
    result["route"] = "/oracle/on-chain/whale/behavior-analysis"
    result["alternative_to"] = "whale_counter_trading_ai_strategy"
    return result


def run_execution_rejected_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    from bd_platform.whales_institutional_layer import (
        build_impact_analysis_78,
        execution_routing_status_78,
    )

    status_78 = execution_routing_status_78(seed=seed)
    impact = build_impact_analysis_78(order_usd=500_000, venue="binance", seed=seed)
    checks.append({"id": "78_impact", "passed": status_78["rejected"] and impact["insight_only"] is True})

    from bd_platform.advanced_ta_risk_layer import (
        dex_front_running_risk_126,
        gas_spike_alert_119,
        orderbook_inefficiency_insight_127,
    )

    gas = gas_spike_alert_119(seed=seed)
    checks.append({"id": "119_gas", "passed": gas["execution_rejected"] is True})
    dex = dex_front_running_risk_126(seed=seed)
    checks.append({"id": "126_dex", "passed": dex["execution_rejected"] is True})
    ob = orderbook_inefficiency_insight_127(seed=seed)
    checks.append({"id": "127_orderbook", "passed": ob["analysis_not_exploitation"] is True})

    from bd_platform.onchain_platform_layer import (
        analyze_dust_assets_131,
        portfolio_stress_alert_139,
        transaction_risk_insight_130,
    )

    tx = transaction_risk_insight_130(seed=seed)
    checks.append({"id": "130_tx", "passed": tx["execution_rejected"] is True})
    dust = analyze_dust_assets_131(seed=seed)
    checks.append({"id": "131_dust", "passed": dust["execution_rejected"] is True})
    stress = portfolio_stress_alert_139(seed=seed)
    checks.append({"id": "139_stress", "passed": stress["panic_button_rejected"] is True})

    from bd_platform.data_sources_layer import alerts_execution_status_152, signal_engine_status_147

    checks.append({"id": "147_trading_engine", "passed": signal_engine_status_147(seed=seed)["trading_engine_rejected"] is True})
    checks.append({"id": "152_alerts", "passed": alerts_execution_status_152(seed=seed)["auto_execution_rejected"] is True})

    from bd_platform.intelligence_analysis_layer import stat_arb_insight_155

    stat = stat_arb_insight_155(seed=seed)
    checks.append({"id": "155_stat_arb", "passed": stat["no_entry_signal"] is True})

    from bd_platform.risk_infrastructure_layer import brokerage_rejected_status_166, liquidity_impact_warning_164

    liq = liquidity_impact_warning_164(seed=seed)
    checks.append({"id": "164_liquidity", "passed": liq["panic_button_rejected"] is True})
    checks.append({"id": "166_brokerage", "passed": brokerage_rejected_status_166(seed=seed)["brokerage_rejected"] is True})

    from bd_platform.arbitrage_portfolio_ux_layer import risk_alert_user_confirmation_188

    alt_188 = risk_alert_user_confirmation_188(seed=seed)
    checks.append({"id": "188_execution", "passed": alt_188["auto_execution_rejected"] is True})

    from bd_platform.derivatives_ta_research_layer import (
        auto_arbitrage_rejected_status_193,
        strategy_simulator_195,
    )

    checks.append({"id": "193_auto_arb", "passed": auto_arbitrage_rejected_status_193(seed=seed)["auto_arbitrage_rejected"] is True})
    sim = strategy_simulator_195(seed=seed)
    checks.append({"id": "195_simulator", "passed": sim["account_linking_rejected"] is True})

    from bd_platform.onchain_defi_sources_layer import (
        analyze_predictive_arbitrage_210,
        analyze_triangular_arbitrage_214,
        capital_allocation_insight_213,
        cross_margin_risk_alert_211,
        flash_loan_gas_rejected_status_215,
        hedge_effectiveness_analysis_212,
    )

    checks.append({"id": "211_cross_margin", "passed": cross_margin_risk_alert_211(seed=seed)["safeguard_rejected"] is True})
    checks.append({"id": "212_hedge", "passed": hedge_effectiveness_analysis_212(seed=seed)["rehedging_rejected"] is True})
    checks.append({"id": "213_capital", "passed": capital_allocation_insight_213(seed=seed)["auto_balancing_rejected"] is True})
    checks.append({"id": "214_triangular", "passed": analyze_triangular_arbitrage_214(seed=seed)["in_flight_modification_rejected"] is True})
    checks.append({"id": "215_flash", "passed": flash_loan_gas_rejected_status_215(seed=seed)["flash_loans_rejected"] is True})

    whale = whale_behavior_analysis_216(seed=seed)
    checks.append({"id": "216_whale", "passed": whale["counter_trading_rejected"] is True})

    registry = execution_rejected_registry(seed=seed)
    checks.append({"id": "registry", "passed": registry["feature_count"] == len(REJECTED_EXECUTION_FEATURES)})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
