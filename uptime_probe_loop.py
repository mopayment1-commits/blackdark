"""
BLACKDARK — Self uptime probe loop (DD requirement #1).

Records liveness probes every 60s so uptime_probes.jsonl accumulates even before
UptimeRobot is configured. External monitoring still required for enterprise DD.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time

logger = logging.getLogger("BLACKDARK.UptimeProbeLoop")

_task: asyncio.Task | None = None


def _enabled() -> bool:
    return os.getenv("UPTIME_SELF_PROBE_ENABLED", "true").lower() in {"1", "true", "yes"}


async def _loop() -> None:
    from uptime_monitor import record_probe

    interval = max(30, int(os.getenv("UPTIME_SELF_PROBE_INTERVAL_SEC", "60")))
    logger.info("Uptime self-probe loop started | interval=%ss", interval)
    while True:
        t0 = time.perf_counter()
        try:
            record_probe(
                ok=True,
                source="self_probe",
                latency_ms=(time.perf_counter() - t0) * 1000,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("Self uptime probe record failed", exc_info=True)
        await asyncio.sleep(interval)


def start_uptime_probe_loop() -> asyncio.Task | None:
    global _task
    if not _enabled():
        logger.info("Uptime self-probe loop disabled (UPTIME_SELF_PROBE_ENABLED=false)")
        return None
    if _task is not None and not _task.done():
        return _task
    _task = asyncio.create_task(_loop(), name="uptime-self-probe")
    return _task


async def stop_uptime_probe_loop() -> None:
    global _task
    if _task is None:
        return
    _task.cancel()
    await asyncio.gather(_task, return_exceptions=True)
    _task = None
