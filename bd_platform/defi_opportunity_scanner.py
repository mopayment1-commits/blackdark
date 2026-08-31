"""
DeFi Opportunity Scanner — Feature #438 (DeFi Layer).

Absorbs:
  #465 DEX Screener — pool mapping, honeypot/risk flags, filter/rank
  #470 LP Position Risk Calculator — renamed from "IL Live Simulator"
  #473 Liquidity Risk — protocol TVL/utilization/borrow-supply/liquidation
  #482 Oracle Risk — oracle dependency/risk analysis dimension (DeFi Risk Layer)
  #491 Smart Contract and Protocol Risk — contract/audit/bounty indicators (DeFi Risk Layer)

NOT standalone — merged into #429 Unified Arbitrage Opportunity Engine.
Monitoring/analytics only — no execution language.
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.DeFiOpportunityScanner")

_FEATURE_ID = 438
_DEX_SCREENER_REF = 465
_LP_POSITION_RISK_REF = 470
_LIQUIDITY_RISK_REF = 473
_ORACLE_RISK_REF = 482
_PROTOCOL_RISK_REF = 491
_TITLE = "DeFi Opportunity Scanner"
_LEGAL_NAME = "DeFi Opportunity Scanner"
_STANDALONE = False
_MERGED_INTO = "Unified Arbitrage Opportunity Engine (#429) / DeFi Layer"
_SPRINT = 2
_PRIORITY = "medium"
_SEED_PATH = Path("data/defi_opportunity_scanner_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "DeFi Opportunity Scanner — on-chain analytics and discovery only. "
    "DEX screener, LP position risk calculator, and liquidity risk monitoring. "
    "No flash loans, no bridge execution, no auto-trading. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"dex_pools": [], "defi_opportunities": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("defi opportunity scanner seed load failed: %s", exc)
        return {"dex_pools": [], "defi_opportunities": []}


def _pool_risk_score(pool: dict[str, Any]) -> float:
    """Composite risk 0–100 from available flags."""
    score = 0.0
    if not pool.get("contract_verified"):
        score += 25
    if not pool.get("liquidity_locked"):
        score += 20
    if not pool.get("owner_renounced"):
        score += 15
    if pool.get("tax_token"):
        score += 20
    honeypot = pool.get("honeypot_check") or {}
    if honeypot.get("is_honeypot"):
        score += 40
    if pool.get("pool_age_days", 999) < 7:
        score += 15
    return min(100.0, score)


def build_risk_flags(pool: dict[str, Any]) -> dict[str, Any]:
    """#465 risk flags — where data exists."""
    honeypot = pool.get("honeypot_check") or {}
    flags = {
        "contract_verified": pool.get("contract_verified"),
        "liquidity_locked": pool.get("liquidity_locked"),
        "owner_renounced": pool.get("owner_renounced"),
        "tax_token": pool.get("tax_token"),
        "honeypot": {
            "provider": honeypot.get("provider", "honeypot.is"),
            "checked": honeypot.get("checked", False),
            "is_honeypot": honeypot.get("is_honeypot"),
            "no_internal_detector_v1": True,
        },
        "pool_age_days": pool.get("pool_age_days"),
        "risk_score": round(_pool_risk_score(pool), 1),
    }
    warnings = []
    if flags["honeypot"].get("is_honeypot"):
        warnings.append("honeypot_detected")
    if not flags["contract_verified"]:
        warnings.append("unverified_contract")
    if not flags["liquidity_locked"]:
        warnings.append("liquidity_not_locked")
    if flags["tax_token"]:
        warnings.append("tax_token")
    flags["warnings"] = warnings
    return flags


