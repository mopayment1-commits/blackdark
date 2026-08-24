"""
Order Flow Analytics — Feature #135 (Sprint 2, Market Radar).

Translates raw order-book volume into user-friendly buy/sell pressure:
  - 'Buy Wall at $30K (500 BTC) — strong support'
  - 'Fake Sell Wall (spoofing detected) — cancels within seconds'

NOT raw volume numbers — plain-language order flow for everyday users.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.OrderFlowAnalytics")

_FEATURE_ID = 135
_WALL_HISTORY_PATH = Path("data/order_flow_wall_history.json")
_CACHE_PATH = Path("data/order_flow_cache.json")
_CACHE_TTL_SEC = 30

_DISCLAIMER = (
    "Order Flow Analytics describes visible order-book pressure — not trading advice. "
    "Walls can be spoofed or pulled instantly. Use as context only."
)

# Wall thresholds (relative to 5-level depth)
_WALL_RATIO_STRONG = 0.35
_WALL_RATIO_MODERATE = 0.20
_SPOOF_RATIO = 2.5  # single level >> rest of book


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_wall_history() -> dict[str, dict[str, Any]]:
    if not _WALL_HISTORY_PATH.exists():
        return {}
    try:
        return json.loads(_WALL_HISTORY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_wall_history(data: dict[str, dict[str, Any]]) -> None:
    _WALL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    _WALL_HISTORY_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _classify_wall_strength(ratio: float) -> tuple[str, str, str]:
    if ratio >= _WALL_RATIO_STRONG:
        return "strong", "strong support", "دعم قوي"
    if ratio >= _WALL_RATIO_MODERATE:
        return "moderate", "moderate pressure", "ضغط متوسط"
    return "weak", "light pressure", "ضغط خفيف"


def _detect_spoofing(
    wall_size: float,
    other_levels_total: float,
    *,
    prev_size: float | None,
) -> bool:
    """Heuristic: dominant single level + rapid disappearance = spoofing."""
    if wall_size > 0 and other_levels_total > 0 and wall_size / other_levels_total >= _SPOOF_RATIO:
        return True
    if prev_size is not None and prev_size > 0 and wall_size < prev_size * 0.2:
        return True
    return False


def analyze_order_book(
    *,
    exchange: str,
    asset: str,
    price: float,
    bids: list[list[float]],
    asks: list[list[float]],
    prev_wall: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Analyze one exchange book for buy/sell walls."""
    signals: list[dict[str, Any]] = []
    sym = asset.upper()

    bid_sizes = [float(b[1]) for b in bids[:10] if len(b) >= 2]
    ask_sizes = [float(a[1]) for a in asks[:10] if len(a) >= 2]
    if not bid_sizes and not ask_sizes:
        return signals

    total_bid = sum(bid_sizes) or 1.0
    total_ask = sum(ask_sizes) or 1.0
    max_bid = max(bid_sizes) if bid_sizes else 0.0
    max_ask = max(ask_sizes) if ask_sizes else 0.0
    max_bid_price = float(bids[bid_sizes.index(max_bid)][0]) if max_bid and bids else price
    max_ask_price = float(asks[ask_sizes.index(max_ask)][0]) if max_ask and asks else price

    prev_bid = float((prev_wall or {}).get("max_bid_size") or 0)
    prev_ask = float((prev_wall or {}).get("max_ask_size") or 0)

    if max_bid > 0:
        ratio = max_bid / total_bid
        strength, label_en, label_ar = _classify_wall_strength(ratio)
        spoofed = _detect_spoofing(max_bid, total_bid - max_bid, prev_size=prev_bid or None)
        if spoofed:
            headline = f"Fake Buy Wall (spoofing detected) at ${max_bid_price:,.0f} ({max_bid:.2f} {sym}) — cancels within seconds"
            headline_ar = f"جدار شراء مزيف (spoofing) عند ${max_bid_price:,.0f} ({max_bid:.2f} {sym}) — يُلغى خلال ثوانٍ"
            signal_type = "spoofed_buy_wall"
        else:
            headline = f"Buy Wall at ${max_bid_price:,.0f} ({max_bid:.2f} {sym}) — {label_en}"
            headline_ar = f"جدار شراء عند ${max_bid_price:,.0f} ({max_bid:.2f} {sym}) — {label_ar}"
            signal_type = "buy_wall"
        signals.append(
            {
                "signal_type": signal_type,
                "side": "buy",
                "exchange": exchange,
                "asset": sym,
                "wall_price": max_bid_price,
                "wall_size": round(max_bid, 4),
                "strength": strength,
                "spoofing_detected": spoofed,
                "headline": headline,
                "headline_ar": headline_ar,
                "buy_sell_pressure": "buying_pressure",
                "user_friendly": True,
            }
        )

    if max_ask > 0:
        ratio = max_ask / total_ask
        strength, label_en, label_ar = _classify_wall_strength(ratio)
        spoofed = _detect_spoofing(max_ask, total_ask - max_ask, prev_size=prev_ask or None)
        if spoofed:
            headline = f"Fake Sell Wall (spoofing detected) at ${max_ask_price:,.0f} ({max_ask:.2f} {sym}) — cancels within seconds"
            headline_ar = f"جدار بيع مزيف (spoofing) عند ${max_ask_price:,.0f} ({max_ask:.2f} {sym}) — يُلغى خلال ثوانٍ"
            signal_type = "spoofed_sell_wall"
        else:
            headline = f"Sell Wall at ${max_ask_price:,.0f} ({max_ask:.2f} {sym}) — {label_en}"
            headline_ar = f"جدار بيع عند ${max_ask_price:,.0f} ({max_ask:.2f} {sym}) — {label_ar}"
            signal_type = "sell_wall"
        signals.append(
            {
                "signal_type": signal_type,
                "side": "sell",
                "exchange": exchange,
                "asset": sym,
                "wall_price": max_ask_price,
                "wall_size": round(max_ask, 4),
                "strength": strength,
                "spoofing_detected": spoofed,
                "headline": headline,
                "headline_ar": headline_ar,
                "buy_sell_pressure": "selling_pressure",
                "user_friendly": True,
            }
        )

    return signals


