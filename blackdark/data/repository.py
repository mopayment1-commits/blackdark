"""Repository layer for Wave 01 data engine (PostgreSQL)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_SOURCES = (
    {
        "slug": "binance",
        "name": "Binance",
        "source_type": "exchange",
        "base_url": "https://api.binance.com",
        "rate_limit_rps": Decimal("20.0"),
        "metadata": {"spot": True, "futures": "https://fapi.binance.com"},
    },
    {
        "slug": "coingecko",
        "name": "CoinGecko",
        "source_type": "aggregator",
        "base_url": "https://api.coingecko.com/api/v3",
        "rate_limit_rps": Decimal("0.5"),
        "metadata": {"free_tier": True},
    },
)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat()


def _dec(value: Any) -> str | None:
    if value is None:
        return None
    return str(Decimal(str(value)))


async def seed_data_sources(session: AsyncSession) -> dict[str, Any]:
    inserted = 0
    for src in DEFAULT_SOURCES:
        result = await session.execute(
            text(
                """
                INSERT INTO data_sources (slug, name, source_type, base_url, rate_limit_rps, metadata)
                VALUES (:slug, :name, :source_type, :base_url, :rate_limit_rps, CAST(:metadata AS jsonb))
                ON CONFLICT (slug) DO UPDATE SET
                    name = EXCLUDED.name,
                    base_url = EXCLUDED.base_url,
                    rate_limit_rps = EXCLUDED.rate_limit_rps,
                    metadata = EXCLUDED.metadata,
                    updated_at = NOW()
                RETURNING id
                """
            ),
            {
                "slug": src["slug"],
                "name": src["name"],
                "source_type": src["source_type"],
                "base_url": src["base_url"],
                "rate_limit_rps": src["rate_limit_rps"],
                "metadata": json.dumps(src["metadata"]),
            },
        )
        if result.fetchone():
            inserted += 1
    return {"seeded": inserted, "sources": [s["slug"] for s in DEFAULT_SOURCES]}


async def get_source_by_slug(session: AsyncSession, slug: str) -> dict[str, Any] | None:
    result = await session.execute(
        text("SELECT * FROM data_sources WHERE slug = :slug"),
        {"slug": slug},
    )
    row = result.mappings().fetchone()
    return dict(row) if row else None


async def create_ingestion_run(
    session: AsyncSession,
    *,
    source_id: int,
    run_type: str,
    params: dict[str, Any] | None = None,
    triggered_by: str = "system",
) -> UUID:
    run_id = uuid4()
    await session.execute(
        text(
            """
            INSERT INTO ingestion_runs (id, source_id, run_type, status, params, triggered_by)
            VALUES (:id, :source_id, :run_type, 'running', CAST(:params AS jsonb), :triggered_by)
            """
        ),
        {
            "id": str(run_id),
            "source_id": source_id,
            "run_type": run_type,
            "params": json.dumps(params or {}),
            "triggered_by": triggered_by,
        },
    )
    return run_id


async def finish_ingestion_run(
    session: AsyncSession,
    run_id: UUID | str,
    *,
    status: str,
    records_fetched: int,
    records_inserted: int,
    records_deduped: int,
    errors_count: int = 0,
    error_log: str | None = None,
) -> None:
    await session.execute(
        text(
            """
            UPDATE ingestion_runs SET
                status = :status,
                completed_at = NOW(),
                records_fetched = :fetched,
                records_inserted = :inserted,
                records_deduped = :deduped,
                errors_count = :errors,
                error_log = :error_log
            WHERE id = :id
            """
        ),
        {
            "id": str(run_id),
            "status": status,
            "fetched": records_fetched,
            "inserted": records_inserted,
            "deduped": records_deduped,
            "errors": errors_count,
            "error_log": error_log,
        },
    )


async def log_ingestion_error(
    session: AsyncSession,
    *,
    ingestion_run_id: UUID | str,
    source_id: int,
    error_type: str,
    error_message: str,
    endpoint: str | None = None,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO ingestion_errors
                (ingestion_run_id, source_id, error_type, error_message, endpoint)
            VALUES (:run_id, :source_id, :error_type, :message, :endpoint)
            """
        ),
        {
            "run_id": str(ingestion_run_id),
            "source_id": source_id,
            "error_type": error_type,
            "message": error_message[:4000],
            "endpoint": endpoint,
        },
    )


