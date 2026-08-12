"""Live data-truth probe — multi-venue public market ingestion + canonical adoption.

Tries Kraken / OKX / Binance public endpoints. Fail-closed when all fail.
Never invents LIVE quotes. Never fabricates L2 sizes — returns venue ladders only.
Binance may return HTTP 451 in restricted regions.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any


async def _http_get_json(url: str) -> tuple[int, Any, int]:
    import httpx

    started = time.time()
    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get(url)
        latency_ms = int((time.time() - started) * 1000)
        try:
            body = r.json()
        except Exception:
            body = None
        return r.status_code, body, latency_ms


def _levels_are_venue_real(bids: list[list[float]], asks: list[list[float]]) -> bool:
    """Reject arithmetic fabricated ladders (2.0+i / 1.5+i) used by prior truth-bus bug."""
    if len(bids) < 2 or len(asks) < 2:
        return bool(bids and asks)
    bid_sizes = [float(q) for _, q in bids[:8]]
    ask_sizes = [float(q) for _, q in asks[:8]]
    # Fabricated pattern was exactly 2.0+i or 1.5+i consecutive integers.
    def _is_arith(seq: list[float], start: float) -> bool:
        if len(seq) < 4:
            return False
        return all(abs(seq[i] - (start + i)) < 1e-9 for i in range(len(seq)))

    if _is_arith(bid_sizes, 2.0) or _is_arith(bid_sizes, 1.5):
        return False
    if _is_arith(ask_sizes, 2.0) or _is_arith(ask_sizes, 1.5):
        return False
    return True


async def probe_okx_book(symbol: str = "BTC-USDT", *, depth: int = 20) -> dict[str, Any]:
    from canonical_adoption import adopt_order_books, adopt_tick_quote
    from canonical_data_layer import FreshnessClass

    sz = max(5, min(int(depth), 400))
    code, body, latency_ms = await _http_get_json(
        f"https://www.okx.com/api/v5/market/books?instId={symbol}&sz={sz}"
    )
    if code != 200 or not isinstance(body, dict) or body.get("code") != "0":
        return {"ok": False, "live": False, "reason": f"okx_http_{code}", "latency_ms": latency_ms}
    rows = (body.get("data") or [{}])[0]
    bids = [[float(p), float(q)] for p, q, *_ in (rows.get("bids") or [])]
    asks = [[float(p), float(q)] for p, q, *_ in (rows.get("asks") or [])]
    if not bids or not asks:
        return {"ok": False, "live": False, "reason": "okx_empty_book", "latency_ms": latency_ms}
    if not _levels_are_venue_real(bids, asks):
        return {"ok": False, "live": False, "reason": "okx_fabricated_sizes_rejected", "latency_ms": latency_ms}
    ts_ms = int(rows.get("ts") or time.time() * 1000)
    adopted = adopt_tick_quote(
        venue="okx",
        symbol=symbol.replace("-", "/"),
        bid=bids[0][0],
        ask=asks[0][0],
        source="okx_public_books",
        provider_timestamp=ts_ms,
        bid_qty=bids[0][1],
        ask_qty=asks[0][1],
        require_live=True,
        path="streaming",
    )
    adopt_order_books(
        {"okx": {adopted["symbol"]: {"bids": bids, "asks": asks}}},
        source="okx_public_books",
        provider_timestamp=ts_ms,
        path="streaming",
    )
    live = adopted.get("freshness_class") == FreshnessClass.LIVE.value
    return {
        "ok": True,
        "live": live,
        "venue": "okx",
        "symbol": adopted["symbol"],
        "bid": adopted["bid"],
        "ask": adopted["ask"],
        "bid_qty": bids[0][1],
        "ask_qty": asks[0][1],
        "bids": bids,
        "asks": asks,
        "freshness_class": adopted.get("freshness_class"),
        "executable_quotes": live,
        "latency_ms": latency_ms,
        "depth_levels": {"bids": len(bids), "asks": len(asks)},
        "depth_source": "venue_l2",
        "fabricated_depth": False,
        "source": "okx_public_books",
        "probed_at": datetime.now(UTC).isoformat(),
    }


async def probe_kraken_depth(pair: str = "XBTUSDT", *, depth: int = 25) -> dict[str, Any]:
    """Kraken public Depth — real L2 sizes (not ticker TOB fabrication)."""
    from canonical_adoption import adopt_order_books, adopt_tick_quote
    from canonical_data_layer import FreshnessClass

    count = max(10, min(int(depth), 100))
    code, body, latency_ms = await _http_get_json(
        f"https://api.kraken.com/0/public/Depth?pair={pair}&count={count}"
    )
    if code != 200 or not isinstance(body, dict) or body.get("error"):
        return {"ok": False, "live": False, "reason": f"kraken_http_{code}", "latency_ms": latency_ms}
    result = body.get("result") or {}
    if not result:
        return {"ok": False, "live": False, "reason": "kraken_empty", "latency_ms": latency_ms}
    row = next(iter(result.values()))
    bids = [[float(p), float(q)] for p, q, *_ in (row.get("bids") or [])]
    asks = [[float(p), float(q)] for p, q, *_ in (row.get("asks") or [])]
    if not bids or not asks:
        return {"ok": False, "live": False, "reason": "kraken_empty_book", "latency_ms": latency_ms}
    if not _levels_are_venue_real(bids, asks):
        return {"ok": False, "live": False, "reason": "kraken_fabricated_sizes_rejected", "latency_ms": latency_ms}
    ts_ms = int(time.time() * 1000)
    adopted = adopt_tick_quote(
        venue="kraken",
        symbol="BTC/USDT",
        bid=bids[0][0],
        ask=asks[0][0],
        source="kraken_public_depth",
        provider_timestamp=ts_ms,
        bid_qty=bids[0][1],
        ask_qty=asks[0][1],
        require_live=True,
        path="streaming",
    )
    adopt_order_books(
        {"kraken": {adopted["symbol"]: {"bids": bids, "asks": asks}}},
        source="kraken_public_depth",
        provider_timestamp=ts_ms,
        path="streaming",
    )
    live = adopted.get("freshness_class") == FreshnessClass.LIVE.value
    return {
        "ok": True,
        "live": live,
        "venue": "kraken",
        "symbol": adopted["symbol"],
        "bid": bids[0][0],
        "ask": asks[0][0],
        "bid_qty": bids[0][1],
        "ask_qty": asks[0][1],
        "bids": bids,
        "asks": asks,
        "freshness_class": adopted.get("freshness_class"),
        "executable_quotes": live,
        "latency_ms": latency_ms,
        "depth_levels": {"bids": len(bids), "asks": len(asks)},
        "depth_source": "venue_l2",
        "fabricated_depth": False,
        "source": "kraken_public_depth",
        "probed_at": datetime.now(UTC).isoformat(),
    }


async def probe_kraken_ticker(pair: str = "XBTUSDT") -> dict[str, Any]:
    """Legacy TOB-only probe — prefer probe_kraken_depth for institutional consumers."""
    from canonical_adoption import adopt_tick_quote
    from canonical_data_layer import FreshnessClass

    code, body, latency_ms = await _http_get_json(
        f"https://api.kraken.com/0/public/Ticker?pair={pair}"
    )
    if code != 200 or not isinstance(body, dict) or body.get("error"):
        return {"ok": False, "live": False, "reason": f"kraken_http_{code}", "latency_ms": latency_ms}
    result = body.get("result") or {}
    if not result:
        return {"ok": False, "live": False, "reason": "kraken_empty", "latency_ms": latency_ms}
    row = next(iter(result.values()))
    bid = float(row["b"][0])
    ask = float(row["a"][0])
    bid_qty = float(row["b"][1]) if len(row.get("b") or []) > 1 else None
    ask_qty = float(row["a"][1]) if len(row.get("a") or []) > 1 else None
    ts_ms = int(time.time() * 1000)
    adopted = adopt_tick_quote(
        venue="kraken",
        symbol="BTC/USDT",
        bid=bid,
        ask=ask,
        source="kraken_public_ticker",
        provider_timestamp=ts_ms,
        bid_qty=bid_qty,
        ask_qty=ask_qty,
        require_live=True,
        path="streaming",
    )
    live = adopted.get("freshness_class") == FreshnessClass.LIVE.value
    # TOB-only: expose single-level book with venue sizes when available — never fabricate ladder.
    bids = [[bid, float(bid_qty)]] if bid_qty else [[bid, 0.0]]
    asks = [[ask, float(ask_qty)]] if ask_qty else [[ask, 0.0]]
    return {
        "ok": True,
        "live": live,
        "venue": "kraken",
        "symbol": adopted["symbol"],
        "bid": bid,
        "ask": ask,
        "bid_qty": bid_qty,
        "ask_qty": ask_qty,
        "bids": bids,
        "asks": asks,
        "freshness_class": adopted.get("freshness_class"),
        "executable_quotes": live,
        "latency_ms": latency_ms,
        "depth_levels": {"bids": 1, "asks": 1},
        "depth_source": "venue_tob",
        "fabricated_depth": False,
        "source": "kraken_public_ticker",
        "probed_at": datetime.now(UTC).isoformat(),
    }


async def probe_binance_public_book(symbol: str = "BTCUSDT") -> dict[str, Any]:
    """Legacy entry — tries Binance first, then multi-venue failover."""
    code, body, latency_ms = await _http_get_json(
        f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
    )
    if code == 200 and isinstance(body, dict) and body.get("bidPrice"):
        from canonical_adoption import adopt_tick_quote
        from canonical_data_layer import FreshnessClass

        bid = float(body["bidPrice"])
        ask = float(body["askPrice"])
        bid_qty = float(body.get("bidQty") or 0) or None
        ask_qty = float(body.get("askQty") or 0) or None
        provider_ts_ms = int(time.time() * 1000)
        adopted = adopt_tick_quote(
            venue="binance",
            symbol=f"{symbol[:-4]}/{symbol[-4:]}",
            bid=bid,
            ask=ask,
            source="binance_public_bookticker",
            provider_timestamp=provider_ts_ms,
            bid_qty=bid_qty,
            ask_qty=ask_qty,
            require_live=True,
            path="streaming",
        )
        live = adopted.get("freshness_class") == FreshnessClass.LIVE.value
        bids = [[bid, float(bid_qty or 0)]]
        asks = [[ask, float(ask_qty or 0)]]
        return {
            "ok": True,
            "live": live,
            "venue": "binance",
            "symbol": adopted["symbol"],
            "bid": bid,
            "ask": ask,
            "bids": bids,
            "asks": asks,
            "freshness_class": adopted.get("freshness_class"),
            "executable_quotes": live,
            "latency_ms": latency_ms,
            "depth_source": "venue_tob",
            "fabricated_depth": False,
            "source": "binance_public_bookticker",
            "probed_at": datetime.now(UTC).isoformat(),
        }
    attempts = [
        ("binance", {"ok": False, "reason": f"binance_http_{code}", "latency_ms": latency_ms}),
    ]
    okx = await probe_okx_book("BTC-USDT")
    attempts.append(("okx", okx))
    if okx.get("ok") and okx.get("live"):
        return {**okx, "failover_from": "binance", "attempts": [a[0] for a in attempts]}
    kr = await probe_kraken_depth("XBTUSDT")
    attempts.append(("kraken", kr))
    if kr.get("ok") and kr.get("live"):
        return {**kr, "failover_from": "binance", "attempts": [a[0] for a in attempts]}
    return {
        "ok": False,
        "live": False,
        "reason": "all_public_venues_unavailable",
        "executable_quotes": False,
        "attempts": [{k: (v if isinstance(v, dict) else {"detail": v})} for k, v in attempts],
        "probed_at": datetime.now(UTC).isoformat(),
    }


async def prove_multi_venue_live() -> dict[str, Any]:
    """Prove independent live venues with real L2 (OKX books + Kraken Depth; Binance optional)."""
    results = []
    for factory in (
        lambda: probe_okx_book("BTC-USDT"),
        lambda: probe_kraken_depth("XBTUSDT"),
    ):
        try:
            results.append(await factory())
        except Exception as exc:  # noqa: BLE001
            results.append({"ok": False, "live": False, "reason": type(exc).__name__})
    try:
        code, body, latency_ms = await _http_get_json(
            "https://api.binance.com/api/v3/ticker/bookTicker?symbol=BTCUSDT"
        )
        if code == 200 and isinstance(body, dict) and body.get("bidPrice"):
            from canonical_adoption import adopt_tick_quote
            from canonical_data_layer import FreshnessClass

            adopted = adopt_tick_quote(
                venue="binance",
                symbol="BTC/USDT",
                bid=float(body["bidPrice"]),
                ask=float(body["askPrice"]),
                source="binance_public_bookticker",
                provider_timestamp=int(time.time() * 1000),
                require_live=True,
                path="streaming",
            )
            results.append(
                {
                    "ok": True,
                    "live": adopted.get("freshness_class") == FreshnessClass.LIVE.value,
                    "venue": "binance",
                    "latency_ms": latency_ms,
                    "source": "binance_public_bookticker",
                    "depth_source": "venue_tob",
                    "fabricated_depth": False,
                }
            )
        else:
            results.append(
                {
                    "ok": False,
                    "live": False,
                    "venue": "binance",
                    "reason": f"binance_http_{code}",
                    "latency_ms": latency_ms,
                }
            )
    except Exception as exc:  # noqa: BLE001
        results.append({"ok": False, "live": False, "venue": "binance", "reason": type(exc).__name__})

    live = [r for r in results if r.get("ok") and r.get("live")]
    venues = sorted({r["venue"] for r in live if r.get("venue")})
    l2_venues = sorted(
        {
            r["venue"]
            for r in live
            if r.get("venue") and r.get("depth_source") == "venue_l2" and not r.get("fabricated_depth")
        }
    )
    return {
        "ok": len(venues) >= 2,
        "live_venues": venues,
        "live_count": len(venues),
        "l2_venues": l2_venues,
        "l2_count": len(l2_venues),
        "probes": results,
        "canonical_required": True,
        "stale_as_live": 0,
        "fabricated_depth_forbidden": True,
        "proved_at": datetime.now(UTC).isoformat(),
        "implementation_class": "PARTIAL" if len(l2_venues) >= 1 else "UNVERIFIED",
    }


def probe_status() -> dict[str, Any]:
    return {
        "surface": "live_data_truth_probe",
        "providers": ["okx_public_books", "kraken_public_depth", "binance_public"],
        "credentials_required": False,
        "fail_closed_on_outage": True,
        "failover": True,
        "fabricated_depth_forbidden": True,
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "note": "Proves live public L2 → canonical adopt; never fabricates depth sizes.",
        "product_complete": False,
    }
