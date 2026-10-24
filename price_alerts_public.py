"""
Simple public price alerts — above/below targets using live spot (Binance chain).
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from config import DATA_DIR

logger = logging.getLogger("BLACKDARK.PriceAlerts")

_STORE_PATH = DATA_DIR / "price_alerts_public.json"
_MAX_PER_CLIENT = 10
_MAX_TOTAL = 5000
_CLIENT_RE = re.compile(r"^[a-f0-9-]{16,64}$", re.I)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load() -> dict[str, Any]:
    try:
        if _STORE_PATH.exists():
            raw = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and isinstance(raw.get("alerts"), list):
                return raw
    except (OSError, json.JSONDecodeError):
        pass
    return {"alerts": []}


def _save(row: dict[str, Any]) -> None:
    try:
        _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _STORE_PATH.write_text(json.dumps(row), encoding="utf-8")
    except OSError:
        logger.debug("price alerts persist failed")


def normalize_client_id(raw: str | None) -> str | None:
    cid = (raw or "").strip().lower()
    if not cid or not _CLIENT_RE.match(cid):
        return None
    return cid


def normalize_symbol(raw: str) -> str | None:
    sym = (raw or "").upper().strip().replace("/", "").replace("-", "")
    if sym.endswith("USDT"):
        sym = sym[:-4]
    if not sym or not sym.isalnum() or len(sym) > 12:
        return None
    import config

    allowed = {str(a).upper() for a in getattr(config, "WHITELIST_ASSETS", ())}
    if allowed and sym not in allowed:
        return None
    return sym


def list_alerts(client_id: str) -> list[dict[str, Any]]:
    cid = normalize_client_id(client_id)
    if not cid:
        return []
    store = _load()
    out: list[dict[str, Any]] = []
    for row in store.get("alerts") or []:
        if not isinstance(row, dict):
            continue
        if str(row.get("client_id") or "").lower() == cid:
            out.append(row)
    out.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    return out


async def _spot_price(symbol: str) -> dict[str, Any] | None:
    pair = f"{symbol}USDT"
    from binance_public_api import fetch_public_spot_market

    row = await fetch_public_spot_market(pair)
    if row is None:
        from market_context import fetch_binance_ticker

        row = await fetch_binance_ticker(pair)
    if row is None:
        from coinpaprika_public_api import fetch_ticker_for_asset

        row = await fetch_ticker_for_asset(symbol)
    if not row:
        return None
    try:
        price = float(row.get("price") or 0)
    except (TypeError, ValueError):
        return None
    if price <= 0:
        return None
    return {
        "price": price,
        "source": str(row.get("source") or "binance"),
        "change_24h": row.get("change_24h"),
    }


def _is_triggered(direction: str, target: float, price: float) -> bool:
    d = direction.lower()
    if d == "above":
        return price >= target
    if d == "below":
        return price <= target
    return False


async def evaluate_alerts(client_id: str) -> dict[str, Any]:
    cid = normalize_client_id(client_id)
    if not cid:
        return {"ok": False, "error": "invalid_client_id"}
    store = _load()
    alerts = store.get("alerts") or []
    symbols = sorted(
        {
            str(r.get("symbol") or "").upper()
            for r in alerts
            if isinstance(r, dict) and str(r.get("client_id") or "").lower() == cid
        }
    )
    prices: dict[str, dict[str, Any]] = {}
    for sym in symbols:
        if not sym:
            continue
        px = await _spot_price(sym)
        if px:
            prices[sym] = px

    enriched: list[dict[str, Any]] = []
    changed = False
    for row in alerts:
        if not isinstance(row, dict) or str(row.get("client_id") or "").lower() != cid:
            continue
        sym = str(row.get("symbol") or "").upper()
        px = prices.get(sym)
        item = dict(row)
        if px:
            item["current_price"] = px["price"]
            item["price_source"] = px["source"]
            try:
                target = float(row.get("target_price") or 0)
            except (TypeError, ValueError):
                target = 0.0
            fired = _is_triggered(str(row.get("direction") or ""), target, float(px["price"]))
            item["condition_met"] = fired and not bool(row.get("triggered"))
            if fired and not row.get("triggered"):
                row["triggered"] = True
                row["triggered_at"] = _utcnow()
                item["triggered"] = True
                item["triggered_at"] = row["triggered_at"]
                changed = True
            else:
                item["triggered"] = bool(row.get("triggered"))
        enriched.append(item)

    if changed:
        _save(store)
    return {
        "ok": True,
        "client_id": cid,
        "alerts": enriched,
        "prices": prices,
        "checked_at": _utcnow(),
    }


async def create_alert(
    *,
    client_id: str,
    symbol: str,
    direction: str,
    target_price: float,
) -> dict[str, Any]:
    cid = normalize_client_id(client_id)
    if not cid:
        return {"ok": False, "error": "invalid_client_id"}
    sym = normalize_symbol(symbol)
    if not sym:
        return {"ok": False, "error": "invalid_symbol"}
    d = (direction or "").lower().strip()
    if d not in {"above", "below"}:
        return {"ok": False, "error": "invalid_direction"}
    try:
        target = float(target_price)
    except (TypeError, ValueError):
        return {"ok": False, "error": "invalid_target_price"}
    if target <= 0:
        return {"ok": False, "error": "invalid_target_price"}

    store = _load()
    alerts = [r for r in (store.get("alerts") or []) if isinstance(r, dict)]
    if len(alerts) >= _MAX_TOTAL:
        return {"ok": False, "error": "store_full"}
    mine = [r for r in alerts if str(r.get("client_id") or "").lower() == cid]
    if len(mine) >= _MAX_PER_CLIENT:
        return {"ok": False, "error": "limit_reached", "max": _MAX_PER_CLIENT}

    row = {
        "id": str(uuid.uuid4()),
        "client_id": cid,
        "symbol": sym,
        "direction": d,
        "target_price": target,
        "created_at": _utcnow(),
        "triggered": False,
        "triggered_at": None,
    }
    alerts.append(row)
    store["alerts"] = alerts
    _save(store)
    return {"ok": True, "alert": row}


def delete_alert(client_id: str, alert_id: str) -> dict[str, Any]:
    cid = normalize_client_id(client_id)
    if not cid:
        return {"ok": False, "error": "invalid_client_id"}
    aid = (alert_id or "").strip()
    if not aid:
        return {"ok": False, "error": "invalid_id"}
    store = _load()
    alerts = store.get("alerts") or []
    kept = [
        r
        for r in alerts
        if not (
            isinstance(r, dict)
            and str(r.get("id")) == aid
            and str(r.get("client_id") or "").lower() == cid
        )
    ]
    if len(kept) == len(alerts):
        return {"ok": False, "error": "not_found"}
    store["alerts"] = kept
    _save(store)
    return {"ok": True}
