"""
BLACKDARK — Ingestion Scheduler (Celery/Airflow-style pattern, asyncio-native).

Schedules category pulls into the data lake:
  prices/news → frequent | macro/events/research → slower

WebSocket live ticks remain in aggregator + hot_spool (Point 38).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

import config
from data_lake import maintenance_prune
from data_sources_registry import CATEGORY_INTERVALS, Category
from ingestion_fetchers import ingest_all_categories, ingest_category

logger = logging.getLogger("BLACKDARK.IngestionScheduler")

_scheduler_task: asyncio.Task | None = None
_category_tasks: dict[Category, asyncio.Task] = {}
_running = False


async def _category_loop(category: Category) -> None:
    interval = CATEGORY_INTERVALS.get(category, 300)
    logger.info("Ingestion loop started | category=%s interval=%ss", category, interval)
    timeout = aiohttp.ClientTimeout(total=config.INGESTION_FETCH_TIMEOUT_SECONDS)

    while _running:
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                stats = await ingest_category(session, category)
            logger.info(
                "Ingestion cycle complete | category=%s ok=%s fail=%s skip=%s",
                category,
                stats.get("ok"),
                stats.get("fail"),
                stats.get("skip"),
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Ingestion category loop failed | category=%s", category)
        await asyncio.sleep(interval)


async def _maintenance_loop() -> None:
    while _running:
        try:
            deleted = await maintenance_prune()
            if deleted:
                logger.info("Data lake pruned | rows_deleted=%s", deleted)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Data lake maintenance failed.")
        await asyncio.sleep(config.INGESTION_MAINTENANCE_INTERVAL_SECONDS)


async def run_initial_bootstrap() -> dict[str, Any]:
    """One-shot full ingest on startup so oracle has lake data immediately."""
    from database import init_db

    await init_db()
    logger.info("Ingestion bootstrap — pulling all registered sources...")
    return await ingest_all_categories()


async def start_ingestion_scheduler(*, bootstrap: bool = True) -> None:
    global _running, _scheduler_task, _category_tasks
    if _running:
        return
    _running = True

    if bootstrap:
        try:
            await run_initial_bootstrap()
        except Exception:
            logger.exception("Ingestion bootstrap failed.")

    for category in CATEGORY_INTERVALS:
        _category_tasks[category] = asyncio.create_task(
            _category_loop(category),
            name=f"ingestion-{category}",
        )

    _scheduler_task = asyncio.create_task(_maintenance_loop(), name="ingestion-maintenance")

    from binance_ws_ingest import start_binance_ws_ingest

    await start_binance_ws_ingest()

    logger.info(
        "Ingestion scheduler started | categories=%s",
        len(CATEGORY_INTERVALS),
    )


async def stop_ingestion_scheduler() -> None:
    global _running, _scheduler_task, _category_tasks
    _running = False

    from binance_ws_ingest import stop_binance_ws_ingest

    await stop_binance_ws_ingest()

    for task in list(_category_tasks.values()):
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    _category_tasks.clear()

    if _scheduler_task is not None:
        _scheduler_task.cancel()
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass
        _scheduler_task = None

    logger.info("Ingestion scheduler stopped.")


def scheduler_running() -> bool:
    return _running
