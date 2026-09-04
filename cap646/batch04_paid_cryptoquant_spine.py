"""Batch04 paid CryptoQuant spine — #187 inflow, #188 outflow, #190 reserve.

Design-complete, env-gated: set ``CRYPTOQUANT_API_KEY`` to activate live calls.
Without a key the handler returns ``PENDING_PAYMENT`` (no fake exchange metrics).
"""

from __future__ import annotations

import time
from typing import Any

from cap646.paid_vendor_spine import (
    CRYPTOQUANT_VENDOR,
    PENDING_PAYMENT_STATUS,
    PaidCapabilitySpec,
    build_pending_payment_payload,
    paid_vendor_api_key,
    paid_vendor_get_json,
)

_CRYPTOQUANT_BASE = "https://api.cryptoquant.com/v1"

_CAP_SPECS: dict[int, PaidCapabilitySpec] = {
    187: PaidCapabilitySpec(187, "exchange_inflow_intelligence", CRYPTOQUANT_VENDOR),
    188: PaidCapabilitySpec(188, "exchange_outflow_intelligence", CRYPTOQUANT_VENDOR),
    190: PaidCapabilitySpec(190, "exchange_supply_balance_intelligence", CRYPTOQUANT_VENDOR),
}

_METRIC_PATHS: dict[int, str] = {
    187: "inflow",
    188: "outflow",
    190: "reserve",
}


def _asset_slug(symbol: str) -> str:
    sym = symbol.upper().replace("/USDT", "").strip()
    mapping = {"BTC": "btc", "ETH": "eth", "USDT": "stablecoin", "USDC": "stablecoin"}
    return mapping.get(sym, sym.lower())


def _latest_point(data: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not data:
        return None
    point = data[-1]
    return point if isinstance(point, dict) else None


def _parse_cryptoquant_series(body: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    status = body.get("status") or {}
    if isinstance(status, dict) and status.get("code") not in (200, "200", None):
        return [], str(status.get("message") or "vendor_error")
    result = body.get("result") or {}
    if not isinstance(result, dict):
        return [], "invalid_result_envelope"
    rows = result.get("data") or []
    if not isinstance(rows, list):
        return [], "invalid_data_array"
    window = str(result.get("window") or "day")
    return rows, window


async def _fetch_cryptoquant_metric(
    capability_id: int,
    *,
    symbol: str,
    exchange: str,
    limit: int,
    api_key: str,
) -> dict[str, Any]:
    metric = _METRIC_PATHS[capability_id]
    asset = _asset_slug(symbol)
    url = f"{_CRYPTOQUANT_BASE}/{asset}/exchange-flows/{metric}"
    params = {"exchange": exchange, "window": "day", "limit": max(1, min(limit, 30))}
    t0 = time.perf_counter()
    body = await paid_vendor_get_json(url, api_key=api_key, params=params)
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
    if body is None:
        return {"ok": False, "error": "vendor_unreachable", "latency_ms": latency_ms}
    if body.get("ok") is False:
        body.setdefault("latency_ms", latency_ms)
        return body
    rows, window = _parse_cryptoquant_series(body)
    latest = _latest_point(rows)
    if latest is None:
        return {"ok": False, "error": "vendor_empty_series", "latency_ms": latency_ms}
    return {
        "ok": True,
        "rows": rows,
        "latest": latest,
        "window": window,
        "latency_ms": body.get("_latency_ms", latency_ms),
        "source": "cryptoquant_live",
    }


def _pending_fields(capability_id: int) -> dict[str, Any]:
    if capability_id == 187:
        return {
            "inflow_usd": None,
            "inflow_native": None,
            "exchange_inflow_status": PENDING_PAYMENT_STATUS,
        }
    if capability_id == 188:
        return {
            "outflow_usd": None,
            "outflow_native": None,
            "alert_confirmation": None,
        }
    return {
        "supply_on_exchanges_pct": None,
        "exchange_supply": None,
        "reserve_native": None,
        "reserve_usd": None,
    }


def _live_fields(capability_id: int, latest: dict[str, Any], *, exchange: str, symbol: str) -> dict[str, Any]:
    if capability_id == 187:
        inflow_total = latest.get("inflow_total")
        return {
            "inflow_native": inflow_total,
            "inflow_usd": None,
            "inflow_mean": latest.get("inflow_mean"),
            "inflow_top10": latest.get("inflow_top10"),
            "exchange_inflow_status": "live",
            "exchange": exchange,
            "observation_date": latest.get("date") or latest.get("datetime"),
        }
    if capability_id == 188:
        outflow_total = latest.get("outflow_total")
        return {
            "outflow_native": outflow_total,
            "outflow_usd": None,
            "outflow_mean": latest.get("outflow_mean"),
            "outflow_top10": latest.get("outflow_top10"),
            "alert_confirmation": False,
            "exchange": exchange,
            "observation_date": latest.get("date") or latest.get("datetime"),
        }
    reserve = latest.get("reserve")
    reserve_usd = latest.get("reserve_usd")
    return {
        "reserve_native": reserve,
        "reserve_usd": reserve_usd,
        "supply_on_exchanges_pct": None,
        "exchange_supply": {"exchange": exchange, "reserve": reserve, "reserve_usd": reserve_usd},
        "exchange": exchange,
        "observation_date": latest.get("date") or latest.get("datetime"),
    }


async def build_cryptoquant_capability(
    capability_id: int,
    *,
    symbol: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    spec = _CAP_SPECS[capability_id]
    exchange = str(params.get("exchange") or "binance").lower()
    limit = int(params.get("limit") or 5)
    api_key = paid_vendor_api_key(spec.vendor.env_var)

    if api_key is None:
        return build_pending_payment_payload(
            spec,
            symbol=symbol,
            extra=_pending_fields(capability_id),
        )

    fetched = await _fetch_cryptoquant_metric(
        capability_id,
        symbol=symbol,
        exchange=exchange,
        limit=limit,
        api_key=api_key,
    )
    if not fetched.get("ok"):
        return {
            "ok": False,
            "feature_ref": capability_id,
            "symbol": symbol.upper(),
            "catalog_goal": spec.catalog_goal,
            "vendor_status": "VENDOR_ERROR",
            "status": f"CryptoQuant call failed: {fetched.get('error')}",
            "vendor": spec.vendor.vendor_id,
            "env_var": spec.vendor.env_var,
            "data_available": False,
            "live_vendor_call": True,
            "exchange": exchange,
            "error": fetched.get("error"),
            "latency_ms": fetched.get("latency_ms"),
        }

    latest = fetched["latest"]
    payload: dict[str, Any] = {
        "ok": True,
        "feature_ref": capability_id,
        "symbol": symbol.upper(),
        "catalog_goal": spec.catalog_goal,
        "vendor_status": "LIVE",
        "status": "live",
        "vendor": spec.vendor.vendor_id,
        "env_var": spec.vendor.env_var,
        "data_available": True,
        "live_vendor_call": True,
        "attribution": "Data: CryptoQuant (paid subscription)",
        "series_window": fetched.get("window"),
        "series_points": len(fetched.get("rows") or []),
        "latency_ms": fetched.get("latency_ms"),
    }
    payload.update(_live_fields(capability_id, latest, exchange=exchange, symbol=symbol))
    return payload


async def build_exchange_inflow_187(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    return await build_cryptoquant_capability(187, symbol=symbol, params=params)


async def build_exchange_outflow_188(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    return await build_cryptoquant_capability(188, symbol=symbol, params=params)


async def build_exchange_supply_balance_190(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    return await build_cryptoquant_capability(190, symbol=symbol, params=params)
