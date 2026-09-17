"""
Launch-57 Phase 1 — Data Batch 1 canonical runtime spine.

Build order: #42 CAP-0504 → #22 CAP-0561 → #23 CAP-0507 → #24 CAP-0506/0513 → #21 CAP-0047
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from launch57.batch1_isolation import finalize_b1_response
from launch57.b1_freshness_bridge import apply_b1_freshness_reconciliation
from launch57.chart_common import attach_chart_envelope
from launch57.temporal_common import (
    TimestampUnit,
    attach_temporal_envelope,
    build_market_temporal_envelope,
    sort_by_temporal_key,
    to_rfc3339,
    utc_now,
    validate_provider_timestamp,
)
from market_context import (
    fetch_binance_klines_bars,
    fetch_binance_market_overview_pack,
    fetch_binance_ticker,
    fetch_symbol_exchange_metadata,
    normalize_oracle_symbol,
    probe_price_sources,
)

LAUNCH57_BATCH1_CAP_IDS: frozenset[int] = frozenset({47, 504, 506, 507, 513, 561})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    504: 42,
    561: 22,
    507: 23,
    506: 24,
    513: 24,
    47: 21,
}

_CONNECTOR_FETCHERS: tuple[tuple[str, str], ...] = (
    ("binance", "primary"),
    ("kraken", "fallback"),
    ("okx", "fallback"),
    ("bybit", "fallback"),
    ("coingecko", "fallback"),
    ("coinbase", "fallback"),
)


def _utcnow_iso() -> str:
    return to_rfc3339(utc_now())


def _attach_market_temporal(
    payload: dict[str, Any],
    *,
    source_raw: Any = None,
    source_unit: TimestampUnit | None = None,
    source_sequence: int | None = None,
    ingestion_sequence: int | None = None,
    immutable_event_id: str | None = None,
) -> dict[str, Any]:
    now = utc_now()
    envelope = build_market_temporal_envelope(
        source_raw=source_raw,
        source_unit=source_unit,
        observed_at=now,
        ingested_at=now,
        processed_at=now,
        source_sequence=source_sequence,
        ingestion_sequence=ingestion_sequence,
        immutable_event_id=immutable_event_id,
    )
    return attach_temporal_envelope(payload, envelope)


def _price_precision(price: float | None) -> int | None:
    if price is None:
        return None
    if price <= 0:
        return None
    d = Decimal(str(price)).normalize()
    exp = d.as_tuple().exponent
    if isinstance(exp, int) and exp < 0:
        return abs(exp)
    return 0


def _attach_b1_metadata(
    payload: dict[str, Any],
    *,
    source: str | None,
    source_raw: Any = None,
    source_unit: TimestampUnit | None = None,
) -> dict[str, Any]:
    out = dict(payload)
    out["source"] = source
    out["sources"] = [source] if source else []
    out["observed_at"] = _utcnow_iso()
    return _attach_market_temporal(
        out,
        source_raw=source_raw if source_raw is not None else out["observed_at"],
        source_unit=source_unit,
    )


def validate_ohlcv_invariants(bars: list[dict[str, Any]]) -> list[str]:
    violations: list[str] = []
    for i, bar in enumerate(bars):
        o, h, l, c, v = bar["open"], bar["high"], bar["low"], bar["close"], bar["volume"]
        if h < o or h < c or h < l:
            violations.append(f"bar[{i}].high_invariant")
        if l > o or l > c or l > h:
            violations.append(f"bar[{i}].low_invariant")
        if v < 0:
            violations.append(f"bar[{i}].volume_negative")
    return violations


async def unified_exchange_connector(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #42 / CAP-0504 — canonical exchange routing, no synthetic data."""
    params = dict(params or {})
    asset, pair = normalize_oracle_symbol(str(params.get("symbol") or symbol or "BTC"))
    probe = await probe_price_sources(asset)
    checks = probe.get("checks") or {}
    routes: list[dict[str, Any]] = []
    for provider, role in _CONNECTOR_FETCHERS:
        check = checks.get(provider) or checks.get(f"binance:{provider}")
        if provider == "binance":
            binance_ok = any(
                (checks.get(host) or {}).get("ok") for host in ("api.binance.com", "data-api.binance.vision", "api.binance.us")
            )
            routes.append(
                {
                    "provider": provider,
                    "role": role,
                    "available": binance_ok,
                    "source": probe.get("resolved_source") if binance_ok else None,
                }
            )
        else:
            row = checks.get(provider) or {}
            routes.append(
                {
                    "provider": provider,
                    "role": role,
                    "available": bool(row.get("ok")),
                    "source": row.get("source"),
                }
            )

    selected = next((r for r in routes if r.get("available")), None)
    body: dict[str, Any] = {
        "capability_id": 504,
        "launch_item_id": 42,
        "surface": "unified_exchange_connector_layer",
        "symbol": asset,
        "pair": pair,
        "canonical_symbol": asset,
        "routing_policy": "priority_failover_no_synthetic",
        "routes": routes,
        "selected_provider": (selected or {}).get("provider"),
        "health_probe": probe,
        "timeout_policy": {"rest_total_s": 12, "retry": "host_failover"},
        "success": selected is not None,
        "failure_state": None if selected else "UNAVAILABLE",
        "backend_module": "launch57.data_batch1",
        "backend_entrypoint": "unified_exchange_connector",
        "binding_source": "launch57_phase1_batch1",
    }
    if not selected:
        body["error"] = "no_exchange_route_available"
        body["success"] = False
    return finalize_b1_response(_attach_b1_metadata(body, source=body.get("selected_provider")))


