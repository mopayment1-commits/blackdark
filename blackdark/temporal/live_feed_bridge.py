"""Bridge Wave01 live ingest rows into the production temporal spine."""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime
from typing import Any, Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from blackdark.temporal.metrics import increment_temporal_metric
from blackdark.temporal.normalization import build_observation_dict, build_provenance_dict
from blackdark.temporal.production_spine import ProductionSpineRequest, run_production_temporal_spine

logger = logging.getLogger("BLACKDARK.Temporal.LiveFeed")


def live_feed_enabled() -> bool:
    return os.getenv("TEMPORAL_LIVE_FEED_ENABLED", "true").strip().lower() in {"1", "true", "yes"}


def _iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


async def bridge_ohlcv_row_to_temporal_spine(
    session: AsyncSession,
    row: Mapping[str, Any],
    *,
    source_slug: str,
    source_record_id: str,
    ingestion_run_id: str | None = None,
) -> dict[str, Any] | None:
    """Map one newly inserted OHLCV row into run_production_temporal_spine."""
    if not live_feed_enabled():
        return None

    symbol = str(row["symbol"]).upper()
    interval = str(row.get("interval") or "1h")
    close_time = row["close_time"]
    if not isinstance(close_time, datetime):
        return None

    close_iso = _iso(close_time)
    ingested_at = datetime.now(UTC)
    observation = build_observation_dict(
        event_time=close_iso,
        observed_time=close_iso,
        available_at=close_iso,
        ingested_at=_iso(ingested_at),
        effective_at=close_iso,
        revised_at=close_iso,
    )
    provenance = build_provenance_dict(
        source=source_slug,
        source_version="live-v1",
        dataset_version=f"{source_slug}-ohlcv-{interval}",
        rights_or_provenance={
            "permitted_purpose": "live_market_observation",
            "ingestion_run_id": ingestion_run_id,
            "source_record_id": source_record_id,
        },
    )
    idempotency_key = f"live-{source_slug}-{symbol}-{interval}-{close_iso}"

    result = await run_production_temporal_spine(
        session,
        ProductionSpineRequest(
            ingestion_payload={
                "entity_key": symbol,
                "event_type": f"ohlcv_{interval}",
                "payload": {
                    "open": str(row.get("open")),
                    "high": str(row.get("high")),
                    "low": str(row.get("low")),
                    "close": str(row.get("close")),
                    "volume": str(row.get("volume")),
                    "interval": interval,
                    "source_record_id": source_record_id,
                },
                "observation": observation,
                "provenance": provenance,
            },
            simulated_time=close_time.astimezone(UTC) if close_time.tzinfo else close_time.replace(tzinfo=UTC),
            prediction={"close": str(row.get("close")), "symbol": symbol},
            confidence=0.5,
            abstention_state="observe",
            subject_identity=symbol,
            input_identity=source_record_id,
            model_version="live-feed-v1",
            dataset_version=f"{source_slug}-ohlcv-{interval}",
            idempotency_key=idempotency_key,
            uses_simulated_time=False,
            live_forward_passage_confirmed=False,
        ),
    )
    if result.status == "completed":
        increment_temporal_metric("temporal_live_feed_ingest_total")
    return result.to_metadata()


async def try_bridge_ohlcv_row(
    session: AsyncSession,
    row: Mapping[str, Any],
    *,
    source_slug: str,
    source_record_id: str,
    ingestion_run_id: str | None = None,
) -> dict[str, Any] | None:
    try:
        return await bridge_ohlcv_row_to_temporal_spine(
            session,
            row,
            source_slug=source_slug,
            source_record_id=source_record_id,
            ingestion_run_id=ingestion_run_id,
        )
    except Exception as exc:
        logger.warning("Temporal live-feed bridge failed for %s: %s", source_slug, exc)
        return None