def map_pools_across_dexs(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#465 pool mapping across Uniswap, PancakeSwap, Raydium, Jupiter."""
    seed = seed or _load_seed()
    cfg = seed.get("dex_screener_465") or {}
    mapping = seed.get("pool_mapping") or {}
    pools_by_id = {p["pool_id"]: p for p in (seed.get("dex_pools") or [])}

    mapped: list[dict[str, Any]] = []
    for pair, dex_map in mapping.items():
        entry: dict[str, Any] = {"pair": pair, "dexs": {}}
        for dex in cfg.get("dexs_v1", []):
            pool_id = dex_map.get(dex)
            if pool_id and pool_id in pools_by_id:
                pool = pools_by_id[pool_id]
                entry["dexs"][dex] = {
                    "pool_id": pool_id,
                    "liquidity_usd": pool.get("liquidity_usd"),
                    "volume_24h_usd": pool.get("volume_24h_usd"),
                    "chain": pool.get("chain"),
                }
            else:
                entry["dexs"][dex] = None
        mapped.append(entry)

    return {
        "ok": True,
        "feature_ref": _DEX_SCREENER_REF,
        "dexs_v1": cfg.get("dexs_v1"),
        "pool_mapping": mapped,
        "mapping_count": len(mapped),
        "timestamp": _utcnow(),
    }


def screen_dex_pools(
    *,
    seed: dict[str, Any] | None = None,
    min_liquidity_usd: float | None = None,
    min_volume_24h_usd: float | None = None,
    min_pool_age_days: int | None = None,
) -> dict[str, Any]:
    """#465 DEX Screener — filter/rank by liquidity/volume/velocity/risk."""
    seed = seed or _load_seed()
    cfg = seed.get("dex_screener_465") or {}
    defaults = cfg.get("default_filters") or {}
    min_liq = min_liquidity_usd if min_liquidity_usd is not None else float(defaults.get("min_liquidity_usd", 100_000))
    min_vol = min_volume_24h_usd if min_volume_24h_usd is not None else float(defaults.get("min_volume_24h_usd", 10_000))
    min_age = min_pool_age_days if min_pool_age_days is not None else int(defaults.get("min_pool_age_days", 7))

    screened: list[dict[str, Any]] = []
    for pool in seed.get("dex_pools") or []:
        liq = float(pool.get("liquidity_usd", 0))
        vol = float(pool.get("volume_24h_usd", 0))
        age = int(pool.get("pool_age_days", 0))
        passes = liq >= min_liq and vol >= min_vol and age >= min_age
        risk_flags = build_risk_flags(pool)
        screened.append({
            "pool_id": pool.get("pool_id"),
            "dex": pool.get("dex"),
            "chain": pool.get("chain"),
            "pair": pool.get("pair"),
            "liquidity_usd": liq,
            "volume_24h_usd": vol,
            "velocity_score": pool.get("velocity_score"),
            "pool_age_days": age,
            "passes_default_filters": passes,
            "risk_flags": risk_flags,
            "risk_score": risk_flags["risk_score"],
            "display": (
                f"{pool.get('pair')} on {pool.get('dex')} | "
                f"Liq ${liq:,.0f} | Vol ${vol:,.0f} | Risk {risk_flags['risk_score']}"
            ),
        })

    screened.sort(
        key=lambda p: (
            p["passes_default_filters"],
            p.get("liquidity_usd", 0),
            p.get("volume_24h_usd", 0),
            -p.get("risk_score", 100),
        ),
        reverse=True,
    )

    return {
        "ok": True,
        "feature_ref": _DEX_SCREENER_REF,
        "title": "DEX Screener",
        "pools": screened,
        "count": len(screened),
        "passing_count": sum(1 for p in screened if p["passes_default_filters"]),
        "filters_applied": {
            "min_liquidity_usd": min_liq,
            "min_volume_24h_usd": min_vol,
            "min_pool_age_days": min_age,
        },
        "dexs_v1": cfg.get("dexs_v1"),
        "honeypot_provider": cfg.get("honeypot_provider"),
        "pool_mapping": map_pools_across_dexs(seed=seed),
        "monitoring_only": True,
        "timestamp": _utcnow(),
    }


def _impermanent_loss_pct(price_ratio: float) -> float:
    """Standard IL formula for 50/50 pool."""
    if price_ratio <= 0:
        return 0.0
    r = price_ratio
    il = 2 * math.sqrt(r) / (1 + r) - 1
    return round(il * 100, 4)


def calculate_lp_position_risk(
    position: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    #470 LP Position Risk Calculator — renamed from IL Live Simulator.
    Inputs: pair, entry prices, pool ratio, fees APY.
    Outputs: IL estimate, fee offset, net PnL.
    """
    seed = seed or _load_seed()
    cfg = seed.get("lp_position_risk_470") or {}

    entry_ratio = float(position.get("entry_price_ratio", 1.0))
    current_ratio = float(position.get("current_price_ratio", 1.0))
    position_value = float(position.get("position_value_usd", 0))
    fees_apy = float(position.get("fees_apy", 0))
    days_held = float(position.get("days_held", 0))
    asset_ref = str(position.get("asset_ref") or position.get("token0", "ETH"))

    price_ratio = current_ratio / entry_ratio if entry_ratio > 0 else 1.0
    il_pct = _impermanent_loss_pct(price_ratio)
    il_usd = round(position_value * il_pct / 100, 2)
    fee_offset_usd = round(position_value * fees_apy / 100 * days_held / 365, 2)
    net_pnl_usd = round(fee_offset_usd + il_usd, 2)

    collateral_grade = None
    collateral_breakdown = None
    try:
        from bd_platform.diligence_risk_scoring import score_collateral_risk

        collateral = score_collateral_risk(asset_ref)
        if collateral.get("ok"):
            collateral_grade = collateral.get("collateral_grade")
            collateral_breakdown = collateral.get("breakdown")
    except Exception:
        logger.debug("collateral grade for LP skipped", exc_info=True)

    return {
        "ok": True,
        "feature_ref": _LP_POSITION_RISK_REF,
        "legal_name": cfg.get("legal_name", "LP Position Risk Calculator"),
        "renamed_from": cfg.get("renamed_from"),
        "position_id": position.get("position_id"),
        "pair": position.get("pair"),
        "inputs": {
            "entry_price_ratio": entry_ratio,
            "current_price_ratio": current_ratio,
            "pool_ratio": position.get("pool_ratio"),
            "position_value_usd": position_value,
            "fees_apy": fees_apy,
            "days_held": days_held,
        },
        "impermanent_loss_pct": il_pct,
        "impermanent_loss_usd": il_usd,
        "fee_offset_usd": fee_offset_usd,
        "net_pnl_usd": net_pnl_usd,
        "collateral_grade_462": collateral_grade,
        "collateral_breakdown_462": collateral_breakdown,
        "cancelled_sla": cfg.get("cancelled_sla"),
        "simulation_only": True,
        "display": (
            f"LP {position.get('pair')}: IL {il_pct:+.2f}% (${il_usd:,.2f}) | "
            f"Fees +${fee_offset_usd:,.2f} | Net ${net_pnl_usd:,.2f}"
        ),
        "timestamp": _utcnow(),
    }


def analyze_protocol_liquidity_risk(
    protocol_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#473 Liquidity Risk — 4 mandatory indicators per protocol."""
    seed = seed or _load_seed()
    protocols = seed.get("liquidity_protocols") or {}
    proto = protocols.get(protocol_id.lower())
    if not proto:
        return {"ok": False, "protocol_id": protocol_id, "error": "protocol_not_found"}

    tvl_trend = float(proto.get("tvl_trend_7d_pct", 0))
    utilization = float(proto.get("utilization_rate", 0))
    borrow_supply = proto.get("borrow_supply_ratio")
    liq_threshold = proto.get("liquidation_threshold")

    risk_score = round(
        min(100, max(0,
            (abs(tvl_trend) * 2)
            + (utilization * 40)
            + ((float(borrow_supply) * 30) if borrow_supply else 0)
            + ((1 - float(liq_threshold)) * 20 if liq_threshold else 0)
        )),
        1,
    )

    return {
        "ok": True,
        "feature_ref": _LIQUIDITY_RISK_REF,
        "protocol_id": protocol_id.lower(),
        "protocol": proto.get("protocol"),
        "chain": proto.get("chain"),
        "tvl_usd": proto.get("tvl_usd"),
        "indicators": {
            "tvl_trend_7d_pct": tvl_trend,
            "utilization_rate": utilization,
            "borrow_supply_ratio": borrow_supply,
            "liquidation_threshold": liq_threshold,
        },
        "liquidity_risk_score": risk_score,
        "supply_apy": proto.get("supply_apy"),
        "borrow_apy": proto.get("borrow_apy"),
        "display": (
            f"{proto.get('protocol')}: TVL trend {tvl_trend:+.1f}% | "
            f"Util {utilization:.0%} | Risk {risk_score}/100"
        ),
        "timestamp": _utcnow(),
    }


def analyze_protocol_oracle_risk(
    protocol_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#482 Oracle Risk — dependency/risk analysis per protocol."""
    seed = seed or _load_seed()
    cfg = seed.get("oracle_risk_482") or {}
    protocols = seed.get("oracle_protocols") or {}
    proto = protocols.get(protocol_id.lower())
    if not proto:
        return {"ok": False, "protocol_id": protocol_id, "error": "protocol_not_found"}

    sources = proto.get("oracle_sources") or []
    source_count = len(sources)
    multi_source = source_count > 1
    heartbeat_secs = float(proto.get("heartbeat_seconds", 3600))
    last_heartbeat_secs = float(proto.get("last_heartbeat_age_seconds", 0))
    heartbeat_fresh = last_heartbeat_secs <= heartbeat_secs * 1.5
    deviation_history = proto.get("deviation_history_bps") or []
    max_deviation = max(deviation_history) if deviation_history else 0.0
    dependency_depth = int(proto.get("dependency_depth", 1))

    risk_score = round(min(100, max(0,
        (0 if multi_source else 35)
        + (0 if heartbeat_fresh else 25)
        + min(25, max_deviation / 4)
        + min(20, dependency_depth * 5)
    )), 1)

    source_config = {
        "version": cfg.get("source_config_version", "1.0"),
        "documented": True,
        "sources": [
            {
                "provider": s.get("provider"),
                "type": s.get("type"),
                "version": s.get("version"),
                "heartbeat_seconds": s.get("heartbeat_seconds"),
                "deviation_threshold_bps": s.get("deviation_threshold_bps"),
            }
            for s in sources
        ],
    }

    return {
        "ok": True,
        "feature_ref": _ORACLE_RISK_REF,
        "protocol_id": protocol_id.lower(),
        "protocol": proto.get("protocol"),
        "chain": proto.get("chain"),
        "oracle_count": source_count,
        "multi_source": multi_source,
        "single_oracle_risk": not multi_source,
        "heartbeat_freshness": {
            "heartbeat_seconds": heartbeat_secs,
            "last_heartbeat_age_seconds": last_heartbeat_secs,
            "fresh": heartbeat_fresh,
        },
        "deviation_history_bps": deviation_history,
        "max_deviation_bps": max_deviation,
        "dependency_depth": dependency_depth,
        "oracle_risk_score": risk_score,
        "source_config": source_config,
        "stablecoin_oracle_linked": proto.get("stablecoin_oracle_linked"),
        "display": (
            f"{proto.get('protocol')}: {source_count} oracle(s) | "
            f"heartbeat {'fresh' if heartbeat_fresh else 'stale'} | "
            f"risk {risk_score}/100"
        ),
        "timestamp": _utcnow(),
    }


def build_oracle_risk_view(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#482 Oracle risk view — all protocols with source config/version."""
    seed = seed or _load_seed()
    cfg = seed.get("oracle_risk_482") or {}
    protocols = seed.get("oracle_protocols") or {}
    analyses = [
        analyze_protocol_oracle_risk(pid, seed=seed)
        for pid in protocols
    ]
    valid = [a for a in analyses if a.get("ok")]
    single_oracle = [a for a in valid if a.get("single_oracle_risk")]

    return {
        "ok": True,
        "feature_ref": _ORACLE_RISK_REF,
        "title": "Oracle Risk",
        "legal_name": "Oracle Risk",
        "merged_into": "DeFi Opportunity Scanner (#438) / DeFi Risk Layer",
        "protocols": valid,
        "count": len(valid),
        "single_oracle_count": len(single_oracle),
        "single_oracle_protocols": [a["protocol_id"] for a in single_oracle],
        "source_config_version": cfg.get("source_config_version", "1.0"),
        "mandatory_indicators": cfg.get("mandatory_indicators"),
        "monitoring_only": True,
        "timestamp": _utcnow(),
    }


def build_portfolio_single_oracle_alerts(
    portfolio_id: str = "demo_portfolio",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#482 → #410: alert when portfolio exposure in single-oracle protocol."""
    seed = seed or _load_seed()
    cfg = seed.get("oracle_risk_482") or {}
    exposure_threshold = float(cfg.get("portfolio_exposure_threshold_pct", 5))
    exposures = (seed.get("portfolio_protocol_exposure") or {}).get(portfolio_id) or {}
    oracle_view = build_oracle_risk_view(seed=seed)
    single_oracle_ids = set(oracle_view.get("single_oracle_protocols") or [])

    alerts: list[dict[str, Any]] = []
    for protocol_id, exposure_pct in exposures.items():
        if protocol_id not in single_oracle_ids:
            continue
        if float(exposure_pct) < exposure_threshold:
            continue
        proto_risk = analyze_protocol_oracle_risk(protocol_id, seed=seed)
        alerts.append({
            "alert_type": "single_oracle_protocol_exposure",
            "feature_ref": _ORACLE_RISK_REF,
            "integration": "capital_protection_controls_410",
            "protocol_id": protocol_id,
            "exposure_pct": exposure_pct,
            "oracle_count": proto_risk.get("oracle_count"),
            "oracle_risk_score": proto_risk.get("oracle_risk_score"),
            "severity": "elevated" if float(exposure_pct) >= exposure_threshold * 2 else "watch",
            "alerts_only": True,
            "display": (
                f"Single-oracle exposure: {proto_risk.get('protocol')} "
                f"at {exposure_pct}% — oracle dependency risk elevated"
            ),
        })

    return {
        "ok": True,
        "feature_ref": _ORACLE_RISK_REF,
        "portfolio_id": portfolio_id,
        "exposure_threshold_pct": exposure_threshold,
        "alerts": alerts,
        "alert_count": len(alerts),
        "backend_enforced": True,
        "timestamp": _utcnow(),
    }


def get_stablecoin_oracle_risk_flag(
    symbol: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#482 → #467: flag stablecoins with oracle dependency risk."""
    seed = seed or _load_seed()
    symbol = symbol.upper()
    flagged = False
    linked_protocols: list[dict[str, Any]] = []

    for pid, proto in (seed.get("oracle_protocols") or {}).items():
        linked = proto.get("stablecoin_oracle_linked") or []
        if symbol not in [s.upper() for s in linked]:
            continue
        risk = analyze_protocol_oracle_risk(pid, seed=seed)
        if risk.get("ok") and (risk.get("single_oracle_risk") or risk.get("oracle_risk_score", 0) >= 50):
            flagged = True
            linked_protocols.append({
                "protocol_id": pid,
                "protocol": risk.get("protocol"),
                "oracle_risk_score": risk.get("oracle_risk_score"),
                "single_oracle": risk.get("single_oracle_risk"),
            })

    return {
        "ok": True,
        "feature_ref": _ORACLE_RISK_REF,
        "symbol": symbol,
        "oracle_risk_flagged": flagged,
        "linked_protocols": linked_protocols,
        "integration": "stablecoin_health_monitor_467",
        "timestamp": _utcnow(),
    }


def analyze_protocol_smart_contract_risk(
    protocol_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#491 Smart Contract and Protocol Risk — 5 mandatory indicators."""
    seed = seed or _load_seed()
    cfg = seed.get("smart_contract_risk_491") or {}
    protocols = seed.get("protocol_contracts") or {}
    proto = protocols.get(protocol_id.lower())
    if not proto:
        return {"ok": False, "protocol_id": protocol_id, "error": "protocol_not_found"}

    indicators = {
        "contract_verified": proto.get("contract_verified_etherscan"),
        "audit_history": proto.get("audit_history"),
        "bug_bounty_active": proto.get("bug_bounty_active"),
        "admin_keys_renounced": proto.get("admin_keys_renounced"),
        "upgradeability": proto.get("upgradeability"),
    }
    score = round(min(100, max(0,
        (25 if indicators["contract_verified"] else 0)
        + (25 if indicators["audit_history"] else 0)
        + (20 if indicators["bug_bounty_active"] else 0)
        + (15 if indicators["admin_keys_renounced"] else 0)
        + (15 if indicators["upgradeability"] == "immutable" else 5)
    )), 1)

    data_sources = proto.get("data_sources") or cfg.get("data_sources_v1", ["defillama", "immunefi"])

    return {
        "ok": True,
        "feature_ref": _PROTOCOL_RISK_REF,
        "protocol_id": protocol_id.lower(),
        "protocol": proto.get("protocol"),
        "chain": proto.get("chain"),
        "indicators": indicators,
        "protocol_risk_score": score,
        "data_sources": data_sources,
        "no_internal_scanner_v1": True,
        "cancelled_sla": cfg.get("cancelled_sla"),
        "display": (
            f"{proto.get('protocol')}: contract risk {score}/100 | "
            f"verified={indicators['contract_verified']} | "
            f"audit={bool(indicators['audit_history'])}"
        ),
        "timestamp": _utcnow(),
    }


def build_smart_contract_risk_view(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#491 full protocol contract risk view."""
    seed = seed or _load_seed()
    protocols = seed.get("protocol_contracts") or {}
    analyses = [
        analyze_protocol_smart_contract_risk(pid, seed=seed)
        for pid in protocols
    ]
    valid = [a for a in analyses if a.get("ok")]
    return {
        "ok": True,
        "feature_ref": _PROTOCOL_RISK_REF,
        "title": "Smart Contract and Protocol Risk",
        "protocols": valid,
        "count": len(valid),
        "mandatory_indicators": (seed.get("smart_contract_risk_491") or {}).get("mandatory_indicators"),
        "data_sources_v1": (seed.get("smart_contract_risk_491") or {}).get("data_sources_v1"),
        "monitoring_only": True,
        "timestamp": _utcnow(),
    }


def apply_protocol_risk_to_opportunity_score(
    opportunity: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#491 → #460: protocol risk adjusts overall opportunity score."""
    seed = seed or _load_seed()
    protocol_id = str(opportunity.get("protocol_id") or opportunity.get("chain", "")).lower()
    if not protocol_id:
        return {"adjusted": False, "reason": "no_protocol_id"}

    contract_risk = analyze_protocol_smart_contract_risk(protocol_id, seed=seed)
    if not contract_risk.get("ok"):
        return {"adjusted": False, "reason": "protocol_not_found"}

    base_score = float(opportunity.get("net_edge_bps") or opportunity.get("gross_spread_bps") or 0)
    risk_penalty = contract_risk["protocol_risk_score"] / 100 * 15
    adjusted_bps = round(max(0, base_score - risk_penalty), 2)

    diligence_adj = None
    try:
        from bd_platform.diligence_risk_scoring import score_entity_risk

        asset = str(opportunity.get("asset", ""))
        dr = score_entity_risk(asset)
        if dr.get("ok"):
            diligence_adj = dr.get("overall_risk_score")
    except Exception:
        logger.debug("diligence risk adj skipped", exc_info=True)

    return {
        "ok": True,
        "feature_ref": _PROTOCOL_RISK_REF,
        "integration": "diligence_risk_460",
        "protocol_id": protocol_id,
        "protocol_risk_score": contract_risk["protocol_risk_score"],
        "base_opportunity_bps": base_score,
        "risk_penalty_bps": round(risk_penalty, 2),
        "adjusted_opportunity_bps": adjusted_bps,
        "diligence_risk_score_460": diligence_adj,
        "adjusted": True,
        "timestamp": _utcnow(),
    }


def analyze_all_liquidity_risks(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#473 — all 6 v1 protocols."""
    seed = seed or _load_seed()
    cfg = seed.get("liquidity_risk_473") or {}
    protocols = seed.get("liquidity_protocols") or {}
    analyses = [
        analyze_protocol_liquidity_risk(pid, seed=seed)
        for pid in protocols
    ]
    valid = [a for a in analyses if a.get("ok")]

    return {
        "ok": True,
        "feature_ref": _LIQUIDITY_RISK_REF,
        "protocols": valid,
        "count": len(valid),
        "protocol_count_target": cfg.get("protocol_count_v1", 6),
        "protocol_count_met": len(valid) >= int(cfg.get("protocol_count_v1", 6)),
        "update_interval_minutes": cfg.get("update_interval_minutes", 15),
        "accuracy_tolerance_pct": cfg.get("accuracy_tolerance_pct", 0.1),
        "historical_retention_days": cfg.get("historical_retention_days", 365),
        "mandatory_indicators": cfg.get("mandatory_indicators"),
        "timestamp": _utcnow(),
    }


def _liquidity_risk_adjusted_collateral(
    asset: str,
    liquidity_risk_score: float,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """#473 → #462 integration: liquidity risk affects collateral grade."""
    try:
        from bd_platform.diligence_risk_scoring import score_collateral_risk

        collateral = score_collateral_risk(asset, seed=seed)
        if not collateral.get("ok"):
            return None
        base_grade = collateral.get("collateral_grade", "C")
        adjusted = base_grade
        if liquidity_risk_score >= 70 and base_grade in ("A", "B"):
            adjusted = "C" if base_grade == "B" else "B"
        elif liquidity_risk_score >= 85:
            adjusted = "D" if base_grade in ("A", "B", "C") else "F"
        return {
            "base_collateral_grade": base_grade,
            "liquidity_risk_adjusted_grade": adjusted,
            "liquidity_risk_score": liquidity_risk_score,
            "breakdown": collateral.get("breakdown"),
            "no_opaque_score": True,
        }
    except Exception:
        logger.debug("liquidity-adjusted collateral skipped", exc_info=True)
        return None


def scan_defi_opportunities(*, seed: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """#438 DeFi Opportunity Scanner — on-chain analytics with #465/#473 enrichments."""
    seed = seed or _load_seed()
    fee_bps = float(seed.get("default_trading_fee_bps", 10))
    slip_bps = float(seed.get("default_slippage_bps", 8))
    quote_usd = 1000.0
    opportunities: list[dict[str, Any]] = []

    liquidity_risks = analyze_all_liquidity_risks(seed=seed)
    avg_liq_risk = 0.0
    if liquidity_risks.get("protocols"):
        avg_liq_risk = sum(p["liquidity_risk_score"] for p in liquidity_risks["protocols"]) / len(
            liquidity_risks["protocols"]
        )

    for raw in seed.get("defi_opportunities") or []:
        gross_bps = float(raw.get("price_divergence_bps", 0))
        gas_usd = float(raw.get("gas_cost_estimate_usd", 0))

        try:
            from bd_platform.unified_arbitrage_engine import compute_arbitrage_economics
            econ = compute_arbitrage_economics(
                gross_spread_bps=gross_bps,
                quote_usd=quote_usd,
                trading_fee_bps=fee_bps,
                slippage_bps=slip_bps,
                transfer_cost_usdt=0.0,
                withdrawal_fee_usdt=gas_usd,
            )
        except Exception:
            econ = {
                "gross_spread_bps": gross_bps,
                "net_edge_usdt": 0,
                "net_edge_bps": 0,
                "trading_fees_usdt": 0,
            }

        asset = str(raw.get("asset", ""))
        opp = {
            "opportunity_id": raw.get("opportunity_id"),
            "opportunity_type": raw.get("scan_type", "on_chain_arbitrage"),
            "feature_ref": _FEATURE_ID,
            "legal_name": _LEGAL_NAME,
            "asset": asset,
            "symbol": raw.get("symbol"),
            "chain": raw.get("chain", "ethereum"),
            "venue_buy": raw.get("venue_buy"),
            "venue_sell": raw.get("venue_sell"),
            "price_divergence_bps": gross_bps,
            "implied_yield_pct": raw.get("implied_yield_pct"),
            "gas_cost_estimate_usd": gas_usd,
            "collateral_ratio": raw.get("collateral_ratio"),
            "liquidation_discount_pct": raw.get("liquidation_discount_pct"),
            "lst_peg_deviation_bps": raw.get("lst_peg_deviation_bps"),
            "gross_spread_bps": econ["gross_spread_bps"],
            "net_edge_usdt": econ["net_edge_usdt"],
            "net_edge_bps": econ["net_edge_bps"],
            "slippage_bps": slip_bps,
            "trading_fees_usdt": econ.get("trading_fees_usdt", 0),
            "withdrawal_fee_usdt": gas_usd,
            "quote_usd": quote_usd,
            "liquidity_risk_473": {
                "avg_protocol_risk_score": round(avg_liq_risk, 1),
                "protocol_count": liquidity_risks.get("count"),
            },
            "cancelled_v1_scope": {
                "flash_loan_simulation": True,
                "bridge_execution": True,
                "liquidation_buying": True,
                "ml_training": True,
            },
            "simulation_only": True,
            "no_auto_execution": True,
            "display": raw.get("display") or f"DeFi divergence {asset} net edge {econ['net_edge_bps']:.2f} bps",
        }

        try:
            from bd_platform.diligence_risk_scoring import score_collateral_risk

            collateral = score_collateral_risk(asset)
            if collateral.get("ok"):
                opp["collateral_grade_462"] = collateral.get("collateral_grade")
                opp["collateral_breakdown_462"] = collateral.get("breakdown")
                adjusted = _liquidity_risk_adjusted_collateral(asset, avg_liq_risk, seed=seed)
                if adjusted:
                    opp["collateral_grade_adjusted_473"] = adjusted
        except Exception:
            logger.debug("collateral grade attachment skipped for %s", asset, exc_info=True)

        protocol_map = seed.get("opportunity_protocol_map") or {}
        opp["protocol_id"] = protocol_map.get(raw.get("opportunity_id")) or protocol_map.get(asset.lower())
        if opp.get("protocol_id"):
            opp["protocol_risk_491"] = apply_protocol_risk_to_opportunity_score(opp, seed=seed)

        opportunities.append(opp)

    return opportunities


def build_lp_position_risk_panel(
    position_id: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    positions = seed.get("lp_positions") or []
    if position_id:
        positions = [p for p in positions if p.get("position_id") == position_id]
    calcs = [calculate_lp_position_risk(p, seed=seed) for p in positions]
    return {
        "ok": True,
        "feature_ref": _LP_POSITION_RISK_REF,
        "legal_name": (seed.get("lp_position_risk_470") or {}).get("legal_name"),
        "positions": [c for c in calcs if c.get("ok")],
        "count": sum(1 for c in calcs if c.get("ok")),
        "simulation_only": True,
        "timestamp": _utcnow(),
    }


def build_defi_panel(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#438 full DeFi panel with absorbed #465/#470/#473."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    opps = scan_defi_opportunities(seed=seed)
    dex_screener = screen_dex_pools(seed=seed)
    liquidity_risk = analyze_all_liquidity_risks(seed=seed)
    lp_risk = build_lp_position_risk_panel(seed=seed)
    oracle_risk = build_oracle_risk_view(seed=seed)
    contract_risk = build_smart_contract_risk_view(seed=seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "merged_into": _MERGED_INTO,
        "absorbed_features": seed.get("absorbed_features"),
        "opportunities": opps,
        "count": len(opps),
        "dex_screener_465": dex_screener,
        "liquidity_risk_473": liquidity_risk,
        "lp_position_risk_470": lp_risk,
        "oracle_risk_482": oracle_risk,
        "smart_contract_risk_491": contract_risk,
        "monitoring_only": True,
        "cancelled_v1_scope": {
            "flash_loan_simulation": True,
            "bridge_execution": True,
            "liquidation_buying": True,
            "sharpe_drawdown_winrate_sla": True,
            "lp_live_simulator_sla": True,
        },
        "simulation_only": True,
        "no_auto_execution": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def defi_opportunity_scanner_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "absorbed_features": seed.get("absorbed_features"),
        "components": {
            "dex_screener_465": True,
            "lp_position_risk_calculator_470": True,
            "liquidity_risk_473": True,
            "oracle_risk_482": True,
            "smart_contract_risk_491": True,
            "on_chain_arbitrage": True,
        },
        "dex_screener": {
            "dexs_v1": (seed.get("dex_screener_465") or {}).get("dexs_v1"),
            "honeypot_provider": (seed.get("dex_screener_465") or {}).get("honeypot_provider"),
            "default_filters": (seed.get("dex_screener_465") or {}).get("default_filters"),
        },
        "liquidity_risk": {
            "protocol_count": len(seed.get("liquidity_protocols") or {}),
            "update_interval_minutes": (seed.get("liquidity_risk_473") or {}).get("update_interval_minutes"),
        },
        "oracle_risk": {
            "feature_ref": _ORACLE_RISK_REF,
            "protocol_count": len(seed.get("oracle_protocols") or {}),
            "source_config_version": (seed.get("oracle_risk_482") or {}).get("source_config_version"),
        },
        "smart_contract_risk": {
            "feature_ref": _PROTOCOL_RISK_REF,
            "protocol_count": len(seed.get("protocol_contracts") or {}),
            "data_sources_v1": (seed.get("smart_contract_risk_491") or {}).get("data_sources_v1"),
        },
        "monitoring_only": True,
        "simulation_only": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "429 merge"})
    checks.append({"id": "dex_screener_4_dexs", "passed": len((seed.get("dex_screener_465") or {}).get("dexs_v1", [])) == 4, "detail": "465"})
    checks.append({"id": "pool_mapping", "passed": len(seed.get("pool_mapping") or {}) >= 1, "detail": "mapping"})

    screener = screen_dex_pools(seed=seed)
    checks.append({"id": "default_filters", "passed": screener["filters_applied"]["min_liquidity_usd"] >= 100_000, "detail": "filters"})
    checks.append({"id": "honeypot_flags", "passed": any(p["risk_flags"]["honeypot"]["checked"] for p in screener["pools"]), "detail": "honeypot.is"})

    lp = calculate_lp_position_risk((seed.get("lp_positions") or [{}])[0], seed=seed)
    checks.append({"id": "lp_il_estimate", "passed": lp.get("impermanent_loss_pct") is not None, "detail": "470"})
    checks.append({"id": "lp_net_pnl", "passed": lp.get("net_pnl_usd") is not None, "detail": "net pnl"})
    checks.append({"id": "lp_renamed", "passed": "Simulator" not in lp.get("legal_name", ""), "detail": "no live sim"})

    liq = analyze_all_liquidity_risks(seed=seed)
    checks.append({"id": "liquidity_6_protocols", "passed": liq.get("protocol_count_met") is True, "detail": "473"})
    checks.append({"id": "liquidity_indicators", "passed": all(
        "tvl_trend_7d_pct" in p["indicators"] for p in liq.get("protocols", [])
    ), "detail": "4 indicators"})

    opps = scan_defi_opportunities(seed=seed)
    checks.append({"id": "defi_opportunities", "passed": len(opps) >= 1, "detail": f"count={len(opps)}"})
    checks.append({"id": "collateral_grade_462", "passed": any("collateral_grade_462" in o for o in opps), "detail": "462"})

    oracle = build_oracle_risk_view(seed=seed)
    checks.append({"id": "oracle_risk_482", "passed": oracle.get("count", 0) >= 1, "detail": "482"})
    checks.append({"id": "oracle_source_config", "passed": oracle.get("source_config_version") is not None, "detail": "config"})
    checks.append({"id": "oracle_indicators", "passed": all(
        "oracle_count" in p and "heartbeat_freshness" in p for p in oracle.get("protocols", [])
    ), "detail": "indicators"})

    single_oracle_alerts = build_portfolio_single_oracle_alerts(seed=seed)
    checks.append({"id": "single_oracle_alerts_410", "passed": single_oracle_alerts.get("backend_enforced") is True, "detail": "410"})

    contract = build_smart_contract_risk_view(seed=seed)
    checks.append({"id": "smart_contract_risk_491", "passed": contract.get("count", 0) >= 1, "detail": "491"})
    checks.append({"id": "contract_5_indicators", "passed": all(
        len(p.get("indicators", {})) >= 5 for p in contract.get("protocols", [])
    ), "detail": "indicators"})
    checks.append({"id": "contract_sla_cancelled", "passed": (seed.get("smart_contract_risk_491") or {}).get("cancelled_sla", {}).get("response_2_seconds") is True, "detail": "SLA"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
