"""Oracle v2 — server-rendered decision surface helpers."""

from __future__ import annotations

from typing import Any

from fastapi import Request

DEFAULT_FEE_EXCHANGE = "binance"
REFERENCE_NOTIONAL_USDT = 10_000.0


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


def build_fee_snapshot(asset: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Estimate round-trip fees via fee_matrix (net after fees on reference notional)."""
    from fee_matrix import taker_fee, trading_fees_usdt, withdrawal_fee_usdt

    exchange = DEFAULT_FEE_EXCHANGE
    notional = REFERENCE_NOTIONAL_USDT
    truth = payload.get("net_edge_truth") or {}
    if truth.get("net_profit_usdt") is not None:
        return {
            "exchange": exchange,
            "notional_usdt": notional,
            "trading_fees_usdt": truth.get("trading_fees_usdt"),
            "withdrawal_fee_usdt": truth.get("withdrawal_fee_usdt"),
            "total_fee_usdt": truth.get("total_fees_usdt") or truth.get("total_fee_usdt"),
            "net_profit_usdt": truth.get("net_profit_usdt"),
            "mode": str(truth.get("mode") or "truth"),
            "label": "Net after fees (truth layer)",
        }

    rate = taker_fee(exchange)
    leg_fee = trading_fees_usdt(exchange, notional)
    withdrawal = withdrawal_fee_usdt(exchange, asset)
    if rate is None or leg_fee is None:
        return {
            "exchange": exchange,
            "notional_usdt": notional,
            "mode": "unavailable",
            "label": "Fee data unavailable (fail-closed)",
        }
    round_trip_trading = float(leg_fee) * 2.0
    withdrawal_f = float(withdrawal) if withdrawal is not None else None
    total_fee = round_trip_trading + (withdrawal_f or 0.0)
    return {
        "exchange": exchange,
        "notional_usdt": notional,
        "taker_rate_pct": round(float(rate) * 100, 4),
        "trading_fees_usdt": round(round_trip_trading, 4),
        "withdrawal_fee_usdt": withdrawal_f,
        "total_fee_usdt": round(total_fee, 4),
        "net_profit_usdt": None,
        "mode": "estimated_round_trip",
        "label": f"Est. round-trip fees on {_format_usd(notional)} notional",
    }


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


def build_oracle_v2_context(
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
    fee = build_fee_snapshot(asset, payload)
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
