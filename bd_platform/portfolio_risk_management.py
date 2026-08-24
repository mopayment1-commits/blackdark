"""
Portfolio Risk Management — Feature #109 (Portfolio AI, Sprint 1).

Actionable, personal risk signals (NOT generic fear/greed):
  1. Volatility-based stop-loss suggestions
  2. Protocol risk score (TVL + audit age)
  3. Ecosystem concentration / correlation risk

Integrates with #190 (Security Controls) and #192 (Security-First Architecture).
Feeds Decision Engine via portfolio_risk payload.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.PortfolioRisk")

# Ecosystem grouping for concentration risk (beyond sector labels).
ECOSYSTEM_MAP: dict[str, str] = {
    "SOL": "Solana",
    "JTO": "Solana",
    "RAY": "Solana",
    "BONK": "Solana",
    "WIF": "Solana",
    "ETH": "Ethereum",
    "UNI": "Ethereum",
    "LINK": "Ethereum",
    "AAVE": "Ethereum",
    "MKR": "Ethereum",
    "ARB": "Ethereum L2",
    "OP": "Ethereum L2",
    "MATIC": "Ethereum L2",
    "POL": "Ethereum L2",
    "BNB": "BNB Chain",
    "CAKE": "BNB Chain",
    "AVAX": "Avalanche",
    "DOT": "Polkadot",
    "ATOM": "Cosmos",
    "NEAR": "NEAR",
    "APT": "Aptos",
    "SUI": "Sui",
    "SEI": "Sei",
    "BTC": "Bitcoin",
    "WBTC": "Bitcoin",
}

# Known DeFi protocols — TVL tier + last audit age (days).
PROTOCOL_REGISTRY: dict[str, dict[str, Any]] = {
    "aave": {"tvl_usd": 12_000_000_000, "audit_age_days": 120, "display": "Aave"},
    "uniswap": {"tvl_usd": 4_500_000_000, "audit_age_days": 90, "display": "Uniswap"},
    "lido": {"tvl_usd": 28_000_000_000, "audit_age_days": 200, "display": "Lido"},
    "curve": {"tvl_usd": 2_100_000_000, "audit_age_days": 365, "display": "Curve"},
    "compound": {"tvl_usd": 2_800_000_000, "audit_age_days": 180, "display": "Compound"},
    "maker": {"tvl_usd": 8_000_000_000, "audit_age_days": 150, "display": "MakerDAO"},
    "raydium": {"tvl_usd": 350_000_000, "audit_age_days": 400, "display": "Raydium"},
    "jupiter": {"tvl_usd": 1_200_000_000, "audit_age_days": 200, "display": "Jupiter"},
    "marinade": {"tvl_usd": 1_100_000_000, "audit_age_days": 250, "display": "Marinade"},
    "orca": {"tvl_usd": 180_000_000, "audit_age_days": 300, "display": "Orca"},
    "unknown_defi": {"tvl_usd": 8_000_000, "audit_age_days": 800, "display": "Unknown DeFi"},
    "new_farm": {"tvl_usd": 3_500_000, "audit_age_days": 950, "display": "New Farm"},
}

_CONCENTRATION_THRESHOLD_PCT = 50.0
_PROTOCOL_HIGH_RISK_SCORE = 60


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _ecosystem_for_symbol(symbol: str) -> str:
    sym = symbol.upper().replace("/USDT", "")
    if sym in ECOSYSTEM_MAP:
        return ECOSYSTEM_MAP[sym]
    sector = config.SECTOR_MAP.get(sym, "Other")
    if sector == "Layer 1":
        return f"{sym} L1"
    if sector == "L2":
        return "Ethereum L2"
    if sector == "DeFi":
        return "DeFi (multi-chain)"
    return sector


def _volatility_pct(symbol: str, *, holding: dict[str, Any] | None = None) -> float:
    if holding and holding.get("volatility_24h_pct") is not None:
        return abs(float(holding["volatility_24h_pct"]))
    # Heuristic fallback when live vol unavailable
    betas = {"BTC": 3.0, "ETH": 4.5, "SOL": 6.0, "DOGE": 8.0, "PEPE": 12.0, "WIF": 10.0}
    return betas.get(symbol.upper(), 5.0)


def suggest_stop_loss(
    symbol: str,
    *,
    value_usd: float,
    volatility_24h_pct: float | None = None,
) -> dict[str, Any]:
    """
    Volatility-scaled stop-loss suggestion.
    Example: "If price drops 5%, sell 20% of position."
    """
    vol = volatility_24h_pct if volatility_24h_pct is not None else _volatility_pct(symbol)
    trigger_pct = round(min(15.0, max(2.0, vol * 0.55)), 1)
    sell_pct = round(min(50.0, max(10.0, vol * 2.8)), 0)
    action = (
        f"If {symbol.upper()} drops {trigger_pct:.0f}%, consider selling "
        f"{sell_pct:.0f}% of the position (${value_usd * sell_pct / 100:,.0f} at current mark)."
    )
    return {
        "symbol": symbol.upper(),
        "value_usd": round(value_usd, 2),
        "volatility_24h_pct": round(vol, 2),
        "trigger_drop_pct": trigger_pct,
        "suggested_trim_pct": sell_pct,
        "action": action,
        "urgency": "high" if vol >= 8 else ("medium" if vol >= 4 else "low"),
        "mode": "suggestion_only",
    }


def score_protocol_risk(protocol_id: str) -> dict[str, Any]:
    """Protocol risk from TVL tier + audit recency."""
    key = (protocol_id or "").strip().lower().replace(" ", "_")
    meta = PROTOCOL_REGISTRY.get(key)
    if not meta:
        meta = {"tvl_usd": 5_000_000, "audit_age_days": 999, "display": protocol_id or "Unknown"}

    tvl = float(meta.get("tvl_usd") or 0)
    audit_days = int(meta.get("audit_age_days") or 999)
    score = 0
    factors: list[str] = []

    if tvl < 10_000_000:
        score += 45
        factors.append("TVL under $10M")
    elif tvl < 50_000_000:
        score += 30
        factors.append("TVL under $50M")
    elif tvl < 200_000_000:
        score += 15
        factors.append("TVL under $200M")

    if audit_days > 730:
        score += 40
        factors.append("audit older than 2 years or missing")
    elif audit_days > 365:
        score += 25
        factors.append("audit older than 1 year")

    score = min(100, score)
    level = "low"
    if score >= _PROTOCOL_HIGH_RISK_SCORE:
        level = "high"
    elif score >= 35:
        level = "medium"

    action = "Hold — protocol risk within tolerance"
    if level == "high":
        action = f"Exit {meta.get('display', protocol_id)} — high protocol risk"
    elif level == "medium":
        action = f"Reduce exposure to {meta.get('display', protocol_id)} — elevated protocol risk"

    return {
        "protocol_id": key,
        "protocol_name": meta.get("display", protocol_id),
        "tvl_usd": tvl,
        "audit_age_days": audit_days,
        "risk_score": score,
        "risk_level": level,
        "factors": factors,
        "action": action,
        "exit_recommended": level == "high",
    }


def analyze_concentration(holdings: list[dict[str, Any]], total_value: float) -> dict[str, Any]:
    """Ecosystem concentration — e.g. 60% in Solana = concentration risk."""
    if total_value <= 0 or not holdings:
        return {
            "ecosystem_weights": {},
            "dominant_ecosystem": None,
            "dominant_pct": 0.0,
            "concentration_risk": False,
            "action": "No holdings to analyze",
            "alerts": [],
        }

    buckets: dict[str, float] = {}
    for h in holdings:
        sym = str(h.get("symbol") or "").upper()
        val = float(h.get("value_usd") or 0)
        eco = _ecosystem_for_symbol(sym)
        buckets[eco] = buckets.get(eco, 0.0) + val

    weights = {k: round(v / total_value * 100, 1) for k, v in buckets.items()}
    dominant = max(weights, key=weights.get) if weights else None
    dominant_pct = weights.get(dominant or "", 0.0)
    concentration = dominant_pct >= _CONCENTRATION_THRESHOLD_PCT

    alerts: list[dict[str, Any]] = []
    action = "Portfolio diversification looks balanced across ecosystems"
    if concentration and dominant:
        action = (
            f"{dominant_pct:.0f}% of portfolio in {dominant} ecosystem — "
            f"concentration risk. Consider trimming to below {_CONCENTRATION_THRESHOLD_PCT:.0f}%."
        )
        alerts.append(
            {
                "level": "high" if dominant_pct >= 65 else "medium",
                "code": "ECOSYSTEM_CONCENTRATION",
                "ecosystem": dominant,
                "weight_pct": dominant_pct,
                "message": action,
            }
        )

    # Sector correlation proxy — multiple L1s still correlated via BTC beta
    l1_pct = sum(
        w for eco, w in weights.items() if "L1" in eco or eco in {"Bitcoin", "Ethereum", "Solana"}
    )
    if l1_pct >= 75 and not concentration:
        msg = f"{l1_pct:.0f}% in correlated Layer-1 exposure — systemic drawdown risk"
        alerts.append({"level": "medium", "code": "L1_CORRELATION", "weight_pct": l1_pct, "message": msg})
        if action.startswith("Portfolio diversification"):
            action = msg

    return {
        "ecosystem_weights": weights,
        "dominant_ecosystem": dominant,
        "dominant_pct": dominant_pct,
        "concentration_risk": concentration,
        "action": action,
        "alerts": alerts,
    }


def _security_controls_snapshot() -> dict[str, Any]:
    """#190 + #192 — surface institutional control posture for risk context."""
    out: dict[str, Any] = {
        "security_controls_verified": False,
        "trading_frozen": False,
        "surface": "portfolio_risk_management",
    }
    try:
        from cap646.institutional_controls import CONTROLS

        verified = 0
        for _cid, fn in CONTROLS:
            try:
                result = fn()
                if hasattr(result, "__await__"):
                    continue
                if isinstance(result, dict) and result.get("status") == "VERIFIED_COMPLETE":
                    verified += 1
            except Exception:
                continue
        total = len(CONTROLS)
        out["security_controls_verified"] = verified >= max(1, int(total * 0.7))
        out["controls_verified"] = verified
        out["controls_total"] = total
        out["security_first_architecture"] = {"controls_sampled": verified, "controls_total": total}
    except Exception:
        logger.debug("institutional controls snapshot unavailable")

    try:
        from risk_manager import is_trading_frozen, risk_status

        out["trading_frozen"] = is_trading_frozen()
        out["execution_risk"] = risk_status()
    except Exception:
        logger.debug("risk_manager snapshot unavailable")

    return out