async def insert_ohlcv_row(
    session: AsyncSession,
    *,
    source_id: int,
    ingestion_run_id: UUID | str,
    row: dict[str, Any],
    provenance_hash: str | None = None,
) -> int | None:
    result = await session.execute(
        text(
            """
            INSERT INTO ohlcv_data (
                source_id, ingestion_run_id, symbol, quote_asset, interval,
                open_time, close_time, open_price, high_price, low_price, close_price,
                volume, quote_volume, trades_count,
                taker_buy_base_volume, taker_buy_quote_volume, provenance_hash
            ) VALUES (
                :source_id, :run_id, :symbol, :quote_asset, :interval,
                :open_time, :close_time, :open, :high, :low, :close,
                :volume, :quote_volume, :trades_count,
                :taker_buy_base, :taker_buy_quote, :prov_hash
            )
            ON CONFLICT (source_id, symbol, interval, open_time) DO NOTHING
            RETURNING id
            """
        ),
        {
            "source_id": source_id,
            "run_id": str(ingestion_run_id),
            "symbol": row["symbol"],
            "quote_asset": row.get("quote_asset", "USDT"),
            "interval": row["interval"],
            "open_time": row["open_time"],
            "close_time": row["close_time"],
            "open": _dec(row["open"]),
            "high": _dec(row["high"]),
            "low": _dec(row["low"]),
            "close": _dec(row["close"]),
            "volume": _dec(row["volume"]),
            "quote_volume": _dec(row.get("quote_volume")),
            "trades_count": row.get("trades_count"),
            "taker_buy_base": _dec(row.get("taker_buy_base_volume")),
            "taker_buy_quote": _dec(row.get("taker_buy_quote_volume")),
            "prov_hash": provenance_hash,
        },
    )
    inserted = result.fetchone()
    return int(inserted[0]) if inserted else None


async def insert_funding_row(
    session: AsyncSession,
    *,
    source_id: int,
    ingestion_run_id: UUID | str,
    row: dict[str, Any],
) -> int | None:
    result = await session.execute(
        text(
            """
            INSERT INTO de_funding_rates (
                source_id, ingestion_run_id, symbol, funding_time,
                funding_rate, mark_price, index_price, realized_rate
            ) VALUES (
                :source_id, :run_id, :symbol, :funding_time,
                :funding_rate, :mark_price, :index_price, :realized_rate
            )
            ON CONFLICT (source_id, symbol, funding_time) DO NOTHING
            RETURNING id
            """
        ),
        {
            "source_id": source_id,
            "run_id": str(ingestion_run_id),
            "symbol": row["symbol"],
            "funding_time": row["funding_time"],
            "funding_rate": _dec(row["funding_rate"]),
            "mark_price": _dec(row.get("mark_price")),
            "index_price": _dec(row.get("index_price")),
            "realized_rate": _dec(row.get("realized_rate")),
        },
    )
    inserted = result.fetchone()
    return int(inserted[0]) if inserted else None


async def insert_open_interest_row(
    session: AsyncSession,
    *,
    source_id: int,
    ingestion_run_id: UUID | str,
    row: dict[str, Any],
) -> int | None:
    result = await session.execute(
        text(
            """
            INSERT INTO open_interest (
                source_id, ingestion_run_id, symbol, oi_time,
                open_interest, open_interest_value
            ) VALUES (
                :source_id, :run_id, :symbol, :oi_time,
                :open_interest, :open_interest_value
            )
            ON CONFLICT (source_id, symbol, oi_time) DO NOTHING
            RETURNING id
            """
        ),
        {
            "source_id": source_id,
            "run_id": str(ingestion_run_id),
            "symbol": row["symbol"],
            "oi_time": row["oi_time"],
            "open_interest": _dec(row["open_interest"]),
            "open_interest_value": _dec(row.get("open_interest_value")),
        },
    )
    inserted = result.fetchone()
    return int(inserted[0]) if inserted else None


async def insert_market_snapshot_row(
    session: AsyncSession,
    *,
    source_id: int,
    ingestion_run_id: UUID | str,
    row: dict[str, Any],
) -> int | None:
    result = await session.execute(
        text(
            """
            INSERT INTO market_snapshots (
                source_id, ingestion_run_id, coin_id, symbol, name,
                current_price, market_cap, total_volume,
                price_change_24h, price_change_pct_24h,
                circulating_supply, total_supply, max_supply,
                ath, ath_change_pct, ath_date,
                atl, atl_change_pct, atl_date, last_updated, fetched_at
            ) VALUES (
                :source_id, :run_id, :coin_id, :symbol, :name,
                :current_price, :market_cap, :total_volume,
                :price_change_24h, :price_change_pct_24h,
                :circulating_supply, :total_supply, :max_supply,
                :ath, :ath_change_pct, :ath_date,
                :atl, :atl_change_pct, :atl_date, :last_updated,
                COALESCE(:fetched_at, NOW())
            )
            ON CONFLICT (source_id, coin_id, fetched_at) DO NOTHING
            RETURNING id
            """
        ),
        {
            "source_id": source_id,
            "run_id": str(ingestion_run_id),
            "coin_id": row["coin_id"],
            "symbol": row["symbol"],
            "name": row.get("name"),
            "current_price": _dec(row.get("current_price")),
            "market_cap": _dec(row.get("market_cap")),
            "total_volume": _dec(row.get("total_volume")),
            "price_change_24h": _dec(row.get("price_change_24h")),
            "price_change_pct_24h": _dec(row.get("price_change_pct_24h")),
            "circulating_supply": _dec(row.get("circulating_supply")),
            "total_supply": _dec(row.get("total_supply")),
            "max_supply": _dec(row.get("max_supply")),
            "ath": _dec(row.get("ath")),
            "ath_change_pct": _dec(row.get("ath_change_pct")),
            "ath_date": row.get("ath_date"),
            "atl": _dec(row.get("atl")),
            "atl_change_pct": _dec(row.get("atl_change_pct")),
            "atl_date": row.get("atl_date"),
            "last_updated": row.get("last_updated"),
            "fetched_at": row.get("last_updated") or row.get("fetched_at"),
        },
    )
    inserted = result.fetchone()
    return int(inserted[0]) if inserted else None


