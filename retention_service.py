"""
BLACKDARK — Subscriber retention guard (bear-market churn mitigation).

Detects low-arbitrage / bear regimes and surfaces non-arb subscriber value so
users see ROI beyond spread capture (Oracle, risk warnings, research, paper P&L).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Literal

import config
logger = logging.getLogger("BLACKDARK.Retention")

ChurnRisk = Literal["low", "moderate", "high", "critical"]

BEAR_REGIMES = frozenset({"panic", "risk_off"})
SUBSCRIPTION_COST_USD = {"pro": 29.0, "whale": 49.0}


def _enabled() -> bool:
    return getattr(config, "RETENTION_GUARD_ENABLED", True)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def is_low_volatility(change_24h: float) -> bool:
    threshold = float(getattr(config, "RETENTION_LOW_VOLATILITY_PCT", 3.0))
    return abs(change_24h) < threshold


def classify_bear_market(
    regime: str,
    *,
    change_24h: float = 0.0,
    profitable_arb_count: int = 0,
) -> dict[str, Any]:
    """Return bear-mode flags used for churn UX and trial extensions."""
    low_vol = is_low_volatility(change_24h)
    max_profitable = int(getattr(config, "RETENTION_LOW_ARB_PROFITABLE_MAX", 1))
    low_arb = profitable_arb_count <= max_profitable

    bear_regime = regime in BEAR_REGIMES or (regime == "neutral" and low_vol)
    bear_market_mode = bear_regime and low_arb

    return {
        "market_regime": regime,
        "change_24h_pct": round(change_24h, 2),
        "low_volatility": low_vol,
        "low_arbitrage": low_arb,
        "profitable_arb_count": profitable_arb_count,
        "bear_market_mode": bear_market_mode,
        "primary_value_pivot": "research_lab" if bear_market_mode else "arbitrage",
        "headline_en": (
            "Bear / low-volatility regime — arbitrage spreads are thin. "
            "Pivot to Oracle risk analytics, Research Lab, and paper simulations."
            if bear_market_mode
            else "Normal regime — arbitrage scanner active alongside Oracle analytics."
        ),
    }


async def fetch_live_market_snapshot() -> dict[str, Any]:
    """BTC-led regime + latest shared arb scan stats."""
    from scan_coordinator import get_shared_scan
    from weight_aggregator import detect_market_regime
    from whale_tracker import get_latest_institutional_context

    change_24h = 0.0
    try:
        import aiohttp

        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(
            "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                change_24h = float(data.get("priceChangePercent") or 0)
    except Exception:
        logger.debug("BTC ticker fetch failed for retention snapshot", exc_info=True)

    ctx = await get_latest_institutional_context()
    regime = detect_market_regime(ctx, change_24h=change_24h)

    scan: dict[str, Any] = {}
    try:
        scan = await get_shared_scan(profitable_only=False)
    except Exception:
        logger.debug("Shared arb scan failed for retention snapshot", exc_info=True)

    profitable = int(scan.get("profitable_count") or 0)
    bear = classify_bear_market(regime, change_24h=change_24h, profitable_arb_count=profitable)
    bear["scan_opportunity_count"] = len(scan.get("opportunities") or [])
    bear["generated_at"] = _utcnow_iso()
    return bear


def estimate_subscriber_value_usd(
    *,
    tier: str,
    oracle_calls_month: int,
    risk_warnings_month: int,
    paper_pnl_usd: float,
    oracle_accuracy_pct: float,
) -> dict[str, Any]:
    """Heuristic ROI model — informational, not a performance guarantee."""
    tier_key = tier if tier in SUBSCRIPTION_COST_USD else "pro"
    sub_cost = SUBSCRIPTION_COST_USD[tier_key]

    oracle_value = oracle_calls_month * 0.35
    risk_value = risk_warnings_month * 2.5
    accuracy_bonus = max(0.0, (oracle_accuracy_pct - 50.0) * 0.15)
    paper_value = max(0.0, paper_pnl_usd) * 0.25
    estimated = round(oracle_value + risk_value + accuracy_bonus + paper_value, 2)
    roi_ratio = round(estimated / sub_cost, 2) if sub_cost else 0.0

    return {
        "subscription_cost_usd_month": sub_cost,
        "estimated_value_usd_month": estimated,
        "roi_ratio": roi_ratio,
        "covers_subscription": estimated >= sub_cost,
        "components": {
            "oracle_calls": oracle_calls_month,
            "risk_warnings": risk_warnings_month,
            "paper_pnl_usd": round(paper_pnl_usd, 2),
            "oracle_accuracy_pct": round(oracle_accuracy_pct, 1),
        },
    }


def compute_churn_risk(
    *,
    bear_market_mode: bool,
    oracle_calls_month: int,
    trial_days_left: int | None,
    roi_covers_subscription: bool,
) -> dict[str, Any]:
    score = 0
    if bear_market_mode:
        score += 35
    if oracle_calls_month < 5:
        score += 25
    if not roi_covers_subscription:
        score += 25
    if trial_days_left is not None and trial_days_left <= 3:
        score += 15

    if score >= 70:
        level: ChurnRisk = "critical"
    elif score >= 50:
        level = "high"
    elif score >= 30:
        level = "moderate"
    else:
        level = "low"

    actions: list[str] = []
    if bear_market_mode:
        actions.append("Use Research Lab + Oracle risk warnings instead of arb-only ROI.")
    if oracle_calls_month < 5:
        actions.append("Run daily Oracle scans on your watchlist to unlock platform value.")
    if not roi_covers_subscription:
        actions.append("Review value digest — paper sim P&L and risk alerts count toward ROI.")
    if trial_days_left is not None and trial_days_left <= 3:
        actions.append("Trial ending soon — explore Research Lab before deciding.")

    return {
        "score": min(100, score),
        "level": level,
        "recommended_actions_en": actions,
    }


async def build_subscriber_value_digest(email: str, tier: str) -> dict[str, Any]:
    from database import (
        count_risk_oracle_predictions_month,
        fetch_oracle_audit_stats,
        fetch_oracle_usage_month,
        fetch_simulation_logs,
    )

    oracle_calls = await fetch_oracle_usage_month(email)
    risk_warnings = await count_risk_oracle_predictions_month()
    audit = await fetch_oracle_audit_stats(limit=100)
    sims = await fetch_simulation_logs(limit=50)
    paper_pnl = sum(float(s.get("pnl_usd") or 0) for s in sims)

    accuracy = float(audit.get("average_accuracy_percent") or 0)
    value = estimate_subscriber_value_usd(
        tier=tier,
        oracle_calls_month=oracle_calls,
        risk_warnings_month=risk_warnings,
        paper_pnl_usd=paper_pnl,
        oracle_accuracy_pct=accuracy,
    )
    return {
        "email": email,
        "tier": tier,
        "value": value,
        "usage": {
            "oracle_calls_30d": oracle_calls,
            "risk_warnings_30d": risk_warnings,
            "simulation_runs_30d": len(sims),
        },
        "disclaimer_en": (
            "Estimated value is illustrative analytics — not guaranteed trading profit "
            "or investment advice."
        ),
    }


async def maybe_grant_bear_trial_extension(email: str, subscription: dict[str, Any] | None) -> dict[str, Any]:
    """One-time bear-market trial extension per rolling window."""
    if not _enabled():
        return {"granted": False, "reason": "disabled"}
    if not getattr(config, "RETENTION_AUTO_TRIAL_EXTENSION", True):
        return {"granted": False, "reason": "auto_extension_off"}

    if not subscription or subscription.get("status") != "trial":
        return {"granted": False, "reason": "not_on_trial"}

    from database import extend_pro_trial, retention_grant_recent

    days = int(getattr(config, "RETENTION_BEAR_TRIAL_EXTENSION_DAYS", 7))
    window = int(getattr(config, "RETENTION_GRANT_COOLDOWN_DAYS", 30))
    if await retention_grant_recent(email, "bear_trial_extension", within_days=window):
        return {"granted": False, "reason": "cooldown_active"}

    market = await fetch_live_market_snapshot()
    if not market.get("bear_market_mode"):
        return {"granted": False, "reason": "not_bear_market"}

    result = await extend_pro_trial(email, days)
    from database import record_retention_grant

    await record_retention_grant(email, "bear_trial_extension", days)
    logger.info(
        "Bear trial extension granted | email=%s days=%s",
        str(email).replace("\r", " ").replace("\n", " "),
        str(days).replace("\r", " ").replace("\n", " "),
    )
    return {"granted": True, "days": days, "trial_ends_at": result.get("trial_ends_at")}


async def build_retention_status(
    user: dict[str, Any] | None = None,
    subscription: dict[str, Any] | None = None,
) -> dict[str, Any]:
    market = await fetch_live_market_snapshot()
    payload: dict[str, Any] = {
        "enabled": _enabled(),
        "generated_at": _utcnow_iso(),
        "market": market,
        "config": {
            "past_due_grace_days": int(getattr(config, "RETENTION_PAST_DUE_GRACE_DAYS", 7)),
            "low_arb_profitable_max": int(getattr(config, "RETENTION_LOW_ARB_PROFITABLE_MAX", 1)),
        },
    }

    if user:
        tier = str(user.get("tier") or "free")
        email = str(user.get("email") or "")
        digest = await build_subscriber_value_digest(email, tier) if tier != "free" else None

        trial_days_left: int | None = None
        if subscription and subscription.get("status") == "trial" and subscription.get("trial_ends_at"):
            try:
                ends = datetime.fromisoformat(str(subscription["trial_ends_at"]))
                trial_days_left = max(0, (ends - _utcnow()).days)
            except ValueError:
                trial_days_left = None

        churn = compute_churn_risk(
            bear_market_mode=bool(market.get("bear_market_mode")),
            oracle_calls_month=(digest or {}).get("usage", {}).get("oracle_calls_30d", 0),
            trial_days_left=trial_days_left,
            roi_covers_subscription=bool((digest or {}).get("value", {}).get("covers_subscription")),
        )
        extension = await maybe_grant_bear_trial_extension(email, subscription)

        payload["subscriber"] = {
            "tier": tier,
            "value_digest": digest,
            "churn_risk": churn,
            "trial_days_left": trial_days_left,
            "bear_trial_extension": extension,
            "dashboard_mode": market.get("primary_value_pivot"),
            "stripe_portal_hint_en": (
                "Payment issue? Update billing in the customer portal — "
                f"{payload['config']['past_due_grace_days']}-day grace keeps Pro access."
            ),
        }

    return payload


def retention_guard_status() -> dict[str, Any]:
    return {
        "enabled": _enabled(),
        "auto_trial_extension": getattr(config, "RETENTION_AUTO_TRIAL_EXTENSION", True),
        "past_due_grace_days": int(getattr(config, "RETENTION_PAST_DUE_GRACE_DAYS", 7)),
        "low_arb_profitable_max": int(getattr(config, "RETENTION_LOW_ARB_PROFITABLE_MAX", 1)),
        "bear_trial_extension_days": int(getattr(config, "RETENTION_BEAR_TRIAL_EXTENSION_DAYS", 7)),
    }
