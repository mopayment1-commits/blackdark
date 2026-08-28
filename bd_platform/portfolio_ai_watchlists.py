"""
Custom Watchlists — Feature #904 (Sprint 2).

Merged into Portfolio AI + Market Radar — NOT standalone watchlist service.
Tenant-isolated persistence with tier limits and rule-based alerts.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.PortfolioAIWatchlists")

_FEATURE_REF = 904
_STANDALONE = False
_MERGED_INTO = "Portfolio AI + Market Radar"
_SEED_PATH = Path("data/portfolio_ai_watchlists_seed.json")
_SYMBOL_RE = re.compile(r"^[A-Z0-9]{2,12}$")

_TIER_LIMITS = {
    "free": {"max_watchlists": 3, "max_assets_per_watchlist": 20},
    "pro": {"max_watchlists": 10, "max_assets_per_watchlist": 100},
    "institution": {"max_watchlists": None, "max_assets_per_watchlist": None},
}

_LOCK = threading.Lock()
_WATCHLISTS: dict[str, dict[str, Any]] = {}

_DISCLAIMER = (
    "Custom watchlists for Portfolio AI (assets) and Market Radar (events/narratives). "
    "Rule-based alerts only — no ML prediction. Tenant-isolated."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("watchlists seed load failed: %s", exc)
        return {}


def reset_watchlists_state_904() -> None:
    with _LOCK:
        _WATCHLISTS.clear()


def watchlists_status_904(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "surfaces": ["portfolio_ai", "market_radar"],
        "portfolio_ai": "asset watchlists — price, volume, signals",
        "market_radar": "event/narrative watchlists — unlocks, narratives",
        "tier_limits": _TIER_LIMITS,
        "tenant_isolation": True,
        "rule_based_alerts_only": True,
        "ml_prediction_rejected": True,
        "fee_db": (seed.get("watchlists_904") or {}).get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def _user_watchlists(user_id: str, tenant_id: str, surface: str | None = None) -> list[dict[str, Any]]:
    items = [
        w
        for w in _WATCHLISTS.values()
        if w["user_id"] == user_id and w["tenant_id"] == tenant_id and (surface is None or w["surface"] == surface)
    ]
    return sorted(items, key=lambda x: x.get("order", 0))


def _validate_asset_symbol(symbol: str) -> dict[str, Any]:
    sym = symbol.strip().upper()
    if not _SYMBOL_RE.match(sym):
        return {"ok": False, "error": "invalid_asset_symbol", "symbol": symbol, "injection_prevented": True}
    return {"ok": True, "symbol": sym}


def _tier_limits(tier: str) -> dict[str, Any]:
    return _TIER_LIMITS.get(tier, _TIER_LIMITS["free"])


def create_watchlist_904(
    *,
    user_id: str,
    tenant_id: str,
    tier: str,
    name: str,
    surface: str,
    asset_ids: list[str] | None = None,
    alerts_config: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    if surface not in ("portfolio_ai", "market_radar"):
        return {"ok": False, "error": "invalid_surface", "allowed": ["portfolio_ai", "market_radar"]}

    limits = _tier_limits(tier)
    existing = _user_watchlists(user_id, tenant_id, surface)
    max_wl = limits["max_watchlists"]
    if max_wl is not None and len(existing) >= max_wl:
        return {"ok": False, "error": "watchlist_limit_exceeded", "tier": tier, "limit": max_wl}

    assets: list[str] = []
    for sym in asset_ids or []:
        validated = _validate_asset_symbol(sym)
        if not validated.get("ok"):
            return validated
        assets.append(validated["symbol"])

    max_assets = limits["max_assets_per_watchlist"]
    if max_assets is not None and len(assets) > max_assets:
        return {"ok": False, "error": "asset_limit_exceeded", "tier": tier, "limit": max_assets}

    watchlist_id = f"wl_{uuid.uuid4().hex[:12]}"
    record = {
        "watchlist_id": watchlist_id,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "name": name,
        "surface": surface,
        "asset_ids": assets,
        "order": len(existing),
        "alerts_config": alerts_config or {"price_threshold": None, "volume_spike_pct": None},
        "rule_based_alerts": True,
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }

    with _LOCK:
        _WATCHLISTS[watchlist_id] = record

    fee = (seed.get("watchlists_904") or {}).get("fee_db") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "watchlist": record,
        "fee_db": {
            "storage_usd": fee.get("storage_per_watchlist_usd", 0.001),
            "sync_usd": fee.get("sync_per_watchlist_usd", 0.002),
            "alert_delivery_usd": fee.get("alert_delivery_usd", 0.0005),
        },
        "tenant_isolated": True,
    }


def update_watchlist_904(
    watchlist_id: str,
    *,
    user_id: str,
    tenant_id: str,
    tier: str,
    name: str | None = None,
    asset_ids: list[str] | None = None,
    alerts_config: dict[str, Any] | None = None,
    order: int | None = None,
) -> dict[str, Any]:
    with _LOCK:
        record = _WATCHLISTS.get(watchlist_id)
    if not record:
        return {"ok": False, "error": "watchlist_not_found"}
    if record["user_id"] != user_id or record["tenant_id"] != tenant_id:
        return {"ok": False, "error": "cross_tenant_access_denied", "tenant_isolation": True}

    if name is not None:
        record["name"] = name
    if order is not None:
        record["order"] = order
    if alerts_config is not None:
        record["alerts_config"] = {**record.get("alerts_config", {}), **alerts_config}
    if asset_ids is not None:
        limits = _tier_limits(tier)
        assets: list[str] = []
        for sym in asset_ids:
            validated = _validate_asset_symbol(sym)
            if not validated.get("ok"):
                return validated
            assets.append(validated["symbol"])
        max_assets = limits["max_assets_per_watchlist"]
        if max_assets is not None and len(assets) > max_assets:
            return {"ok": False, "error": "asset_limit_exceeded", "limit": max_assets}
        record["asset_ids"] = assets

    record["updated_at"] = _utcnow()
    with _LOCK:
        _WATCHLISTS[watchlist_id] = record

    return {"ok": True, "feature_ref": _FEATURE_REF, "watchlist": record}


def delete_watchlist_904(watchlist_id: str, *, user_id: str, tenant_id: str) -> dict[str, Any]:
    with _LOCK:
        record = _WATCHLISTS.get(watchlist_id)
        if not record:
            return {"ok": False, "error": "watchlist_not_found"}
        if record["user_id"] != user_id or record["tenant_id"] != tenant_id:
            return {"ok": False, "error": "cross_tenant_access_denied"}
        del _WATCHLISTS[watchlist_id]
    return {"ok": True, "feature_ref": _FEATURE_REF, "deleted": watchlist_id}


def list_watchlists_904(
    *,
    user_id: str,
    tenant_id: str,
    surface: str | None = None,
) -> dict[str, Any]:
    items = _user_watchlists(user_id, tenant_id, surface)
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "count": len(items),
        "watchlists": items,
        "tenant_isolated": True,
    }


def build_portfolio_ai_watchlist_dashboard_904(
    *,
    user_id: str,
    tenant_id: str,
    watchlist_id: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    with _LOCK:
        record = _WATCHLISTS.get(watchlist_id)
    if not record or record["user_id"] != user_id or record["tenant_id"] != tenant_id:
        return {"ok": False, "error": "watchlist_not_found_or_denied"}

    market_data = (seed.get("watchlists_904") or {}).get("sample_market_data") or {}
    assets_panel = []
    for sym in record.get("asset_ids") or []:
        quote = market_data.get(sym) or {"price_usd": None, "volume_24h_usd": None, "change_24h_pct": None}
        assets_panel.append({"symbol": sym, **quote})

    alerts = _evaluate_rule_alerts(record, assets_panel)
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "surface": "portfolio_ai",
        "watchlist": record,
        "assets": assets_panel,
        "alerts": alerts,
        "rule_based_only": True,
        "timestamp": _utcnow(),
    }


def build_market_radar_watchlist_dashboard_904(
    *,
    user_id: str,
    tenant_id: str,
    watchlist_id: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    with _LOCK:
        record = _WATCHLISTS.get(watchlist_id)
    if not record or record["user_id"] != user_id or record["tenant_id"] != tenant_id:
        return {"ok": False, "error": "watchlist_not_found_or_denied"}

    events = (seed.get("watchlists_904") or {}).get("sample_events") or []
    tracked = [e for e in events if e.get("asset") in (record.get("asset_ids") or [])]
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "surface": "market_radar",
        "watchlist": record,
        "events": tracked,
        "narratives": [e for e in tracked if e.get("type") == "narrative"],
        "unlocks": [e for e in tracked if e.get("type") == "unlock"],
        "timestamp": _utcnow(),
    }


def _evaluate_rule_alerts(watchlist: dict[str, Any], assets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cfg = watchlist.get("alerts_config") or {}
    price_threshold = cfg.get("price_threshold")
    volume_spike_pct = cfg.get("volume_spike_pct")
    alerts: list[dict[str, Any]] = []

    for asset in assets:
        price = asset.get("price_usd")
        change = asset.get("change_24h_pct")
        if price_threshold is not None and price is not None and float(price) >= float(price_threshold):
            alerts.append(
                {
                    "symbol": asset["symbol"],
                    "type": "price_threshold",
                    "rule_based": True,
                    "message": f"{asset['symbol']} crossed price threshold ${price_threshold}",
                }
            )
        if volume_spike_pct is not None and change is not None and abs(float(change)) >= float(volume_spike_pct):
            alerts.append(
                {
                    "symbol": asset["symbol"],
                    "type": "volume_spike",
                    "rule_based": True,
                    "message": f"{asset['symbol']} 24h change {change}% exceeds {volume_spike_pct}%",
                }
            )
    return alerts


def run_watchlists_e2e_904(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_watchlists_state_904()
    checks: list[dict[str, Any]] = []

    status = watchlists_status_904(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "dual_surface", "passed": "portfolio_ai" in status["surfaces"]})

    created = create_watchlist_904(
        user_id="user_free",
        tenant_id="tenant_a",
        tier="free",
        name="Core holdings",
        surface="portfolio_ai",
        asset_ids=["BTC", "ETH"],
        alerts_config={"price_threshold": 60000},
        seed=seed,
    )
    checks.append({"id": "create", "passed": created.get("ok") is True})

    wl_id = created["watchlist"]["watchlist_id"]
    updated = update_watchlist_904(
        wl_id, user_id="user_free", tenant_id="tenant_a", tier="free", name="Core + SOL", asset_ids=["BTC", "ETH", "SOL"]
    )
    checks.append({"id": "edit", "passed": updated.get("ok") is True})

    cross = update_watchlist_904(wl_id, user_id="other_user", tenant_id="tenant_b", tier="pro", name="Hack")
    checks.append({"id": "tenant_isolation", "passed": cross.get("error") == "cross_tenant_access_denied"})

    invalid = create_watchlist_904(
        user_id="user_free",
        tenant_id="tenant_a",
        tier="free",
        name="Inject",
        surface="portfolio_ai",
        asset_ids=["BTC'; DROP TABLE--"],
        seed=seed,
    )
    checks.append({"id": "symbol_validation", "passed": invalid.get("injection_prevented") is True})

    for i in range(3):
        create_watchlist_904(
            user_id="user_limit",
            tenant_id="tenant_a",
            tier="free",
            name=f"WL {i}",
            surface="portfolio_ai",
            asset_ids=["BTC"],
            seed=seed,
        )
    over_limit = create_watchlist_904(
        user_id="user_limit",
        tenant_id="tenant_a",
        tier="free",
        name="WL overflow",
        surface="portfolio_ai",
        asset_ids=["BTC"],
        seed=seed,
    )
    checks.append({"id": "tier_limits", "passed": over_limit.get("error") == "watchlist_limit_exceeded"})

    dashboard = build_portfolio_ai_watchlist_dashboard_904(
        user_id="user_free", tenant_id="tenant_a", watchlist_id=wl_id, seed=seed
    )
    checks.append({"id": "portfolio_dashboard", "passed": dashboard.get("ok") is True})

    radar = create_watchlist_904(
        user_id="user_pro",
        tenant_id="tenant_a",
        tier="pro",
        name="Unlock tracker",
        surface="market_radar",
        asset_ids=["ARB", "OP"],
        seed=seed,
    )
    radar_dash = build_market_radar_watchlist_dashboard_904(
        user_id="user_pro",
        tenant_id="tenant_a",
        watchlist_id=radar["watchlist"]["watchlist_id"],
        seed=seed,
    )
    checks.append({"id": "market_radar_dashboard", "passed": radar_dash.get("ok") is True})

    deleted = delete_watchlist_904(wl_id, user_id="user_free", tenant_id="tenant_a")
    checks.append({"id": "delete", "passed": deleted.get("ok") is True})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature_ref": _FEATURE_REF, "all_passed": all_passed, "checks": checks}
