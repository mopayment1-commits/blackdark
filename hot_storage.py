"""
BLACKDARK — Async Hot-Data Pipeline (Point 38).

Decouples high-frequency market snapshots from SQLite using an in-memory
buffer and asynchronous flush workers. Supports local NDJSON spool (default),
ClickHouse HTTP ingestion, and TimescaleDB (asyncpg) backends.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import aiohttp
from pydantic import BaseModel, Field

import config

logger = logging.getLogger("BLACKDARK.HotStorage")


class HotRecordType(StrEnum):
    PRICING = "pricing"
    ORDER_BOOK = "order_book"
    FUNDING = "funding"
    TICK = "tick"


class HotRecord(BaseModel):
    record_type: HotRecordType
    timestamp: str
    exchange: str
    symbol: str
    payload: dict[str, Any]
    market_type: str = "spot"


class HotStorageStats(BaseModel):
    enqueued: int = 0
    dropped: int = 0
    flushed: int = 0
    flush_errors: int = 0
    buffer_depth: int = 0
    last_flush_at: str | None = None
    active_backends: list[str] = Field(default_factory=list)


@dataclass
class _BufferState:
    queue: deque[HotRecord] = field(default_factory=deque)
    lock: asyncio.Lock | None = None
    enqueued: int = 0
    dropped: int = 0


class HotStorageBackend(ABC):
    """Abstract async backend for hot-data persistence."""

    name: str = "base"

    @abstractmethod
    async def connect(self) -> None:
        await asyncio.sleep(0)
        raise NotImplementedError("HotStorageBackend.connect")

    @abstractmethod
    async def close(self) -> None:
        await asyncio.sleep(0)
        raise NotImplementedError("HotStorageBackend.close")

    @abstractmethod
    async def insert_batch(self, records: list[HotRecord]) -> int:
        await asyncio.sleep(0)
        raise NotImplementedError("HotStorageBackend.insert_batch")

    def health_check(self) -> bool:
        return True


class LocalNDJSONSpoolBackend(HotStorageBackend):
    """
    High-throughput local append-only spool.

    Writes newline-delimited JSON partitioned by record type and UTC date.
    """

    name = "local_ndjson"

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or config.HOT_STORAGE_DIR
        self._open_handles: dict[Path, Any] = {}

    async def connect(self) -> None:
        await asyncio.sleep(0)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        for record_type in HotRecordType:
            (self.root_dir / record_type.value).mkdir(parents=True, exist_ok=True)

    async def close(self) -> None:
        await asyncio.sleep(0)
        for handle in self._open_handles.values():
            try:
                handle.flush()
                handle.close()
            except Exception:
                logger.exception("Failed closing hot spool file handle.")
        self._open_handles.clear()

    def _spool_path(self, record: HotRecord) -> Path:
        day = record.timestamp[:10]
        return self.root_dir / record.record_type.value / f"{day}.ndjson"

    def _get_handle(self, path: Path):
        handle = self._open_handles.get(path)
        if handle is None:
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = path.open("a", encoding="utf-8")
            self._open_handles[path] = handle
        return handle

    async def insert_batch(self, records: list[HotRecord]) -> int:
        await asyncio.sleep(0)
        if not records:
            return 0

        written = 0
        for record in records:
            try:
                path = self._spool_path(record)
                line = json.dumps(record.model_dump(), separators=(",", ":"))
                handle = self._get_handle(path)
                handle.write(line + "\n")
                written += 1
            except Exception:
                logger.exception(
                    "Local spool write failed | type=%s exchange=%s symbol=%s",
                    record.record_type.value,
                    record.exchange,
                    record.symbol,
                )
        for handle in self._open_handles.values():
            try:
                handle.flush()
            except Exception:
                logger.exception("Local spool flush failed.")
        return written


class ClickHouseBackend(HotStorageBackend):
    """ClickHouse HTTP JSONEachRow ingestion backend."""

    name = "clickhouse"

    def __init__(
        self,
        base_url: str | None = None,
        database: str | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> None:
        self.base_url = (base_url or config.HOT_STORAGE_CLICKHOUSE_URL).rstrip("/")
        self.database = database or config.HOT_STORAGE_CLICKHOUSE_DATABASE
        self.user = user or config.HOT_STORAGE_CLICKHOUSE_USER
        self.password = password or config.HOT_STORAGE_CLICKHOUSE_PASSWORD
        self._session: aiohttp.ClientSession | None = None

    async def connect(self) -> None:
        if not self.base_url:
            raise RuntimeError("ClickHouse URL is not configured.")

        timeout = aiohttp.ClientTimeout(total=30)
        self._session = aiohttp.ClientSession(timeout=timeout)
        await self._ensure_schema()

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    async def _execute(self, sql: str, body: str | None = None) -> None:
        assert self._session is not None
        auth = aiohttp.BasicAuth(self.user, self.password) if self.password else None
        async with self._session.post(
            self.base_url,
            params={"query": sql},
            data=body,
            auth=auth,
        ) as response:
            response.raise_for_status()
            await response.text()

    async def _ensure_schema(self) -> None:
        statements = [
            f"CREATE DATABASE IF NOT EXISTS {self.database}",
            f"""
            CREATE TABLE IF NOT EXISTS {self.database}.hot_pricing (
                timestamp DateTime64(3),
                exchange LowCardinality(String),
                symbol LowCardinality(String),
                market_type LowCardinality(String),
                price Float64,
                volume Nullable(Float64),
                opportunity_score Float64
            ) ENGINE = MergeTree()
            ORDER BY (exchange, symbol, timestamp)
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.database}.hot_order_books (
                timestamp DateTime64(3),
                exchange LowCardinality(String),
                symbol LowCardinality(String),
                market_type LowCardinality(String),
                bids_json String,
                asks_json String
            ) ENGINE = MergeTree()
            ORDER BY (exchange, symbol, timestamp)
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.database}.hot_funding (
                timestamp DateTime64(3),
                exchange LowCardinality(String),
                symbol LowCardinality(String),
                funding_rate Float64,
                next_funding_time Nullable(String)
            ) ENGINE = MergeTree()
            ORDER BY (exchange, symbol, timestamp)
            """,
            f"""
            CREATE TABLE IF NOT EXISTS {self.database}.hot_ticks (
                timestamp DateTime64(3),
                exchange LowCardinality(String),
                symbol LowCardinality(String),
                side LowCardinality(String),
                price Float64,
                quantity Float64,
                notional_usd Float64,
                trade_time_ms Int64
            ) ENGINE = MergeTree()
            ORDER BY (exchange, symbol, trade_time_ms)
            """,
        ]
        for sql in statements:
            await self._execute(sql.strip())

    async def insert_batch(self, records: list[HotRecord]) -> int:
        if not records or self._session is None:
            return 0

        grouped: dict[str, list[dict[str, Any]]] = {
            "hot_pricing": [],
            "hot_order_books": [],
            "hot_funding": [],
            "hot_ticks": [],
        }

        for record in records:
            if record.record_type == HotRecordType.PRICING:
                grouped["hot_pricing"].append(
                    {
                        "timestamp": record.timestamp,
                        "exchange": record.exchange,
                        "symbol": record.symbol,
                        "market_type": record.market_type,
                        "price": record.payload.get("price"),
                        "volume": record.payload.get("volume"),
                        "opportunity_score": record.payload.get("opportunity_score", 0.0),
                    }
                )
            elif record.record_type == HotRecordType.ORDER_BOOK:
                grouped["hot_order_books"].append(
                    {
                        "timestamp": record.timestamp,
                        "exchange": record.exchange,
                        "symbol": record.symbol,
                        "market_type": record.market_type,
                        "bids_json": json.dumps(record.payload.get("bids", []), separators=(",", ":")),
                        "asks_json": json.dumps(record.payload.get("asks", []), separators=(",", ":")),
                    }
                )
            elif record.record_type == HotRecordType.FUNDING:
                grouped["hot_funding"].append(
                    {
                        "timestamp": record.timestamp,
                        "exchange": record.exchange,
                        "symbol": record.symbol,
                        "funding_rate": record.payload.get("funding_rate"),
                        "next_funding_time": record.payload.get("next_funding_time"),
                    }
                )
            elif record.record_type == HotRecordType.TICK:
                grouped["hot_ticks"].append(
                    {
                        "timestamp": record.timestamp,
                        "exchange": record.exchange,
                        "symbol": record.symbol,
                        "side": record.payload.get("side"),
                        "price": record.payload.get("price"),
                        "quantity": record.payload.get("quantity"),
                        "notional_usd": record.payload.get("notional_usd"),
                        "trade_time_ms": record.payload.get("trade_time_ms"),
                    }
                )

        inserted = 0
        for table, rows in grouped.items():
            if not rows:
                continue
            body = "\n".join(json.dumps(row, separators=(",", ":")) for row in rows)
            query = f"INSERT INTO {self.database}.{table} FORMAT JSONEachRow"
            try:
                await self._execute(query, body)
                inserted += len(rows)
            except Exception:
                logger.exception("ClickHouse batch insert failed | table=%s rows=%d", table, len(rows))
        return inserted


class TimescaleDBBackend(HotStorageBackend):
    """TimescaleDB backend using asyncpg."""

    name = "timescale"

    def __init__(self, dsn: str | None = None, schema: str | None = None) -> None:
        from sql_safety import require_schema_ident

        self.dsn = dsn or config.HOT_STORAGE_TIMESCALE_DSN
        self.schema = require_schema_ident(schema or config.HOT_STORAGE_TIMESCALE_SCHEMA)
        self._pool: Any = None

    async def connect(self) -> None:
        if not self.dsn:
            raise RuntimeError("TimescaleDB DSN is not configured.")

        try:
            import asyncpg
        except ImportError as exc:
            raise RuntimeError(
                "asyncpg is required for TimescaleDB hot storage. Install with: pip install asyncpg"
            ) from exc

        self._pool = await asyncpg.create_pool(dsn=self.dsn, min_size=1, max_size=5)
        schema = self.schema
        async with self._pool.acquire() as conn:
            create_schema = f"CREATE SCHEMA IF NOT EXISTS {schema}"  # nosec B608
            await conn.execute(create_schema)
            pricing_ddl = (
                f"CREATE TABLE IF NOT EXISTS {schema}.hot_pricing ("  # nosec B608
                "timestamp TIMESTAMPTZ NOT NULL, exchange TEXT NOT NULL, symbol TEXT NOT NULL, "
                "market_type TEXT NOT NULL, price DOUBLE PRECISION NOT NULL, "
                "volume DOUBLE PRECISION, opportunity_score DOUBLE PRECISION)"
            )
            books_ddl = (
                f"CREATE TABLE IF NOT EXISTS {schema}.hot_order_books ("  # nosec B608
                "timestamp TIMESTAMPTZ NOT NULL, exchange TEXT NOT NULL, symbol TEXT NOT NULL, "
                "market_type TEXT NOT NULL, bids_json JSONB NOT NULL, asks_json JSONB NOT NULL)"
            )
            funding_ddl = (
                f"CREATE TABLE IF NOT EXISTS {schema}.hot_funding ("  # nosec B608
                "timestamp TIMESTAMPTZ NOT NULL, exchange TEXT NOT NULL, symbol TEXT NOT NULL, "
                "funding_rate DOUBLE PRECISION NOT NULL, next_funding_time TEXT)"
            )
            ticks_ddl = (
                f"CREATE TABLE IF NOT EXISTS {schema}.hot_ticks ("  # nosec B608
                "timestamp TIMESTAMPTZ NOT NULL, exchange TEXT NOT NULL, symbol TEXT NOT NULL, "
                "side TEXT NOT NULL, price DOUBLE PRECISION NOT NULL, quantity DOUBLE PRECISION NOT NULL, "
                "notional_usd DOUBLE PRECISION NOT NULL, trade_time_ms BIGINT NOT NULL)"
            )
            for ddl in (pricing_ddl, books_ddl, funding_ddl, ticks_ddl):
                await conn.execute(ddl)
            for table in ("hot_pricing", "hot_order_books", "hot_funding", "hot_ticks"):
                try:
                    hyper = (
                        f"SELECT create_hypertable('{schema}.{table}', 'timestamp', "  # nosec B608
                        "if_not_exists => TRUE)"
                    )
                    await conn.execute(hyper)
                except Exception:
                    logger.warning(
                        "Timescale hypertable setup skipped for %s.%s (extension may be unavailable).",
                        self.schema,
                        table,
                    )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
        self._pool = None

    async def insert_batch(self, records: list[HotRecord]) -> int:
        if not records or self._pool is None:
            return 0

        pricing_rows = []
        book_rows = []
        funding_rows = []
        tick_rows = []

        for record in records:
            if record.record_type == HotRecordType.PRICING:
                pricing_rows.append(
                    (
                        record.timestamp,
                        record.exchange,
                        record.symbol,
                        record.market_type,
                        record.payload.get("price"),
                        record.payload.get("volume"),
                        record.payload.get("opportunity_score", 0.0),
                    )
                )
            elif record.record_type == HotRecordType.ORDER_BOOK:
                book_rows.append(
                    (
                        record.timestamp,
                        record.exchange,
                        record.symbol,
                        record.market_type,
                        json.dumps(record.payload.get("bids", []), separators=(",", ":")),
                        json.dumps(record.payload.get("asks", []), separators=(",", ":")),
                    )
                )
            elif record.record_type == HotRecordType.FUNDING:
                funding_rows.append(
                    (
                        record.timestamp,
                        record.exchange,
                        record.symbol,
                        record.payload.get("funding_rate"),
                        record.payload.get("next_funding_time"),
                    )
                )
            elif record.record_type == HotRecordType.TICK:
                tick_rows.append(
                    (
                        record.timestamp,
                        record.exchange,
                        record.symbol,
                        record.payload.get("side"),
                        record.payload.get("price"),
                        record.payload.get("quantity"),
                        record.payload.get("notional_usd"),
                        record.payload.get("trade_time_ms"),
                    )
                )

        inserted = 0
        schema = self.schema
        insert_pricing = (
            f"INSERT INTO {schema}.hot_pricing ("  # nosec B608
            "timestamp, exchange, symbol, market_type, price, volume, opportunity_score) "
            "VALUES ($1::timestamptz, $2, $3, $4, $5, $6, $7)"
        )
        insert_books = (
            f"INSERT INTO {schema}.hot_order_books ("  # nosec B608
            "timestamp, exchange, symbol, market_type, bids_json, asks_json) "
            "VALUES ($1::timestamptz, $2, $3, $4, $5::jsonb, $6::jsonb)"
        )
        insert_funding = (
            f"INSERT INTO {schema}.hot_funding ("  # nosec B608
            "timestamp, exchange, symbol, funding_rate, next_funding_time) "
            "VALUES ($1::timestamptz, $2, $3, $4, $5)"
        )
        insert_ticks = (
            f"INSERT INTO {schema}.hot_ticks ("  # nosec B608
            "timestamp, exchange, symbol, side, price, quantity, notional_usd, trade_time_ms) "
            "VALUES ($1::timestamptz, $2, $3, $4, $5, $6, $7, $8)"
        )
        async with self._pool.acquire() as conn:
            if pricing_rows:
                await conn.executemany(insert_pricing, pricing_rows)
                inserted += len(pricing_rows)
            if book_rows:
                await conn.executemany(insert_books, book_rows)
                inserted += len(book_rows)
            if funding_rows:
                await conn.executemany(insert_funding, funding_rows)
                inserted += len(funding_rows)
            if tick_rows:
                await conn.executemany(insert_ticks, tick_rows)
                inserted += len(tick_rows)
        return inserted


class SQLiteMirrorBackend(HotStorageBackend):
    """Background mirror into the primary SQLite cold store."""

    name = "sqlite_mirror"

    async def connect(self) -> None:
        from database import init_db

        await init_db()

    async def close(self) -> None:
        await asyncio.sleep(0)
        return None

    async def insert_batch(self, records: list[HotRecord]) -> int:
        if not records:
            return 0

        from database import insert_funding_rate, insert_order_book, insert_pricing_log

        written = 0
        for record in records:
            try:
                if record.record_type == HotRecordType.PRICING:
                    await insert_pricing_log(
                        exchange=record.exchange,
                        symbol=record.symbol,
                        price=float(record.payload["price"]),
                        volume=record.payload.get("volume"),
                        opportunity_score=record.payload.get("opportunity_score"),
                        timestamp=record.timestamp,
                        market_type=record.market_type,
                    )
                elif record.record_type == HotRecordType.ORDER_BOOK:
                    await insert_order_book(
                        exchange=record.exchange,
                        symbol=record.symbol,
                        bids=record.payload.get("bids", []),
                        asks=record.payload.get("asks", []),
                        timestamp=record.timestamp,
                        market_type=record.market_type,
                    )
                elif record.record_type == HotRecordType.FUNDING:
                    await insert_funding_rate(
                        exchange=record.exchange,
                        symbol=record.symbol,
                        funding_rate=float(record.payload["funding_rate"]),
                        next_funding_time=record.payload.get("next_funding_time"),
                        timestamp=record.timestamp,
                    )
                written += 1
            except Exception:
                logger.exception(
                    "SQLite mirror write failed | type=%s exchange=%s symbol=%s",
                    record.record_type.value,
                    record.exchange,
                    record.symbol,
                )
        return written


def _resolve_backend_mode() -> str:
    env_mode = os.getenv("HOT_STORAGE_BACKEND", config.HOT_STORAGE_BACKEND).strip().lower()
    if env_mode:
        return env_mode
    if os.getenv("HOT_STORAGE_CLICKHOUSE_URL") or config.HOT_STORAGE_CLICKHOUSE_URL:
        return "clickhouse"
    if os.getenv("HOT_STORAGE_TIMESCALE_DSN") or config.HOT_STORAGE_TIMESCALE_DSN:
        return "timescale"
    return "local"


def build_hot_storage_backends(mode: str | None = None) -> list[HotStorageBackend]:
    """Construct backend chain from config and environment."""
    resolved = (mode or _resolve_backend_mode()).lower()
    backends: list[HotStorageBackend] = [LocalNDJSONSpoolBackend()]

    if resolved in {"clickhouse", "multi"}:
        url = os.getenv("HOT_STORAGE_CLICKHOUSE_URL", config.HOT_STORAGE_CLICKHOUSE_URL)
        if url:
            backends.append(
                ClickHouseBackend(
                    base_url=url,
                    database=os.getenv(
                        "HOT_STORAGE_CLICKHOUSE_DATABASE",
                        config.HOT_STORAGE_CLICKHOUSE_DATABASE,
                    ),
                    user=os.getenv("HOT_STORAGE_CLICKHOUSE_USER", config.HOT_STORAGE_CLICKHOUSE_USER),
                    password=os.getenv(
                        "HOT_STORAGE_CLICKHOUSE_PASSWORD",
                        config.HOT_STORAGE_CLICKHOUSE_PASSWORD,
                    ),
                )
            )

    if resolved in {"timescale", "multi"}:
        dsn = os.getenv("HOT_STORAGE_TIMESCALE_DSN", config.HOT_STORAGE_TIMESCALE_DSN)
        if dsn:
            backends.append(TimescaleDBBackend(dsn=dsn))

    if config.HOT_STORAGE_MIRROR_SQLITE:
        backends.append(SQLiteMirrorBackend())

    return backends


class HotDataPipeline:
    """
    In-memory hot-data sink with asynchronous flush workers.

    Aggregator producers enqueue with put-nowait semantics so the polling loop
    never waits on remote database I/O.
    """

    def __init__(
        self,
        *,
        max_buffer: int | None = None,
        batch_size: int | None = None,
        flush_interval_seconds: float | None = None,
        backends: list[HotStorageBackend] | None = None,
    ) -> None:
        self.max_buffer = max_buffer or config.HOT_STORAGE_BUFFER_MAX
        self.batch_size = batch_size or config.HOT_STORAGE_FLUSH_BATCH_SIZE
        self.flush_interval_seconds = (
            flush_interval_seconds or config.HOT_STORAGE_FLUSH_INTERVAL_SECONDS
        )
        self.backends = backends or build_hot_storage_backends()
        self._buffer = _BufferState()
        self._buffer.lock = asyncio.Lock()
        self._running = False
        self._flush_task: asyncio.Task[None] | None = None
        self._stats = HotStorageStats(active_backends=[backend.name for backend in self.backends])
        self._flush_lock = asyncio.Lock()

    @property
    def stats(self) -> HotStorageStats:
        self._stats.buffer_depth = len(self._buffer.queue)
        return self._stats.model_copy()

    def enqueue(self, record: HotRecord) -> bool:
        """
        Non-blocking enqueue into the in-memory hot buffer.

        Returns True when accepted, False when dropped due to backpressure.
        """
        try:
            if len(self._buffer.queue) >= self.max_buffer:
                self._buffer.queue.popleft()
                self._buffer.dropped += 1
                self._stats.dropped += 1

            self._buffer.queue.append(record)
            self._buffer.enqueued += 1
            self._stats.enqueued += 1
            self._stats.buffer_depth = len(self._buffer.queue)
            return True
        except Exception:
            logger.exception(
                "Hot buffer enqueue failed | type=%s exchange=%s symbol=%s",
                record.record_type.value,
                record.exchange,
                record.symbol,
            )
            return False

    async def start(self) -> None:
        if self._running:
            return

        for backend in self.backends:
            try:
                await backend.connect()
            except Exception:
                logger.exception("Hot storage backend connect failed | backend=%s", backend.name)

        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop(), name="hot-storage-flush")
        logger.info(
            "Hot-data pipeline started | backends=%s buffer_max=%d batch=%d interval=%ss",
            [backend.name for backend in self.backends],
            self.max_buffer,
            self.batch_size,
            self.flush_interval_seconds,
        )

    async def stop(self) -> None:
        self._running = False
        if self._flush_task is not None:
            self._flush_task.cancel()
            await asyncio.gather(self._flush_task, return_exceptions=True)
            self._flush_task = None

        await self.flush_now()

        for backend in self.backends:
            try:
                await backend.close()
            except Exception:
                logger.exception("Hot storage backend close failed | backend=%s", backend.name)

        logger.info("Hot-data pipeline stopped.")

    async def _drain_batch(self, limit: int) -> list[HotRecord]:
        lock = self._buffer.lock
        if lock is None:
            lock = asyncio.Lock()
            self._buffer.lock = lock

        async with lock:
            batch: list[HotRecord] = []
            while self._buffer.queue and len(batch) < limit:
                batch.append(self._buffer.queue.popleft())
            self._stats.buffer_depth = len(self._buffer.queue)
            return batch

    async def flush_now(self) -> int:
        async with self._flush_lock:
            total_flushed = 0
            while True:
                batch = await self._drain_batch(self.batch_size)
                if not batch:
                    break
                total_flushed += await self._flush_batch(batch)
            return total_flushed

    async def _flush_batch(self, batch: list[HotRecord]) -> int:
        if not batch:
            return 0

        flushed = 0
        for backend in self.backends:
            try:
                flushed = max(flushed, await backend.insert_batch(batch))
            except Exception:
                self._stats.flush_errors += 1
                logger.exception("Hot storage flush failed | backend=%s", backend.name)

        self._stats.flushed += len(batch)
        self._stats.last_flush_at = datetime.now(UTC).isoformat()
        return flushed

    async def _flush_loop(self) -> None:
        while self._running:
            await asyncio.sleep(self.flush_interval_seconds)
            try:
                batch = await self._drain_batch(self.batch_size)
                if batch:
                    await self._flush_batch(batch)
            except Exception:
                self._stats.flush_errors += 1
                logger.exception("Hot storage flush loop iteration failed.")


_pipeline: HotDataPipeline | None = None
_pipeline_lock = asyncio.Lock()


async def start_hot_pipeline(
    *,
    backends: list[HotStorageBackend] | None = None,
) -> HotDataPipeline:
    global _pipeline
    async with _pipeline_lock:
        if _pipeline is None:
            _pipeline = HotDataPipeline(backends=backends)
        await _pipeline.start()
        return _pipeline


async def shutdown_hot_pipeline() -> None:
    global _pipeline
    async with _pipeline_lock:
        if _pipeline is not None:
            await _pipeline.stop()
            _pipeline = None


def get_hot_pipeline() -> HotDataPipeline | None:
    return _pipeline


@asynccontextmanager
async def hot_pipeline_context(
    *,
    backends: list[HotStorageBackend] | None = None,
) -> AsyncIterator[HotDataPipeline]:
    pipeline = await start_hot_pipeline(backends=backends)
    try:
        yield pipeline
    finally:
        await shutdown_hot_pipeline()


def enqueue_pricing_snapshot(
    *,
    exchange: str,
    symbol: str,
    price: float,
    volume: float | None,
    timestamp: str,
    market_type: str = "spot",
    opportunity_score: float = 0.0,
) -> bool:
    pipeline = get_hot_pipeline()
    if pipeline is None:
        return False
    return pipeline.enqueue(
        HotRecord(
            record_type=HotRecordType.PRICING,
            timestamp=timestamp,
            exchange=exchange,
            symbol=symbol,
            market_type=market_type,
            payload={
                "price": price,
                "volume": volume,
                "opportunity_score": opportunity_score,
            },
        )
    )


def enqueue_order_book_snapshot(
    *,
    exchange: str,
    symbol: str,
    bids: list[list[float]],
    asks: list[list[float]],
    timestamp: str,
    market_type: str = "spot",
) -> bool:
    pipeline = get_hot_pipeline()
    if pipeline is None:
        return False
    return pipeline.enqueue(
        HotRecord(
            record_type=HotRecordType.ORDER_BOOK,
            timestamp=timestamp,
            exchange=exchange,
            symbol=symbol,
            market_type=market_type,
            payload={"bids": bids, "asks": asks},
        )
    )


def enqueue_funding_snapshot(
    *,
    exchange: str,
    symbol: str,
    funding_rate: float,
    next_funding_time: str | None,
    timestamp: str,
) -> bool:
    pipeline = get_hot_pipeline()
    if pipeline is None:
        return False
    return pipeline.enqueue(
        HotRecord(
            record_type=HotRecordType.FUNDING,
            timestamp=timestamp,
            exchange=exchange,
            symbol=symbol,
            payload={
                "funding_rate": funding_rate,
                "next_funding_time": next_funding_time,
            },
        )
    )


def enqueue_market_snapshot(
    *,
    exchange: str,
    symbol: str,
    price: float,
    volume: float | None,
    bids: list[list[float]],
    asks: list[list[float]],
    timestamp: str,
    market_type: str = "spot",
    opportunity_score: float = 0.0,
) -> tuple[bool, bool]:
    pricing_ok = enqueue_pricing_snapshot(
        exchange=exchange,
        symbol=symbol,
        price=price,
        volume=volume,
        timestamp=timestamp,
        market_type=market_type,
        opportunity_score=opportunity_score,
    )
    book_ok = enqueue_order_book_snapshot(
        exchange=exchange,
        symbol=symbol,
        bids=bids,
        asks=asks,
        timestamp=timestamp,
        market_type=market_type,
    )
    return pricing_ok, book_ok


def enqueue_tick_snapshot(
    *,
    exchange: str,
    symbol: str,
    side: str,
    price: float,
    quantity: float,
    notional_usd: float,
    trade_time_ms: int,
    timestamp: str,
) -> bool:
    """Enqueue a tick-by-tick trade print into the hot buffer (non-blocking)."""
    pipeline = get_hot_pipeline()
    if pipeline is None:
        return False
    return pipeline.enqueue(
        HotRecord(
            record_type=HotRecordType.TICK,
            timestamp=timestamp,
            exchange=exchange,
            symbol=symbol,
            payload={
                "side": side,
                "price": price,
                "quantity": quantity,
                "notional_usd": notional_usd,
                "trade_time_ms": trade_time_ms,
            },
        )
    )


def get_hot_storage_stats() -> HotStorageStats:
    pipeline = get_hot_pipeline()
    if pipeline is None:
        return HotStorageStats()
    return pipeline.stats