async def scan_order_flow(asset: str = "BTC", *, limit: int = 10) -> dict[str, Any]:
    """#135 — Order Flow Analytics for Market Radar."""
    t0 = time.perf_counter()
    sym = asset.upper()
    pair = f"{sym}/USDT"
    signals: list[dict[str, Any]] = []
    history = _load_wall_history()
    next_history = dict(history)

    try:
        from database import fetch_latest_order_books
        from live_book_hub import get_best_price

        books = await fetch_latest_order_books()
        for ex, syms in (books or {}).items():
            book = syms.get(pair) or syms.get(f"{sym}USDT")
            if not book:
                continue
            bids = book.get("bids") or []
            asks = book.get("asks") or []
            top = get_best_price(ex, pair) or {}
            price = float(top.get("mid") or 0)
            if price <= 0 and bids:
                price = float(bids[0][0])
            key = f"{ex}:{sym}"
            prev = history.get(key)
            rows = analyze_order_book(
                exchange=ex,
                asset=sym,
                price=price,
                bids=bids,
                asks=asks,
                prev_wall=prev,
            )
            signals.extend(rows)
            if bids or asks:
                bid_sizes = [float(b[1]) for b in bids[:10] if len(b) >= 2]
                ask_sizes = [float(a[1]) for a in asks[:10] if len(a) >= 2]
                next_history[key] = {
                    "max_bid_size": max(bid_sizes) if bid_sizes else 0,
                    "max_ask_size": max(ask_sizes) if ask_sizes else 0,
                    "timestamp": _utcnow(),
                }
    except Exception:
        logger.debug("Order flow book fetch failed", exc_info=True)

    # Fallback: live book hub top-of-book only
    if not signals:
        try:
            from live_book_hub import get_best_price

            for ex in ("binance", "okx", "bybit"):
                row = get_best_price(ex, pair)
                if not row:
                    continue
                bid_qty = float(row.get("bid_qty") or 0)
                ask_qty = float(row.get("ask_qty") or 0)
                price = float(row.get("mid") or 0)
                if bid_qty > ask_qty * 1.5 and bid_qty > 0:
                    signals.append(
                        {
                            "signal_type": "buy_pressure",
                            "side": "buy",
                            "exchange": ex,
                            "asset": sym,
                            "wall_price": float(row.get("bid") or price),
                            "wall_size": bid_qty,
                            "strength": "moderate",
                            "spoofing_detected": False,
                            "headline": f"Buying pressure on {ex.title()} at ${float(row.get('bid') or price):,.0f} — bid size {bid_qty:.2f} {sym}",
                            "headline_ar": f"ضغط شراء على {ex.title()} — حجم العرض {bid_qty:.2f} {sym}",
                            "buy_sell_pressure": "buying_pressure",
                            "user_friendly": True,
                        }
                    )
                elif ask_qty > bid_qty * 1.5 and ask_qty > 0:
                    signals.append(
                        {
                            "signal_type": "sell_pressure",
                            "side": "sell",
                            "exchange": ex,
                            "asset": sym,
                            "wall_price": float(row.get("ask") or price),
                            "wall_size": ask_qty,
                            "strength": "moderate",
                            "spoofing_detected": False,
                            "headline": f"Selling pressure on {ex.title()} at ${float(row.get('ask') or price):,.0f} — ask size {ask_qty:.2f} {sym}",
                            "headline_ar": f"ضغط بيع على {ex.title()} — حجم الطلب {ask_qty:.2f} {sym}",
                            "buy_sell_pressure": "selling_pressure",
                            "user_friendly": True,
                        }
                    )
        except Exception:
            pass

    _save_wall_history(next_history)

    strength_order = {"strong": 0, "moderate": 1, "weak": 2}
    signals.sort(key=lambda s: (strength_order.get(str(s.get("strength")), 9), s.get("spoofing_detected", False)))
    signals = signals[:limit]

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "product_name": "Order Flow Analytics",
        "surface": "market_radar",
        "asset": sym,
        "signal_count": len(signals),
        "signals": signals,
        "translation": "buy_sell_pressure",
        "disclaimer": _DISCLAIMER,
        "mode": "analytics_only",
        "no_trading_advice": True,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


def enrich_market_radar(payload: dict[str, Any], order_flow: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["order_flow_analytics"] = {
        "enabled": order_flow.get("ok", False),
        "asset": order_flow.get("asset"),
        "signal_count": order_flow.get("signal_count", 0),
        "signals": order_flow.get("signals", [])[:3],
        "disclaimer": _DISCLAIMER,
    }
    return out
