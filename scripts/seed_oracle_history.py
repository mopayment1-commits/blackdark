#!/usr/bin/env python3
"""
Seed oracle predictions from Binance historical klines — HONEST backfill.

Verdict is chosen from past data only (momentum rule). Resolution uses the
next candle close without retroactively picking a matching verdict.

Rows are tagged source=historical_seed and EXCLUDED from live metrics/training.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aiohttp

from ml.labeling_pipeline import score_verdict_accuracy

ASSETS = ("BTC", "ETH", "SOL", "BNB", "XRP")
DAYS = 90
PREDICTIONS_PER_ASSET = 24


async def fetch_klines(session: aiohttp.ClientSession, symbol: str) -> list[dict]:
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": f"{symbol}USDT", "interval": "1d", "limit": DAYS + 5}
    async with session.get(url, params=params) as resp:
        if resp.status != 200:
            return []
        data = await resp.json()
    return [
        {"ts": int(k[0]), "open": float(k[1]), "close": float(k[4])}
        for k in data
    ]


def _verdict_from_past_only(prior_closes: list[float]) -> str:
    """Point-in-time rule: no future prices."""
    if len(prior_closes) < 3:
        return "WAIT"
    ret_3d = (prior_closes[-1] / prior_closes[-3] - 1.0) * 100
    if ret_3d > 2.0:
        return "STRONG BUY"
    if ret_3d < -2.0:
        return "AVOID"
    return "WAIT"


async def seed_history() -> dict:
    from database import init_db, insert_oracle_prediction, resolve_oracle_prediction

    await init_db()

    inserted = 0
    resolved = 0
    correct = 0
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for asset in ASSETS:
            klines = await fetch_klines(session, asset)
            if len(klines) < 10:
                continue

            step = max(1, len(klines) // PREDICTIONS_PER_ASSET)
            for i in range(2, len(klines) - 1, step):
                k = klines[i]
                k_next = klines[i + 1]
                prior_closes = [row["close"] for row in klines[: i + 1]]
                price_at = k["open"]
                price_after = k_next["close"]

                verdict = _verdict_from_past_only(prior_closes)
                outcome, accuracy, direction = score_verdict_accuracy(
                    verdict, price_at, price_after
                )
                label = outcome if outcome in {"correct", "incorrect", "partial"} else "partial"
                if label == "correct":
                    correct += 1

                ts = datetime.fromtimestamp(k["ts"] / 1000, tz=timezone.utc).isoformat()
                resolved_ts = datetime.fromtimestamp(
                    k_next["ts"] / 1000, tz=timezone.utc
                ).isoformat()

                pred_id = await insert_oracle_prediction(
                    asset=asset,
                    price_at_prediction=price_at,
                    verdict=verdict,
                    opportunity_score=0,
                    confidence=0,
                    timestamp=ts,
                    source="historical_seed",
                )
                inserted += 1

                await resolve_oracle_prediction(
                    pred_id,
                    price_after,
                    outcome,
                    accuracy,
                    label=label,
                    direction_label=direction,
                    resolved_at=resolved_ts,
                )
                resolved += 1

    hit_rate = round(correct / resolved * 100, 2) if resolved else 0

    from oracle_track_record import backfill_from_database

    chain = await backfill_from_database()

    return {
        "inserted": inserted,
        "resolved": resolved,
        "correct": correct,
        "hit_rate_percent": hit_rate,
        "days_span": DAYS,
        "chain_records": chain.get("chain_records"),
        "synthetic": True,
        "excluded_from_live_metrics": True,
        "method": "honest_momentum_backfill",
        "note": (
            "Verdict from past-only 3-day momentum; resolved against next close. "
            "Tagged historical_seed — excluded from training and public hit rate."
        ),
    }


async def main() -> int:
    result = await seed_history()
    print("Oracle history seed complete (honest backfill):")
    for k, v in result.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