def _compliance_footer() -> dict[str, Any]:
    try:
        from decision_certificate import compliance_footer_block

        return compliance_footer_block(
            surface="portfolio_risk_management",
            trust_basis="volatility model + protocol registry + ecosystem weights",
            data_sources="holdings marks · protocol TVL/audit registry · institutional controls",
        )
    except Exception:
        return {
            "disclaimer": (
                "Not financial advice. Stop-loss and protocol risk outputs are suggestions only. "
                "Verify on the Public Accuracy Ledger."
            ),
        }


def analyze_portfolio_risk(
    holdings: list[dict[str, Any]],
    *,
    total_value: float | None = None,
) -> dict[str, Any]:
    """
    Full portfolio risk analysis for Portfolio AI enrichment.
    """
    t0 = time.perf_counter()
    tv = total_value if total_value is not None else sum(float(h.get("value_usd") or 0) for h in holdings)

    stop_losses: list[dict[str, Any]] = []
    protocol_risks: list[dict[str, Any]] = []
    actionable: list[dict[str, Any]] = []

    for h in holdings:
        sym = str(h.get("symbol") or "").upper()
        val = float(h.get("value_usd") or 0)
        if not sym or val <= 0:
            continue

        vol = h.get("volatility_24h_pct")
        sl = suggest_stop_loss(sym, value_usd=val, volatility_24h_pct=float(vol) if vol is not None else None)
        stop_losses.append(sl)
        if sl["urgency"] in {"high", "medium"}:
            actionable.append({"type": "stop_loss", "priority": sl["urgency"], "headline": sl["action"]})

        protocol = h.get("protocol") or h.get("defi_protocol")
        if protocol:
            pr = score_protocol_risk(str(protocol))
            pr["symbol"] = sym
            pr["position_usd"] = round(val, 2)
            protocol_risks.append(pr)
            if pr["exit_recommended"]:
                actionable.append(
                    {
                        "type": "protocol_exit",
                        "priority": "high",
                        "headline": pr["action"],
                    }
                )

    concentration = analyze_concentration(holdings, tv)
    for alert in concentration.get("alerts") or []:
        actionable.append(
            {
                "type": "concentration",
                "priority": alert.get("level", "medium"),
                "headline": alert.get("message", ""),
            }
        )

    # Deduplicate actionable by headline, sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    seen: set[str] = set()
    unique_actionable: list[dict[str, Any]] = []
    for item in sorted(actionable, key=lambda x: priority_order.get(str(x.get("priority")), 9)):
        headline = str(item.get("headline") or "")
        if headline and headline not in seen:
            seen.add(headline)
            unique_actionable.append(item)

    elapsed = time.perf_counter() - t0
    overall_risk = "low"
    high_count = sum(1 for a in unique_actionable if a.get("priority") == "high")
    if high_count >= 2:
        overall_risk = "high"
    elif high_count >= 1 or concentration.get("concentration_risk"):
        overall_risk = "medium"

    return {
        "ok": True,
        "feature_id": 109,
        "surface": "portfolio_risk_management",
        "hero": "portfolio_ai",
        "timestamp": _utcnow(),
        "total_value_usd": round(tv, 2),
        "overall_risk_level": overall_risk,
        "stop_loss_suggestions": stop_losses,
        "protocol_risks": protocol_risks,
        "concentration": concentration,
        "actionable_alerts": unique_actionable[:8],
        "security": _security_controls_snapshot(),
        "compliance_footer": _compliance_footer(),
        "sla_met": elapsed <= 2.0,
        "accuracy_target_pct": 95,
        "mode": "suggestion_only",
    }


async def portfolio_risk_overview(
    assets: list[dict[str, Any]],
    *,
    holdings_enriched: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Async entry — enriches holdings with live vol when possible, then analyzes.
    """
    t0 = time.perf_counter()
    enriched: list[dict[str, Any]] = []

    if holdings_enriched:
        enriched = list(holdings_enriched)
    else:
        try:
            from bd_platform.slippage_tolerance_optimizer import _market_context
        except ImportError:
            _market_context = None  # type: ignore[assignment]

        for item in assets:
            sym = str(item.get("symbol") or item.get("asset") or "").upper()
            row = dict(item)
            if _market_context and sym:
                try:
                    ctx = await _market_context(sym)
                    if ctx.get("volatility_24h_pct") is not None:
                        row["volatility_24h_pct"] = ctx["volatility_24h_pct"]
                except Exception:
                    pass
            enriched.append(row)

    total = sum(float(h.get("value_usd") or h.get("amount", 0) * h.get("price", 0)) for h in enriched)
    result = analyze_portfolio_risk(enriched, total_value=total)
    result["sla_met"] = (time.perf_counter() - t0) <= 2.0
    return result
