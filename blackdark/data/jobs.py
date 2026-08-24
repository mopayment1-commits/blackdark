"""APScheduler background jobs for Wave 01 data engine."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from blackdark.data.db import data_engine_available, get_session
from blackdark.data.ingestors.binance import ingest_funding, ingest_ohlcv
from blackdark.data.ingestors.coingecko import ingest_markets

logger = logging.getLogger("BLACKDARK.DataEngine.Jobs")

_scheduler: AsyncIOScheduler | None = None
_started = False


def _enabled() -> bool:
    return os.getenv("DATA_ENGINE_ENABLED", "true").lower() in {"1", "true", "yes"}


async def _run_with_session(coro_factory) -> None:
    async with get_session() as session:
        await coro_factory(session)


async def job_binance_ohlcv_1m() -> None:
    await _run_with_session(
        lambda s: ingest_ohlcv(s, intervals=["1m"], limit=500, triggered_by="job:binance_ohlcv_1m")
    )


async def job_binance_ohlcv_1h() -> None:
    await _run_with_session(
        lambda s: ingest_ohlcv(s, intervals=["1h"], limit=500, triggered_by="job:binance_ohlcv_1h")
    )


async def job_binance_funding() -> None:
    await _run_with_session(lambda s: ingest_funding(s, triggered_by="job:binance_funding"))


async def job_coingecko_market() -> None:
    await _run_with_session(lambda s: ingest_markets(s, triggered_by="job:coingecko_market"))


async def run_bootstrap_ingest_once() -> dict[str, Any]:
    """One-shot ingest when the database has no OHLCV rows (startup bootstrap)."""
    if not _enabled() or not data_engine_available():
        return {"ok": False, "reason": "disabled_or_no_postgres"}
    logger.info("Wave 01 bootstrap ingest starting")
    try:
        async with get_session() as session:
            ohlcv = await ingest_ohlcv(
                session,
                symbols=["BTCUSDT"],
                intervals=["1h"],
                limit=24,
                triggered_by="bootstrap:startup",
            )
            funding = await ingest_funding(
                session,
                symbols=["BTCUSDT"],
                triggered_by="bootstrap:startup",
            )
            markets = await ingest_markets(session, triggered_by="bootstrap:startup")
        result = {
            "ok": True,
            "ohlcv_inserted": int(ohlcv.get("records_inserted", 0)),
            "funding_inserted": int(funding.get("records_inserted", 0)),
            "markets_inserted": int(markets.get("records_inserted", 0)),
        }
        logger.info("Wave 01 bootstrap ingest complete | %s", result)
        return result
    except Exception as exc:
        logger.exception("Wave 01 bootstrap ingest failed")
        return {"ok": False, "error": str(exc)}


async def bootstrap_data_engine() -> dict[str, Any]:
    if not _enabled() or not data_engine_available():
        return {"ok": False, "reason": "disabled_or_no_postgres"}
    from blackdark.data.db import ensure_data_engine_ready

    await ensure_data_engine_ready()
    return {"ok": True, "bootstrapped": True}


def start_data_engine_jobs(loop: asyncio.AbstractEventLoop | None = None) -> dict[str, Any]:
    global _scheduler, _started
    if _started or not _enabled() or not data_engine_available():
        return {"started": False}
    _scheduler = AsyncIOScheduler(event_loop=loop or asyncio.get_event_loop())
    _scheduler.add_job(
        job_binance_ohlcv_1m,
        IntervalTrigger(minutes=1),
        id="binance_ohlcv_1m",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        job_binance_ohlcv_1h,
        CronTrigger(minute=0),
        id="binance_ohlcv_1h",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        job_binance_funding,
        CronTrigger(hour="*/8", minute=5),
        id="binance_funding",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.add_job(
        job_coingecko_market,
        IntervalTrigger(minutes=5),
        id="coingecko_market",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    _started = True
    logger.info("Wave 01 data engine scheduler started")
    return {"started": True, "jobs": [j.id for j in _scheduler.get_jobs()]}


def stop_data_engine_jobs() -> None:
    global _scheduler, _started
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
    _started = False
