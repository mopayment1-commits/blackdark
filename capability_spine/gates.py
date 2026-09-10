"""Admission gates: freshness SLO, time sync, venue, network, user constraints."""

from __future__ import annotations

import time
from typing import Any

METHODOLOGY_VERSION = "capability_spine_gates_v1"

FEATURE_FRESHNESS_SLO: dict[str, dict[str, Any]] = {
    "order_book:depth": {"source": "live_book_hub", "max_age_s": 2, "state_on_breach": "STALE"},
    "cex_spot:ticker": {"source": "binance", "max_age_s": 15, "state_on_breach": "DELAYED"},
    "funding:rate": {"source": "arbitrage_engine", "max_age_s": 300, "state_on_breach": "DELAYED"},
    "onchain:rpc": {"source": "onchain_hub", "max_age_s": 30, "state_on_breach": "STALE"},
    "macro:m2": {"source": "fred", "max_age_s": 86400 * 35, "state_on_breach": "DELAYED"},
    "sentiment:fear_greed": {"source": "alternative_me", "max_age_s": 3600, "state_on_breach": "DELAYED"},
}


def per_source_feature_freshness(
    *,
    source: str,
    feature: str,
    age_seconds: float | None,
    event_time: float | None = None,
    ingest_time: float | None = None,
) -> dict[str, Any]:
    """CAP-41 — per-source/per-feature threshold registry."""
    key = f"{source}:{feature}"
    cfg = FEATURE_FRESHNESS_SLO.get(key) or {"source": source, "max_age_s": 60, "state_on_breach": "STALE"}
    max_age = float(cfg["max_age_s"])
    now = time.time()
    if age_seconds is None and event_time is not None and ingest_time is not None:
        age_seconds = ingest_time - event_time
    if age_seconds is None:
        state = "UNAVAILABLE"
        slo_met = False
    elif age_seconds <= max_age * 0.5:
        state = "LIVE"
        slo_met = True
    elif age_seconds <= max_age:
        state = "DELAYED"
        slo_met = True
    else:
        state = str(cfg.get("state_on_breach") or "STALE")
        slo_met = False
    return {
        "ok": True,
        "source": source,
        "feature": feature,
        "freshness_state": state,
        "age_seconds": age_seconds,
        "max_age_s": max_age,
        "slo_met": slo_met,
        "event_time": event_time,
        "ingest_time": ingest_time or now,
        "methodology_version": METHODOLOGY_VERSION,
    }


def time_sync_clock_skew_detection(
    *,
    source_ts_ms: float,
    ingest_ts_ms: float,
    server_ts_ms: float | None = None,
    max_skew_ms: float = 5000.0,
) -> dict[str, Any]:
    """CAP-43 — compare source/event/ingest/system time."""
    now_ms = server_ts_ms or time.time() * 1000
    skew_source_ingest = abs(ingest_ts_ms - source_ts_ms)
    skew_server_source = abs(now_ms - source_ts_ms)
    material = max(skew_source_ingest, skew_server_source) > max_skew_ms
    return {
        "ok": True,
        "pass": not material,
        "skew_source_ingest_ms": round(skew_source_ingest, 2),
        "skew_server_source_ms": round(skew_server_source, 2),
        "max_skew_ms": max_skew_ms,
        "action": "reject" if material else "pass",
        "methodology_version": METHODOLOGY_VERSION,
    }


def venue_trading_status_gate(
    venue: str,
    *,
    trading_state: str | None = None,
    deposit_open: bool | None = None,
    withdraw_open: bool | None = None,
    status_age_s: float | None = None,
    max_status_age_s: float = 120.0,
) -> dict[str, Any]:
    """CAP-44 — market trading state gate."""
    if status_age_s is not None and status_age_s > max_status_age_s:
        return {
            "ok": True,
            "pass": False,
            "reason": "stale_venue_status",
            "venue": venue,
            "methodology_version": METHODOLOGY_VERSION,
        }
    state = (trading_state or "UNKNOWN").upper()
    halted = state in {"HALT", "MAINTENANCE", "DISABLED", "UNKNOWN"}
    transfer_blocked = deposit_open is False or withdraw_open is False
    return {
        "ok": True,
        "pass": not halted and not transfer_blocked,
        "venue": venue,
        "trading_state": state,
        "deposit_open": deposit_open,
        "withdraw_open": withdraw_open,
        "methodology_version": METHODOLOGY_VERSION,
    }


def network_compatibility_validator(
    *,
    asset: str,
    chain: str,
    deposit_networks: list[str] | None = None,
    withdraw_networks: list[str] | None = None,
    required_network: str | None = None,
) -> dict[str, Any]:
    """CAP-45 — network/contract compatibility."""
    dep = [n.lower() for n in (deposit_networks or [])]
    wd = [n.lower() for n in (withdraw_networks or [])]
    req = (required_network or chain).lower()
    supported = req in dep and req in wd if dep and wd else req == chain.lower()
    if not dep and not wd:
        supported = False
    return {
        "ok": True,
        "pass": supported,
        "asset": asset,
        "chain": chain,
        "required_network": req,
        "deposit_networks": dep,
        "withdraw_networks": wd,
        "methodology_version": METHODOLOGY_VERSION,
    }


def new_asset_probation_gate(
    asset: str,
    *,
    lifecycle_state: str = "PROBATION",
    listing_age_days: float | None = None,
    data_quality_score: float | None = None,
    min_quality: float = 60.0,
    min_age_days: float = 7.0,
) -> dict[str, Any]:
    """CAP-46 — explicit lifecycle with evidence criteria."""
    state = lifecycle_state.upper()
    if state in {"DISABLED", "BLOCKED"}:
        return {"ok": True, "pass": False, "state": state, "asset": asset, "methodology_version": METHODOLOGY_VERSION}
    quality_ok = data_quality_score is None or data_quality_score >= min_quality
    age_ok = listing_age_days is None or listing_age_days >= min_age_days
    graduated = state == "GRADUATED" or (quality_ok and age_ok)
    return {
        "ok": True,
        "pass": graduated,
        "state": "GRADUATED" if graduated else "PROBATION",
        "asset": asset,
        "listing_age_days": listing_age_days,
        "data_quality_score": data_quality_score,
        "methodology_version": METHODOLOGY_VERSION,
    }


def user_capital_constraint(
    *,
    declared_capital_usd: float | None,
    required_capital_usd: float,
) -> dict[str, Any]:
    """CAP-47 — never recommend above allowed capital; unknown != zero."""
    if declared_capital_usd is None:
        return {
            "ok": True,
            "pass": False,
            "state": "UNKNOWN",
            "reason": "capital_unknown_not_zero",
            "methodology_version": METHODOLOGY_VERSION,
        }
    return {
        "ok": True,
        "pass": required_capital_usd <= declared_capital_usd,
        "declared_capital_usd": declared_capital_usd,
        "required_capital_usd": required_capital_usd,
        "methodology_version": METHODOLOGY_VERSION,
    }


def user_risk_constraint(
    *,
    risk_score: float,
    max_risk: float | None,
    preferences: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """CAP-48 — server-side risk limit enforcement."""
    if max_risk is None:
        return {
            "ok": True,
            "pass": False,
            "state": "UNKNOWN",
            "reason": "risk_limit_not_configured",
            "methodology_version": METHODOLOGY_VERSION,
        }
    exceeded = risk_score > max_risk
    return {
        "ok": True,
        "pass": not exceeded,
        "risk_score": risk_score,
        "max_risk": max_risk,
        "preferences": preferences or {},
        "methodology_version": METHODOLOGY_VERSION,
    }
