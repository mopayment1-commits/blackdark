"""Sealed Prediction Market — Oracle Act/Wait contracts."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sealed_market_store import (
    MAX_BET_USDT,
    PLATFORM_FEE_RATE,
    adjust_user_balance,
    fetch_market_by_prediction,
    get_user_balance,
    insert_bet,
    insert_market,
    list_bets_for_market,
    list_markets,
    list_open_bets,
    update_bet,
    update_market,
)

logger = logging.getLogger("BLACKDARK.SealedMarket")

BETTING_WINDOW_HOURS = 24


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


def _map_decision_action(verdict: str) -> str:
    from supplemental_public_compliance import map_public_decision_action

    raw = (verdict or "").strip().upper()
    action = map_public_decision_action(raw)
    if action in {"ACT", "WAIT", "I_DONT_KNOW", "CONDITIONS MET"}:
        return action.replace(" ", "_")
    if "WAIT" in raw or "HOLD" in raw:
        return "WAIT"
    return "ACT"


def build_certificate_hash(
    *,
    prediction_id: int,
    asset: str,
    verdict: str,
    price_at_prediction: float,
    sealed_at: str,
) -> str:
    body = {
        "prediction_id": prediction_id,
        "asset": asset.upper(),
        "verdict": verdict.upper(),
        "price_at_prediction": price_at_prediction,
        "sealed_at": sealed_at,
        "engine": "oracle_sealed_market_v1",
    }
    raw = json.dumps(body, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


async def on_oracle_prediction_sealed(
    prediction_id: int,
    *,
    asset: str,
    verdict: str,
    price_at_prediction: float,
    timestamp: str | None = None,
) -> dict[str, Any] | None:
    if prediction_id <= 0:
        return None
    existing = await fetch_market_by_prediction(prediction_id)
    if existing:
        return existing
    sealed_at = timestamp or _utcnow().isoformat()
    closes = (_parse_dt(sealed_at) or _utcnow()) + timedelta(hours=BETTING_WINDOW_HOURS)
    cert_hash = build_certificate_hash(
        prediction_id=prediction_id,
        asset=asset,
        verdict=verdict,
        price_at_prediction=price_at_prediction,
        sealed_at=sealed_at,
    )
    market_id = await insert_market(
        {
            "prediction_id": prediction_id,
            "asset": asset.upper(),
            "decision_action": _map_decision_action(verdict),
            "verdict_raw": verdict.upper(),
            "certificate_hash": cert_hash,
            "sealed_at": sealed_at,
            "betting_closes_at": closes.isoformat(),
            "status": "open",
        }
    )
    return await fetch_market_by_prediction(prediction_id)


async def ensure_market_for_prediction(prediction_id: int) -> dict[str, Any] | None:
    from database import fetch_oracle_prediction_public_row

    market = await fetch_market_by_prediction(prediction_id)
    if market:
        return market
    row = await fetch_oracle_prediction_public_row(prediction_id)
    if not row or row.get("resolved"):
        return None
    return await on_oracle_prediction_sealed(
        prediction_id,
        asset=str(row.get("asset") or ""),
        verdict=str(row.get("verdict") or "WAIT"),
        price_at_prediction=float(row.get("price_at_prediction") or 0),
        timestamp=str(row.get("timestamp") or ""),
    )


def _market_public_view(market: dict[str, Any], *, include_hash: bool = True) -> dict[str, Any]:
    closes = _parse_dt(str(market.get("betting_closes_at") or ""))
    now = _utcnow()
    betting_open = (
        market.get("status") == "open"
        and closes is not None
        and now < closes
    )
    out = {
        "market_id": market.get("id"),
        "prediction_id": market.get("prediction_id"),
        "asset": market.get("asset"),
        "decision_action": market.get("decision_action"),
        "status": market.get("status"),
        "sealed_at": market.get("sealed_at"),
        "betting_closes_at": market.get("betting_closes_at"),
        "betting_open": betting_open,
        "total_pool_usdt": round(float(market.get("total_pool_usdt") or 0), 4),
        "yes_pool_usdt": round(float(market.get("yes_pool_usdt") or 0), 4),
        "no_pool_usdt": round(float(market.get("no_pool_usdt") or 0), 4),
        "participant_count": int(market.get("participant_count") or 0),
        "outcome_label": market.get("outcome_label"),
        "platform_fee_usdt": market.get("platform_fee_usdt"),
        "settled_at": market.get("settled_at"),
        "max_bet_usdt": MAX_BET_USDT,
        "platform_fee_rate": PLATFORM_FEE_RATE,
    }
    if include_hash:
        out["certificate_hash"] = market.get("certificate_hash")
    return out


async def backfill_open_markets(limit: int = 15) -> int:
    from database import fetch_unresolved_oracle_predictions

    created = 0
    for row in await fetch_unresolved_oracle_predictions(limit=limit):
        pid = int(row.get("id") or 0)
        if pid and await ensure_market_for_prediction(pid):
            created += 1
    return created


async def public_markets_payload(limit: int = 40) -> dict[str, Any]:
    try:
        await backfill_open_markets()
    except Exception:
        logger.exception("Sealed market backfill skipped")
    rows = await list_markets(limit=limit)
    active = []
    closed = []
    for m in rows:
        view = _market_public_view(m)
        if m.get("status") == "open" and view.get("betting_open"):
            active.append(view)
        else:
            closed.append(view)
    return {"active": active, "settled": closed, "fee_rate": PLATFORM_FEE_RATE}


async def market_detail(prediction_id: int) -> dict[str, Any] | None:
    market = await ensure_market_for_prediction(prediction_id)
    if not market:
        market = await fetch_market_by_prediction(prediction_id)
    if not market:
        return None
    from database import fetch_oracle_prediction_public_row

    pred = await fetch_oracle_prediction_public_row(prediction_id)
    view = _market_public_view(market)
    view["prediction"] = {
        "resolved": bool(pred and pred.get("resolved")),
        "label": pred.get("label") if pred else None,
        "accuracy_score": pred.get("accuracy_score") if pred else None,
        "price_at_prediction": pred.get("price_at_prediction") if pred else None,
        "price_after_24h": pred.get("price_after_24h") if pred else None,
        "timestamp": pred.get("timestamp") if pred else None,
        "resolved_at": pred.get("resolved_at") if pred else None,
    }
    return view


async def place_market_bet(
    *,
    user_id: int,
    prediction_id: int,
    side: str,
    stake_usdt: float,
    funding: str = "internal",
) -> dict[str, Any]:
    side_norm = side.strip().lower()
    if side_norm not in {"yes", "no"}:
        raise ValueError("side must be yes (decision correct) or no (decision wrong)")
    stake = float(stake_usdt)
    if stake <= 0 or stake > MAX_BET_USDT:
        raise ValueError(f"Stake must be >0 and ≤ {MAX_BET_USDT} USDT equivalent")
    funding_norm = funding.strip().lower()
    if funding_norm not in {"internal", "usdt"}:
        raise ValueError("funding must be internal or usdt (ledger credits)")

    market = await ensure_market_for_prediction(prediction_id)
    if not market:
        raise ValueError("No sealed market for this prediction")
    view = _market_public_view(market)
    if not view.get("betting_open"):
        raise ValueError("Betting window closed (24h elapsed or market settled)")

    bal = await get_user_balance(user_id)
    if bal < stake:
        raise ValueError("Insufficient internal market balance")

    await adjust_user_balance(user_id, -stake)
    bet_id = await insert_bet(
        {
            "market_id": int(market["id"]),
            "user_id": user_id,
            "side": side_norm,
            "stake_usdt": stake,
            "funding": funding_norm,
        }
    )
    yes_pool = float(market.get("yes_pool_usdt") or 0) + (stake if side_norm == "yes" else 0)
    no_pool = float(market.get("no_pool_usdt") or 0) + (stake if side_norm == "no" else 0)
    total = float(market.get("total_pool_usdt") or 0) + stake
    participants = int(market.get("participant_count") or 0) + 1
    await update_market(
        int(market["id"]),
        total_pool_usdt=total,
        yes_pool_usdt=yes_pool,
        no_pool_usdt=no_pool,
        participant_count=participants,
    )
    return {
        "bet_id": bet_id,
        "stake_usdt": stake,
        "side": side_norm,
        "balance_usdt": await get_user_balance(user_id),
    }


async def settle_market_for_prediction(prediction_id: int, *, label: str | None) -> dict[str, Any] | None:
    market = await fetch_market_by_prediction(prediction_id)
    if not market or market.get("status") == "settled":
        return None
    lbl = str(label or "").lower()
    winning_side = "yes" if lbl == "correct" else "no"
    losing_pool = float(market.get("no_pool_usdt") or 0) if winning_side == "yes" else float(
        market.get("yes_pool_usdt") or 0
    )
    winning_pool = float(market.get("yes_pool_usdt") or 0) if winning_side == "yes" else float(
        market.get("no_pool_usdt") or 0
    )
    fee = round(losing_pool * PLATFORM_FEE_RATE, 8)
    distributable = max(0.0, losing_pool - fee)

    bets = await list_open_bets(int(market["id"]))
    winners = [b for b in bets if b.get("side") == winning_side]
    losers = [b for b in bets if b.get("side") != winning_side]

    win_stake_total = sum(float(b.get("stake_usdt") or 0) for b in winners)
    for bet in losers:
        await update_bet(int(bet["id"]), status="lost", payout_usdt=0.0)

    for bet in winners:
        stake = float(bet.get("stake_usdt") or 0)
        share = (stake / win_stake_total) if win_stake_total > 0 else 0.0
        payout = round(stake + distributable * share, 8)
        await update_bet(int(bet["id"]), status="won", payout_usdt=payout)
        await adjust_user_balance(int(bet["user_id"]), payout)

    await update_market(
        int(market["id"]),
        status="settled",
        outcome_label=lbl or "unknown",
        platform_fee_usdt=fee,
        settled_at=_utcnow().isoformat(),
    )
    return {
        "prediction_id": prediction_id,
        "winning_side": winning_side,
        "platform_fee_usdt": fee,
        "winners": len(winners),
        "losers": len(losers),
    }


async def on_oracle_prediction_resolved_market(
    prediction_id: int,
    *,
    label: str | None,
) -> None:
    try:
        await settle_market_for_prediction(prediction_id, label=label)
    except Exception:
        logger.exception("Sealed market settlement failed prediction_id=%s", prediction_id)
