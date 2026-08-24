"""SQLAlchemy declarative models for Wave 01 data engine."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    rate_limit_rps: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("data_sources.id"))
    run_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="running")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_fetched: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_deduped: Mapped[int] = mapped_column(Integer, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, default=0)
    params: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    error_log: Mapped[str | None] = mapped_column(Text)
    triggered_by: Mapped[str] = mapped_column(String(64), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class OhlcvData(Base):
    __tablename__ = "ohlcv_data"
    __table_args__ = (
        UniqueConstraint("source_id", "symbol", "interval", "open_time", name="ohlcv_data_source_id_symbol_interval_open_time_key"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("data_sources.id"))
    ingestion_run_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("ingestion_runs.id"))
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    quote_asset: Mapped[str] = mapped_column(String(16), nullable=False)
    interval: Mapped[str] = mapped_column(String(8), nullable=False)
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open_price: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    high_price: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    low_price: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(36, 18), nullable=False)
    quote_volume: Mapped[Decimal | None] = mapped_column(Numeric(36, 18))
    trades_count: Mapped[int | None] = mapped_column(Integer)
    taker_buy_base_volume: Mapped[Decimal | None] = mapped_column(Numeric(36, 18))
    taker_buy_quote_volume: Mapped[Decimal | None] = mapped_column(Numeric(36, 18))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    provenance_hash: Mapped[str | None] = mapped_column(String(64))