async def _fetch_ticker_via_connector(asset: str, pair: str, connector: dict[str, Any]) -> dict[str, Any] | None:
    if not connector.get("success"):
        return None
    ticker = await fetch_binance_ticker(pair)
    if ticker:
        ticker.setdefault("pair", pair)
        ticker.setdefault("asset", asset)
        return ticker
    return None


async def real_time_prices(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #22 / CAP-0561 — temporal price path; freshness semantics blocked until #41 reconciliation."""
    params = dict(params or {})
    asset, pair = normalize_oracle_symbol(str(params.get("symbol") or symbol or "BTC"))
    connector = await unified_exchange_connector(symbol=asset, params=params)
    ticker = await _fetch_ticker_via_connector(asset, pair, connector)

    if not ticker or float(ticker.get("price") or 0) <= 0:
        body = {
            "capability_id": 561,
            "launch_item_id": 22,
            "surface": "real_time_prices",
            "symbol": asset,
            "pair": pair,
            "availability": "UNAVAILABLE",
            "success": False,
            "error": "price_unavailable",
            "connector": {"selected_provider": connector.get("selected_provider"), "success": connector.get("success")},
            "backend_module": "launch57.data_batch1",
            "backend_entrypoint": "real_time_prices",
            "binding_source": "launch57_phase1_batch1",
        }
        return finalize_b1_response(
            _attach_b1_metadata(body, source=None),
            require_freshness_owner=True,
        )

    age_sec = float(ticker.get("age_sec") or 0)
    if ticker.get("freshness_ms") is not None:
        age_sec = float(ticker["freshness_ms"]) / 1000.0

    price = float(ticker["price"])
    source_raw = ticker.get("timestamp") or ticker.get("event_time") or ticker.get("source_time")
    source_validation = validate_provider_timestamp(source_raw) if source_raw is not None else None
    if source_raw is not None and source_validation and not source_validation.ok:
        body = {
            "capability_id": 561,
            "launch_item_id": 22,
            "surface": "real_time_prices",
            "symbol": asset,
            "pair": pair,
            "availability": "UNAVAILABLE",
            "success": False,
            "error": f"provider_timestamp_invalid:{source_validation.error}",
            "provider_timestamp_validation": {
                "ok": False,
                "error": source_validation.error,
                "raw": source_raw,
            },
            "backend_module": "launch57.data_batch1",
            "backend_entrypoint": "real_time_prices",
            "binding_source": "launch57_phase1_batch1",
        }
        return finalize_b1_response(
            _attach_b1_metadata(body, source=None, source_raw=source_raw),
            require_freshness_owner=True,
        )

    body: dict[str, Any] = {
        "capability_id": 561,
        "launch_item_id": 22,
        "surface": "real_time_prices",
        "symbol": asset,
        "pair": pair,
        "price": price,
        "unit": "USDT",
        "precision": _price_precision(price),
        "change_24h": ticker.get("change_24h"),
        "volume": ticker.get("volume"),
        "quote_volume": ticker.get("quote_volume"),
        "provider": ticker.get("source"),
        "event_timestamp": to_rfc3339(source_validation.canonical) if source_validation and source_validation.canonical else _utcnow_iso(),
        "update_timestamp": _utcnow_iso(),
        "data_age_sec": age_sec,
        "connector_ref": connector.get("selected_provider"),
        "success": True,
        "price_data_available": True,
        "backend_module": "launch57.data_batch1",
        "backend_entrypoint": "real_time_prices",
        "binding_source": "launch57_phase1_batch1",
    }
    out = _attach_b1_metadata(
        body,
        source=str(ticker.get("source")),
        source_raw=source_raw,
        source_unit=source_validation.unit if source_validation else None,
    )
    out = finalize_b1_response(out, require_freshness_owner=False)
    return apply_b1_freshness_reconciliation(
        out,
        age_sec=age_sec if age_sec else None,
        source_time=source_raw,
        temporal=out.get("temporal"),
    )  # canonical #41 freshness via b1_freshness_bridge


async def ohlcv(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #23 / CAP-0507 — full OHLCV bars with invariant checks."""
    params = dict(params or {})
    asset, pair = normalize_oracle_symbol(str(params.get("symbol") or symbol or "BTC"))
    interval = str(params.get("interval") or "1h")
    limit = int(params.get("limit") or 100)

    connector = await unified_exchange_connector(symbol=asset, params=params)
    if not connector.get("success"):
        body = {
            "capability_id": 507,
            "launch_item_id": 23,
            "surface": "ohlcv",
            "symbol": asset,
            "pair": pair,
            "interval": interval,
            "success": False,
            "error": "connector_unavailable",
            "backend_module": "launch57.data_batch1",
            "backend_entrypoint": "ohlcv",
            "binding_source": "launch57_phase1_batch1",
        }
        return attach_chart_envelope(finalize_b1_response(body), params=params)

    bars, source_host = await fetch_binance_klines_bars(pair, interval=interval, limit=limit)
    violations = validate_ohlcv_invariants(bars) if bars else ["no_bars"]
    ordered_bars = bars
    if bars:
        bar_rows = [
            {
                "open_time_ms": bar.get("open_time_ms"),
                "source_sequence": idx,
                "ingestion_sequence": idx,
                "immutable_event_id": f"{pair}:{interval}:{bar.get('open_time_ms')}",
                **bar,
            }
            for idx, bar in enumerate(bars)
        ]
        ordered_bars = sort_by_temporal_key(bar_rows, time_field="open_time_ms")

    body: dict[str, Any] = {
        "capability_id": 507,
        "launch_item_id": 23,
        "surface": "ohlcv",
        "symbol": asset,
        "pair": pair,
        "interval": interval,
        "timezone": "UTC",
        "bar_order": "ascending_by_open_time",
        "bars": ordered_bars,
        "bar_count": len(ordered_bars),
        "partial_semantics": "incomplete_tail_candle_may_exist",
        "invariant_violations": violations,
        "provider": f"binance:{source_host}",
        "success": bool(bars) and not violations,
        "backend_module": "launch57.data_batch1",
        "backend_entrypoint": "ohlcv",
        "binding_source": "launch57_phase1_batch1",
    }
    if violations:
        body["error"] = "ohlcv_invariant_violation" if bars else "ohlcv_unavailable"
        body["success"] = False

    first_open = ordered_bars[0].get("open_time_ms") if ordered_bars else None
    body = _attach_b1_metadata(
        body,
        source=body.get("provider"),
        source_raw=first_open,
        source_unit=TimestampUnit.MILLISECONDS if first_open is not None else None,
    )
    return attach_chart_envelope(finalize_b1_response(body), params=params)


async def quote_data(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #24 / CAP-0506 — quote payload (distinct from metadata)."""
    params = dict(params or {})
    asset, pair = normalize_oracle_symbol(str(params.get("symbol") or symbol or "BTC"))
    connector = await unified_exchange_connector(symbol=asset, params=params)
    ticker = await _fetch_ticker_via_connector(asset, pair, connector)

    if not ticker:
        body = {
            "capability_id": 506,
            "launch_item_id": 24,
            "surface": "quote_data",
            "symbol": asset,
            "pair": pair,
            "quote": None,
            "success": False,
            "error": "quote_unavailable",
            "unknown_is_not_zero": True,
            "backend_module": "launch57.data_batch1",
            "backend_entrypoint": "quote_data",
            "binding_source": "launch57_phase1_batch1",
        }
        return finalize_b1_response(body)

    price = float(ticker.get("price") or 0)
    quote = {
        "last": price if price > 0 else None,
        "change_24h_pct": ticker.get("change_24h"),
        "volume_base": ticker.get("volume"),
        "volume_quote": ticker.get("quote_volume"),
        "bid": ticker.get("bid"),
        "ask": ticker.get("ask"),
        "unit": "USDT",
        "precision": _price_precision(price if price > 0 else None),
    }
    body = {
        "capability_id": 506,
        "launch_item_id": 24,
        "surface": "quote_data",
        "symbol": asset,
        "pair": pair,
        "quote": quote,
        "provider": ticker.get("source"),
        "success": quote["last"] is not None,
        "unknown_is_not_zero": True,
        "backend_module": "launch57.data_batch1",
        "backend_entrypoint": "quote_data",
        "binding_source": "launch57_phase1_batch1",
    }
    return finalize_b1_response(_attach_b1_metadata(body, source=str(ticker.get("source"))))


async def symbol_metadata(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #24 / CAP-0513 — symbol metadata (distinct contract from quote)."""
    params = dict(params or {})
    asset, pair = normalize_oracle_symbol(str(params.get("symbol") or symbol or "BTC"))
    meta = await fetch_symbol_exchange_metadata(pair)

    if not meta:
        body = {
            "capability_id": 513,
            "launch_item_id": 24,
            "surface": "asset_symbol_metadata",
            "symbol": asset,
            "pair": pair,
            "metadata": None,
            "success": False,
            "error": "symbol_metadata_unavailable",
            "ambiguous_or_delisted": True,
            "backend_module": "launch57.data_batch1",
            "backend_entrypoint": "symbol_metadata",
            "binding_source": "launch57_phase1_batch1",
        }
        return finalize_b1_response(body)

    if meta.get("delisted"):
        body = {
            "capability_id": 513,
            "launch_item_id": 24,
            "surface": "asset_symbol_metadata",
            "symbol": asset,
            "pair": pair,
            "metadata": meta,
            "success": False,
            "error": "symbol_not_trading",
            "ambiguous_or_delisted": True,
            "backend_module": "launch57.data_batch1",
            "backend_entrypoint": "symbol_metadata",
            "binding_source": "launch57_phase1_batch1",
        }
        return finalize_b1_response(_attach_b1_metadata(body, source=meta.get("provider")))

    body = {
        "capability_id": 513,
        "launch_item_id": 24,
        "surface": "asset_symbol_metadata",
        "symbol": asset,
        "pair": pair,
        "metadata": meta,
        "success": True,
        "ambiguous_or_delisted": False,
        "backend_module": "launch57.data_batch1",
        "backend_entrypoint": "symbol_metadata",
        "binding_source": "launch57_phase1_batch1",
    }
    return finalize_b1_response(_attach_b1_metadata(body, source=meta.get("provider")))


async def spot_market_metrics_suite(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #21 / CAP-0047 — spot metrics with canonical #41 freshness reconciliation."""
    params = dict(params or {})
    asset, pair = normalize_oracle_symbol(str(params.get("symbol") or symbol or "BTC"))
    limit = int(params.get("limit") or 20)

    connector = await unified_exchange_connector(symbol=asset, params={"symbol": asset})
    overview = await fetch_binance_market_overview_pack(limit=limit)
    probe = await probe_price_sources(asset)

    data_source = overview.get("data_source") or "unavailable"
    assets = list(overview.get("assets") or [])
    focal = next((a for a in assets if str(a.get("symbol")).upper() == asset), None)
    ticker = await _fetch_ticker_via_connector(asset, pair, connector) if connector.get("success") else None

    metrics: dict[str, Any] = {}
    if focal:
        metrics = {
            "price": focal.get("price"),
            "change_24h": focal.get("change_24h"),
            "volume_24h": focal.get("volume_24h"),
            "score": focal.get("score"),
            "verdict": focal.get("verdict"),
            "sector": focal.get("sector"),
            "unit": "USDT",
            "precision": _price_precision(float(focal["price"])) if focal.get("price") else None,
            "lineage": f"overview:{data_source}",
        }
    elif ticker:
        metrics = {
            "price": ticker.get("price"),
            "change_24h": ticker.get("change_24h"),
            "volume_24h": ticker.get("quote_volume") or ticker.get("volume"),
            "unit": "USDT",
            "precision": _price_precision(float(ticker["price"])) if ticker.get("price") else None,
            "lineage": f"ticker:{ticker.get('source')}",
        }
    else:
        metrics = {
            "price": None,
            "change_24h": None,
            "volume_24h": None,
            "unit": "USDT",
            "lineage": "unavailable",
        }

    body = {
        "capability_id": 47,
        "launch_item_id": 21,
        "surface": "spot_market_metrics_suite",
        "symbol": asset,
        "pair": pair,
        "metrics": metrics,
        "overview_source": data_source,
        "overview_count": len(assets),
        "probe_resolved": probe.get("resolved"),
        "unknown_is_not_zero": True,
        "success": metrics.get("price") is not None,
        "backend_module": "launch57.data_batch1",
        "backend_entrypoint": "spot_market_metrics_suite",
        "binding_source": "launch57_phase1_batch1",
    }
    if metrics.get("price") is None:
        body["error"] = "metrics_unavailable"

    out = finalize_b1_response(_attach_b1_metadata(body, source=data_source), require_freshness_owner=False)
    age_sec = None
    if ticker and ticker.get("age_sec") is not None:
        age_sec = float(ticker.get("age_sec"))
    elif ticker and ticker.get("freshness_ms") is not None:
        age_sec = float(ticker["freshness_ms"]) / 1000.0
    return apply_b1_freshness_reconciliation(
        out,
        age_sec=age_sec,
        source_time=(ticker or {}).get("timestamp"),
        temporal=out.get("temporal"),
    )


_DISPATCH_ENTRYPOINTS: dict[int, str] = {
    504: "unified_exchange_connector",
    561: "real_time_prices",
    507: "ohlcv",
    506: "quote_data",
    513: "symbol_metadata",
    47: "spot_market_metrics_suite",
}


async def execute_launch57_batch1(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in LAUNCH57_BATCH1_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 data batch 1")
    entrypoint = _DISPATCH_ENTRYPOINTS[capability_id]
    fn = globals()[entrypoint]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