async def query_ohlcv(
    session: AsyncSession,
    *,
    symbol: str,
    interval: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    source_slug: str | None = None,
) -> list[dict[str, Any]]:
    clauses = ["o.symbol = :symbol", "o.interval = :interval"]
    params: dict[str, Any] = {"symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)}
    if start_time:
        clauses.append("o.open_time >= :start_time")
        params["start_time"] = start_time
    if end_time:
        clauses.append("o.open_time <= :end_time")
        params["end_time"] = end_time
    if source_slug:
        clauses.append("ds.slug = :source_slug")
        params["source_slug"] = source_slug
    where = " AND ".join(clauses)
    result = await session.execute(
        text(
            f"""
            SELECT
                o.open_time, o.open_price AS open, o.high_price AS high,
                o.low_price AS low, o.close_price AS close, o.volume,
                ds.slug AS source, p.id AS provenance_id
            FROM ohlcv_data o
            LEFT JOIN data_sources ds ON ds.id = o.source_id
            LEFT JOIN LATERAL (
                SELECT id FROM data_provenance
                WHERE target_table = 'ohlcv_data' AND target_record_id = o.id
                ORDER BY parsed_at DESC LIMIT 1
            ) p ON true
            WHERE {where}
            ORDER BY o.open_time DESC
            LIMIT :limit
            """
        ),
        params,
    )
    rows = []
    for row in result.mappings().fetchall():
        item = dict(row)
        item["open_time"] = _iso(item["open_time"])
        for k in ("open", "high", "low", "close", "volume"):
            if item.get(k) is not None:
                item[k] = str(item[k])
        if item.get("provenance_id"):
            item["provenance_id"] = str(item["provenance_id"])
        rows.append(item)
    return rows


async def query_funding(
    session: AsyncSession,
    *,
    symbol: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    source_slug: str | None = None,
) -> list[dict[str, Any]]:
    clauses = ["f.symbol = :symbol"]
    params: dict[str, Any] = {"symbol": symbol.upper(), "limit": min(limit, 1000)}
    if start_time:
        clauses.append("f.funding_time >= :start_time")
        params["start_time"] = start_time
    if end_time:
        clauses.append("f.funding_time <= :end_time")
        params["end_time"] = end_time
    if source_slug:
        clauses.append("ds.slug = :source_slug")
        params["source_slug"] = source_slug
    where = " AND ".join(clauses)
    result = await session.execute(
        text(
            f"""
            SELECT f.funding_time, f.funding_rate, f.mark_price, f.index_price,
                   ds.slug AS source, p.id AS provenance_id
            FROM funding_rates f
            LEFT JOIN data_sources ds ON ds.id = f.source_id
            LEFT JOIN LATERAL (
                SELECT id FROM data_provenance
                WHERE target_table = 'funding_rates' AND target_record_id = f.id
                ORDER BY parsed_at DESC LIMIT 1
            ) p ON true
            WHERE {where}
            ORDER BY f.funding_time DESC
            LIMIT :limit
            """
        ),
        params,
    )
    rows = []
    for row in result.mappings().fetchall():
        item = dict(row)
        item["funding_time"] = _iso(item["funding_time"])
        if item.get("funding_rate") is not None:
            item["funding_rate"] = str(item["funding_rate"])
        if item.get("provenance_id"):
            item["provenance_id"] = str(item["provenance_id"])
        rows.append(item)
    return rows


async def query_open_interest(
    session: AsyncSession,
    *,
    symbol: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
    source_slug: str | None = None,
) -> list[dict[str, Any]]:
    clauses = ["oi.symbol = :symbol"]
    params: dict[str, Any] = {"symbol": symbol.upper(), "limit": min(limit, 1000)}
    if start_time:
        clauses.append("oi.oi_time >= :start_time")
        params["start_time"] = start_time
    if end_time:
        clauses.append("oi.oi_time <= :end_time")
        params["end_time"] = end_time
    if source_slug:
        clauses.append("ds.slug = :source_slug")
        params["source_slug"] = source_slug
    where = " AND ".join(clauses)
    result = await session.execute(
        text(
            f"""
            SELECT oi.oi_time, oi.open_interest, oi.open_interest_value,
                   ds.slug AS source, p.id AS provenance_id
            FROM open_interest oi
            LEFT JOIN data_sources ds ON ds.id = oi.source_id
            LEFT JOIN LATERAL (
                SELECT id FROM data_provenance
                WHERE target_table = 'open_interest' AND target_record_id = oi.id
                ORDER BY parsed_at DESC LIMIT 1
            ) p ON true
            WHERE {where}
            ORDER BY oi.oi_time DESC
            LIMIT :limit
            """
        ),
        params,
    )
    rows = []
    for row in result.mappings().fetchall():
        item = dict(row)
        item["oi_time"] = _iso(item["oi_time"])
        if item.get("open_interest") is not None:
            item["open_interest"] = str(item["open_interest"])
        if item.get("provenance_id"):
            item["provenance_id"] = str(item["provenance_id"])
        rows.append(item)
    return rows


async def query_events(
    session: AsyncSession,
    *,
    event_type: str | None = None,
    severity: str | None = None,
    symbol: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: dict[str, Any] = {"limit": min(limit, 1000)}
    if event_type:
        clauses.append("event_type = :event_type")
        params["event_type"] = event_type
    if severity:
        clauses.append("severity = :severity")
        params["severity"] = severity
    if symbol:
        clauses.append("symbol = :symbol")
        params["symbol"] = symbol.upper()
    if start_time:
        clauses.append("start_time >= :start_time")
        params["start_time"] = start_time
    if end_time:
        clauses.append("start_time <= :end_time")
        params["end_time"] = end_time
    where = " AND ".join(clauses)
    result = await session.execute(
        text(
            f"""
            SELECT id, event_type, severity, symbol, start_time, end_time,
                   description, price_change_pct, volume_spike_multiplier,
                   source_links, detected_by, confirmed, created_at
            FROM market_events
            WHERE {where}
            ORDER BY start_time DESC
            LIMIT :limit
            """
        ),
        params,
    )
    rows = []
    for row in result.mappings().fetchall():
        item = dict(row)
        for k in ("start_time", "end_time", "created_at"):
            if item.get(k):
                item[k] = _iso(item[k])
        rows.append(item)
    return rows


async def data_engine_status(session: AsyncSession) -> dict[str, Any]:
    sources_result = await session.execute(
        text(
            """
            SELECT
                ds.slug,
                ds.is_active,
                MAX(ir.completed_at) AS last_ingestion,
                (
                    SELECT status FROM ingestion_runs ir2
                    WHERE ir2.source_id = ds.id
                    ORDER BY ir2.started_at DESC LIMIT 1
                ) AS last_run_status,
                (
                    SELECT COALESCE(SUM(records_inserted), 0) FROM ingestion_runs ir3
                    WHERE ir3.source_id = ds.id
                      AND ir3.started_at >= NOW() - INTERVAL '24 hours'
                ) AS records_24h,
                (
                    SELECT COUNT(*) FROM ingestion_errors ie
                    WHERE ie.source_id = ds.id
                      AND ie.created_at >= NOW() - INTERVAL '24 hours'
                ) AS errors_24h
            FROM data_sources ds
            LEFT JOIN ingestion_runs ir ON ir.source_id = ds.id
            GROUP BY ds.id, ds.slug, ds.is_active
            ORDER BY ds.slug
            """
        )
    )
    sources = []
    for row in sources_result.mappings().fetchall():
        item = dict(row)
        if item.get("last_ingestion"):
            item["last_ingestion"] = _iso(item["last_ingestion"])
        sources.append(item)

    totals = await session.execute(
        text(
            """
            SELECT
                (SELECT COUNT(*) FROM ohlcv_data)
              + (SELECT COUNT(*) FROM funding_rates)
              + (SELECT COUNT(*) FROM open_interest)
              + (SELECT COUNT(*) FROM market_snapshots) AS total_records,
                (SELECT MIN(open_time) FROM ohlcv_data) AS oldest_ohlcv
            """
        )
    )
    total_row = totals.mappings().fetchone() or {}
    return {
        "sources": sources,
        "total_records": int(total_row.get("total_records") or 0),
        "oldest_record": _iso(total_row.get("oldest_ohlcv")),
    }
