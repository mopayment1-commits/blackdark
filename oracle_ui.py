"""Oracle v2 — server-rendered decision surface helpers."""

from __future__ import annotations

from typing import Any

from fastapi import Request

DEFAULT_FEE_EXCHANGE = "binance"


def wants_oracle_json(request: Request) -> bool:
    """JSON for API clients (default); HTML only for explicit browser navigation."""
    fmt = request.query_params.get("format", "").lower()
    if fmt == "json":
        return True
    if fmt == "html":
        return False
    accept = (request.headers.get("accept") or "").lower().strip()
    if not accept:
        return True
    # Browser document navigation prefers HTML first.
    if accept.startswith("text/html"):
        return False
    if "application/json" in accept:
        return True
    return True


def verdict_tone(verdict: str | None) -> str:
    label = (verdict or "").upper()
    if any(token in label for token in ("BUY", "BULL", "ACT")):
        return "green"
    if any(token in label for token in ("WAIT", "HOLD", "CAUTION")):
        return "yellow"
    if any(token in label for token in ("SELL", "BEAR", "DO NOT", "AVOID", "TOUCH")):
        return "red"
    return "gray"


def _format_usd(value: float | int | None, *, signed: bool = False) -> str:
    if value is None:
        return "—"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "—"
    prefix = "+" if signed and num > 0 else ("-" if signed and num < 0 else "")
    body = f"{abs(num):,.2f}" if abs(num) < 1_000_000 else f"{abs(num):,.0f}"
    return f"{prefix}${body}"


def format_hold_period(payload: dict[str, Any]) -> str:
    half = payload.get("opportunity_half_life") or {}
    seconds = half.get("expected_half_life_seconds") or half.get("remaining_seconds")
    if seconds is None:
        return "—"
    secs = float(seconds)
    if secs < 60:
        return f"{int(secs)}s"
    if secs < 3600:
        return f"{int(secs // 60)}m"
    if secs < 86_400:
        return f"{secs / 3600:.1f}h"
    return f"{secs / 86_400:.1f}d"


