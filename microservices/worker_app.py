"""
BLACKDARK — Standalone microservice worker (health + background loops).

Usage:
  SERVICE_MODE=aggregator uvicorn microservices.worker_app:app --port 8091
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from microservices.lifecycle import ServiceContext, current_mode, service_info, shutdown, startup

_ctx: ServiceContext | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ctx
    _ctx = await startup()
    yield
    if _ctx is not None:
        await shutdown(_ctx)
        _ctx = None


app = FastAPI(
    title=f"BLACKDARK Worker ({current_mode()})",
    lifespan=lifespan,
)


@app.get("/health/live")
async def health_live():
    """Instant liveness probe — no DB/Redis (target <50ms)."""
    import time

    return {"status": "ok", "probe": "live", "service_mode": current_mode(), "ts": time.time()}


@app.get("/health/ready")
async def health_ready():
    from postgres_backend import pool_stats, use_postgres
    from service_bus import bus_stats

    return {
        "status": "ok",
        "probe": "ready",
        "service_mode": current_mode(),
        "database_engine": "postgresql" if use_postgres() else "sqlite",
        "postgres_pool": pool_stats(),
        "service_bus": bus_stats(),
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service_mode": current_mode(),
        "probes": {"live": "/health/live", "ready": "/health/ready"},
    }


@app.get("/api/services/status")
async def services_status():
    return service_info(_ctx)
