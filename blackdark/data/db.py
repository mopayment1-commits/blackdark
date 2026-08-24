"""SQLAlchemy 2.0 async database session for Wave 01 data engine."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import config
from postgres_backend import use_postgres

logger = logging.getLogger("BLACKDARK.DataEngine.DB")

_engine: Any = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_initialized = False


def _async_url() -> str:
    url = (getattr(config, "DATABASE_URL", None) or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is required for the Wave 01 data engine (PostgreSQL).")
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    raise RuntimeError(f"Unsupported DATABASE_URL for data engine: {url[:32]}...")


def data_engine_available() -> bool:
    return use_postgres()


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _async_url(),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_data_engine() -> dict[str, Any]:
    """Run migrations and prepare session factory."""
    global _initialized
    if not data_engine_available():
        return {"ok": False, "reason": "postgres_required"}
    from blackdark.data.migrate import apply_migrations

    result = await apply_migrations()
    get_session_factory()
    _initialized = True
    logger.info("Wave 01 data engine initialized | migrations=%s", result.get("applied"))
    return {"ok": True, **result}


async def ensure_data_engine_ready() -> None:
    if not _initialized:
        await init_data_engine()