def _fee_row_snapshot(row: dict[str, Any], *, mode: str) -> dict[str, Any]:
    return {
        "exchange": row.get("exchange") or DEFAULT_FEE_EXCHANGE,
        "opportunity_id": row.get("opportunity_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "trading_fees_usdt": row.get("trading_fee_usdt"),
        "withdrawal_fee_usdt": row.get("withdrawal_fee_usdt"),
        "deposit_fee_usdt": row.get("deposit_fee_usdt"),
        "gas_fee_usdt": row.get("gas_fee_usdt"),
        "total_fee_usdt": row.get("total_fee_usdt"),
        "net_profit_usdt": row.get("net_profit_usdt"),
        "trading_fee_pct": row.get("trading_fee_pct"),
        "timestamp": row.get("timestamp"),
        "mode": mode,
        "label": "Net after fees (persisted fees table)",
    }


def _fee_unavailable_snapshot(*, symbol: str) -> dict[str, Any]:
    return {
        "exchange": DEFAULT_FEE_EXCHANGE,
        "symbol": symbol,
        "mode": "unavailable",
        "label": "Fee data unavailable — no persisted fees row (fail-closed)",
    }


async def build_fee_snapshot_from_db(asset: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Read fee economics only from the durable `fees` table (no fee_matrix UI bypass)."""
    from database import fetch_fee_record, fetch_latest_fee_for_symbol

    pair = f"{asset.upper()}/USDT"
    exchange = DEFAULT_FEE_EXCHANGE

    fee_record = payload.get("fee_record")
    if isinstance(fee_record, dict) and fee_record.get("total_fee_usdt") is not None:
        return _fee_row_snapshot(fee_record, mode="payload_fee_record")

    for opp_key in ("opportunity_id", "prediction_id"):
        opp_id = payload.get(opp_key)
        if not opp_id:
            continue
        row = await fetch_fee_record(str(opp_id), exchange, pair)
        if row is not None:
            return _fee_row_snapshot(row, mode="persisted_opportunity")

    row = await fetch_latest_fee_for_symbol(exchange, pair)
    if row is not None:
        return _fee_row_snapshot(row, mode="persisted_latest_symbol")

    return _fee_unavailable_snapshot(symbol=pair)


def build_fee_snapshot(asset: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Sync shim — prefer ``build_fee_snapshot_from_db`` in async routes."""
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(build_fee_snapshot_from_db(asset, payload))
    if loop.is_running():
        raise RuntimeError("build_fee_snapshot cannot run inside a running loop; await build_fee_snapshot_from_db")
    return loop.run_until_complete(build_fee_snapshot_from_db(asset, payload))


def _driver_card(key: str, title: str, value: str, detail: str, tone: str = "neutral") -> dict[str, str]:
    return {"key": key, "title": title, "value": value, "detail": detail, "tone": tone}


def build_driver_cards(asset: str, price: float, payload: dict[str, Any]) -> list[dict[str, str]]:
    from bd_platform.derivatives_ta_research_layer import analyze_funding_rate_192, compute_cvd_194

    cards: list[dict[str, str]] = []

    try:
        cvd = compute_cvd_194(asset=asset)
        cvd_usd = float(cvd.get("cvd_usd") or 0)
        tone = "positive" if cvd_usd >= 0 else "negative"
        cards.append(
            _driver_card(
                "cvd",
                "CVD",
                f"${cvd_usd / 1_000_000:+.1f}M" if abs(cvd_usd) >= 1_000_000 else f"${cvd_usd:,.0f}",
                str((cvd.get("insight") or {}).get("en") or "Cumulative volume delta"),
                tone,
            )
        )
    except Exception:
        cards.append(_driver_card("cvd", "CVD", "—", "Volume delta unavailable", "neutral"))

    try:
        funding = analyze_funding_rate_192(asset=asset, spot_price=price)
        annual = funding.get("avg_annualized_pct")
        pressure = "Elevated" if funding.get("bullish_pressure_signal") else "Neutral"
        cards.append(
            _driver_card(
                "funding",
                "Funding",
                f"{annual}% ann." if annual is not None else "—",
                f"Carry pressure: {pressure}",
                "positive" if funding.get("bullish_pressure_signal") else "neutral",
            )
        )
    except Exception:
        cards.append(_driver_card("funding", "Funding", "—", "Funding data unavailable", "neutral"))

    whale_text = str(payload.get("whale_alert") or "").strip()
    expl_whale = ((payload.get("explanation") or {}).get("whale_activity") or {})
    if not whale_text and isinstance(expl_whale, dict):
        whale_text = str(expl_whale.get("summary") or expl_whale.get("headline") or "").strip()
    if not whale_text:
        modal = (payload.get("modal_breakdown") or {}).get("whale") or {}
        adj = modal.get("adjustment")
        if adj is not None:
            whale_text = f"Whale dimension {float(adj):+.2f}"
    cards.append(
        _driver_card(
            "whale",
            "Whale",
            "Active" if whale_text and whale_text != "—" else "Quiet",
            whale_text or "No notable whale signal",
            "positive" if whale_text and "inflow" in whale_text.lower() else "neutral",
        )
    )
    return cards


def certificate_href(payload: dict[str, Any]) -> str | None:
    cert = payload.get("decision_certificate") or {}
    cert_hash = cert.get("certificate_hash")
    prediction_id = payload.get("prediction_id") or cert.get("prediction_id")
    if not cert_hash and not prediction_id:
        return None
    query = []
    if cert_hash:
        query.append(f"cert={str(cert_hash)[:16]}")
    if prediction_id:
        query.append(f"pid={prediction_id}")
    return f"/oracle-accuracy?{'&'.join(query)}"


async def build_oracle_v2_context(
    payload: dict[str, Any],
    *,
    asset: str,
    price: float,
    change: float,
    ux_mode: str,
    lang: str,
) -> dict[str, Any]:
    verdict = str(payload.get("verdict") or payload.get("decision_action") or "WAIT")
    confidence = int(payload.get("confidence") or payload.get("opportunity_score") or 0)
    confidence = max(0, min(100, confidence))
    sentence = (
        payload.get("decision_sentence")
        or payload.get("oracle")
        or payload.get("narrative")
        or payload.get("action")
        or f"{verdict} on {asset}"
    )
    fee = await build_fee_snapshot_from_db(asset, payload)
    return {
        "asset": asset.upper(),
        "price_display": _format_usd(price),
        "change_24h": change,
        "change_display": f"{change:+.2f}%",
        "verdict": verdict,
        "verdict_tone": verdict_tone(verdict),
        "decision_sentence": sentence,
        "confidence": confidence,
        "drivers": build_driver_cards(asset, price, payload),
        "hold_period": format_hold_period(payload),
        "risk_level": str(payload.get("risk_level") or "—"),
        "fee": fee,
        "fee_total_display": _format_usd(fee.get("total_fee_usdt")),
        "net_profit_display": _format_usd(fee.get("net_profit_usdt"), signed=True)
        if fee.get("net_profit_usdt") is not None
        else None,
        "certificate_href": certificate_href(payload),
        "prediction_id": payload.get("prediction_id"),
        "ux_mode": ux_mode,
        "lang": lang,
        "opportunity_score": payload.get("opportunity_score"),
        "timestamp_human": payload.get("timestamp_human"),
    }
