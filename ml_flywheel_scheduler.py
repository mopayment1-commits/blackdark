"""
BLACKDARK — Background ML flywheel scheduler.

Runs labeling → export → optional baseline training on a fixed interval.
"""

from __future__ import annotations

import asyncio
import logging

import config

logger = logging.getLogger("BLACKDARK.MLFlywheel")

_flywheel_task: asyncio.Task | None = None
_running = False


async def _flywheel_loop() -> None:
    interval = max(300, int(config.ML_FLYWHEEL_INTERVAL_SEC))
    while _running:
        try:
            from ml.labeling_pipeline import run_labeling_flywheel_cycle

            result = await run_labeling_flywheel_cycle()
            logger.info(
                "ML flywheel cycle | resolved=%s exported=%s trained=%s",
                (result.get("labeling") or {}).get("resolved_24h"),
                (result.get("export") or {}).get("exported"),
                (result.get("training") or {}).get("trained"),
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("ML flywheel cycle failed.")
        await asyncio.sleep(interval)


async def start_ml_flywheel() -> None:
    global _running, _flywheel_task
    if _running or not config.ML_FLYWHEEL_ENABLED:
        return
    _running = True
    _flywheel_task = asyncio.create_task(_flywheel_loop(), name="ml-flywheel")
    logger.info("ML flywheel scheduler started | interval=%ss", config.ML_FLYWHEEL_INTERVAL_SEC)


async def stop_ml_flywheel() -> None:
    global _running, _flywheel_task
    _running = False
    if _flywheel_task is not None:
        _flywheel_task.cancel()
        await asyncio.gather(_flywheel_task, return_exceptions=True)
        _flywheel_task = None
    logger.info("ML flywheel scheduler stopped.")


def flywheel_running() -> bool:
    return _running
