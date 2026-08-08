"""
BLACKDARK — Automated Cold/Warm Storage Compaction (Point 39).

Scans completed hot-spool NDJSON batches and SQLite tables older than 24 hours,
writes Snappy-compressed Parquet archives under data/history/year=YYYY/month=MM/day=DD/,
verifies files on disk, and purges archived SQLite rows.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.ParquetCompactor")

SPOOL_DATE_FORMAT = "%Y-%m-%d"
SUPPORTED_RECORD_TYPES = ("pricing", "order_book", "funding", "tick")


class CompactionDisposition(StrEnum):
    ARCHIVE = "archive"
    DELETE = "delete"


@dataclass
class FileCompactionResult:
    record_type: str
    spool_path: Path
    parquet_path: Path | None = None
    rows_read: int = 0
    rows_written: int = 0
    success: bool = False
    error: str | None = None


@dataclass
class CompactionReport:
    started_at: str
    finished_at: str | None = None
    files_processed: int = 0
    files_succeeded: int = 0
    files_failed: int = 0
    rows_written: int = 0
    results: list[FileCompactionResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "files_processed": self.files_processed,
            "files_succeeded": self.files_succeeded,
            "files_failed": self.files_failed,
            "rows_written": self.rows_written,
            "results": [
                {
                    "record_type": item.record_type,
                    "spool_path": str(item.spool_path),
                    "parquet_path": str(item.parquet_path) if item.parquet_path else None,
                    "rows_read": item.rows_read,
                    "rows_written": item.rows_written,
                    "success": item.success,
                    "error": item.error,
                }
                for item in self.results
            ],
        }


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def _load_parquet_dependencies() -> tuple[Any, Any, Any]:
    try:
        import pandas as pd
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError(
            "Parquet compaction requires pandas and pyarrow. "
            "Install with: pip install pandas pyarrow"
        ) from exc
    return pd, pa, pq


def _parse_spool_date(filename: str) -> date | None:
    stem = Path(filename).stem
    try:
        return date.fromisoformat(stem)
    except ValueError:
        return None


def _flatten_record(raw: dict[str, Any], record_type: str) -> dict[str, Any] | None:
    try:
        payload = raw.get("payload") or {}
        base = {
            "timestamp": str(raw.get("timestamp") or ""),
            "exchange": str(raw.get("exchange") or ""),
            "symbol": str(raw.get("symbol") or ""),
            "record_type": str(raw.get("record_type") or record_type),
        }

        if record_type == "pricing":
            return {
                **base,
                "market_type": str(raw.get("market_type") or "spot"),
                "price": float(payload.get("price") or 0.0),
                "volume": float(payload["volume"]) if payload.get("volume") is not None else None,
                "opportunity_score": float(payload.get("opportunity_score") or 0.0),
            }

        if record_type == "order_book":
            return {
                **base,
                "market_type": str(raw.get("market_type") or "spot"),
                "bids_json": json.dumps(payload.get("bids", []), separators=(",", ":")),
                "asks_json": json.dumps(payload.get("asks", []), separators=(",", ":")),
            }

        if record_type == "funding":
            return {
                **base,
                "funding_rate": float(payload.get("funding_rate") or 0.0),
                "next_funding_time": str(payload.get("next_funding_time") or ""),
            }

        if record_type == "tick":
            return {
                **base,
                "side": str(payload.get("side") or ""),
                "price": float(payload.get("price") or 0.0),
                "quantity": float(payload.get("quantity") or 0.0),
                "notional_usd": float(payload.get("notional_usd") or 0.0),
                "trade_time_ms": int(payload.get("trade_time_ms") or 0),
            }

        return None
    except (TypeError, ValueError):
        return None


def _schema_for_record_type(record_type: str, pa: Any) -> Any:
    if record_type == "pricing":
        return pa.schema(
            [
                ("timestamp", pa.string()),
                ("exchange", pa.string()),
                ("symbol", pa.string()),
                ("record_type", pa.string()),
                ("market_type", pa.string()),
                ("price", pa.float64()),
                ("volume", pa.float64()),
                ("opportunity_score", pa.float64()),
            ]
        )

    if record_type == "order_book":
        return pa.schema(
            [
                ("timestamp", pa.string()),
                ("exchange", pa.string()),
                ("symbol", pa.string()),
                ("record_type", pa.string()),
                ("market_type", pa.string()),
                ("bids_json", pa.string()),
                ("asks_json", pa.string()),
            ]
        )

    if record_type == "funding":
        return pa.schema(
            [
                ("timestamp", pa.string()),
                ("exchange", pa.string()),
                ("symbol", pa.string()),
                ("record_type", pa.string()),
                ("funding_rate", pa.float64()),
                ("next_funding_time", pa.string()),
            ]
        )

    if record_type == "tick":
        return pa.schema(
            [
                ("timestamp", pa.string()),
                ("exchange", pa.string()),
                ("symbol", pa.string()),
                ("record_type", pa.string()),
                ("side", pa.string()),
                ("price", pa.float64()),
                ("quantity", pa.float64()),
                ("notional_usd", pa.float64()),
                ("trade_time_ms", pa.int64()),
            ]
        )

    raise ValueError(f"Unsupported record type for compaction: {record_type}")


def _read_ndjson_rows(spool_path: Path, record_type: str) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    malformed = 0

    with spool_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw = json.loads(stripped)
                flattened = _flatten_record(raw, record_type)
                if flattened is None:
                    malformed += 1
                    continue
                rows.append(flattened)
            except json.JSONDecodeError:
                malformed += 1
                logger.warning(
                    "Skipping malformed NDJSON line | file=%s line=%d",
                    spool_path,
                    line_number,
                )
            except Exception:
                malformed += 1
                logger.exception(
                    "Failed parsing NDJSON line | file=%s line=%d",
                    spool_path,
                    line_number,
                )

    if malformed:
        logger.warning(
            "NDJSON parse completed with malformed rows | file=%s malformed=%d",
            spool_path,
            malformed,
        )
    return rows, len(rows)


def _write_parquet_file(
    rows: list[dict[str, Any]],
    *,
    record_type: str,
    output_path: Path,
) -> int:
    if not rows:
        return 0

    pd, pa, pq = _load_parquet_dependencies()
    schema = _schema_for_record_type(record_type, pa)
    frame = pd.DataFrame(rows)

    for column_name, column_type in zip(schema.names, schema.types):
        if column_name not in frame.columns:
            if pa.types.is_string(column_type):
                frame[column_name] = ""
            elif pa.types.is_floating(column_type):
                frame[column_name] = 0.0
            elif pa.types.is_integer(column_type):
                frame[column_name] = 0
            else:
                frame[column_name] = None

    frame = frame[schema.names]
    table = pa.Table.from_pandas(frame, schema=schema, preserve_index=False)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, output_path, compression="snappy")
    return len(rows)


def _historical_parquet_path(
    output_root: Path,
    record_type: str,
    spool_date: date,
) -> Path:
    return (
        output_root
        / record_type
        / f"{spool_date.year:04d}"
        / f"{spool_date.month:02d}"
        / f"{spool_date.isoformat()}.parquet"
    )


def _archive_spool_file(
    spool_path: Path,
    *,
    record_type: str,
    archive_root: Path,
) -> Path:
    destination = archive_root / record_type / spool_path.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(spool_path), str(destination))
    return destination


def _dispose_spool_file(
    spool_path: Path,
    *,
    record_type: str,
    disposition: CompactionDisposition,
    archive_root: Path,
) -> None:
    if disposition == CompactionDisposition.DELETE:
        spool_path.unlink(missing_ok=True)
        return
    _archive_spool_file(spool_path, record_type=record_type, archive_root=archive_root)


def discover_completed_spool_files(
    spool_root: Path | None = None,
    *,
    cutoff_date: date | None = None,
) -> list[tuple[str, Path, date]]:
    """
    Return eligible spool files from days strictly before cutoff_date.

    Today's spool files are excluded because they may still be actively written.
    """
    root = spool_root or config.HOT_STORAGE_DIR
    cutoff = cutoff_date or _utcnow().date()
    discovered: list[tuple[str, Path, date]] = []

    if not root.exists():
        return discovered

    for record_type in SUPPORTED_RECORD_TYPES:
        type_dir = root / record_type
        if not type_dir.is_dir():
            continue

        for spool_path in sorted(type_dir.glob("*.ndjson")):
            spool_date = _parse_spool_date(spool_path.name)
            if spool_date is None:
                logger.warning("Skipping spool file with invalid date name: %s", spool_path)
                continue
            if spool_date >= cutoff:
                continue
            if not spool_path.is_file() or spool_path.stat().st_size == 0:
                continue
            discovered.append((record_type, spool_path, spool_date))

    return discovered


def compact_spool_file_sync(
    spool_path: Path,
    *,
    record_type: str,
    spool_date: date,
    output_root: Path | None = None,
    disposition: CompactionDisposition | None = None,
    archive_root: Path | None = None,
) -> FileCompactionResult:
    result = FileCompactionResult(record_type=record_type, spool_path=spool_path)

    try:
        rows, rows_read = _read_ndjson_rows(spool_path, record_type)
        result.rows_read = rows_read

        if rows_read == 0:
            result.success = True
            result.error = "empty_spool"
            _dispose_spool_file(
                spool_path,
                record_type=record_type,
                disposition=disposition or _compaction_disposition(),
                archive_root=archive_root or config.PARQUET_COMPACTION_ARCHIVE_DIR,
            )
            return result

        parquet_path = _historical_parquet_path(
            output_root or config.HISTORICAL_PARQUET_DIR,
            record_type,
            spool_date,
        )
        rows_written = _write_parquet_file(rows, record_type=record_type, output_path=parquet_path)
        result.parquet_path = parquet_path
        result.rows_written = rows_written

        _dispose_spool_file(
            spool_path,
            record_type=record_type,
            disposition=disposition or _compaction_disposition(),
            archive_root=archive_root or config.PARQUET_COMPACTION_ARCHIVE_DIR,
        )
        result.success = True
        return result
    except Exception as exc:
        result.success = False
        result.error = str(exc)
        logger.exception("Parquet compaction failed | file=%s", spool_path)
        return result


async def compact_spool_file(
    spool_path: Path,
    *,
    record_type: str,
    spool_date: date,
    output_root: Path | None = None,
    disposition: CompactionDisposition | None = None,
    archive_root: Path | None = None,
) -> FileCompactionResult:
    result = await asyncio.to_thread(
        compact_spool_file_sync,
        spool_path,
        record_type=record_type,
        spool_date=spool_date,
        output_root=output_root,
        disposition=disposition,
        archive_root=archive_root,
    )
    await _trigger_cloud_sync_safe(result)
    return result


async def _trigger_cloud_sync_safe(result: FileCompactionResult) -> None:
    if not result.success or result.parquet_path is None:
        return
    try:
        from cloud_syncer import sync_parquet_file_safe

        await sync_parquet_file_safe(result.parquet_path)
    except Exception:
        logger.exception(
            "Post-compaction cloud sync hook failed safely | file=%s",
            result.parquet_path,
        )


def _compaction_disposition() -> CompactionDisposition:
    mode = str(config.PARQUET_COMPACTION_DISPOSITION).strip().lower()
    if mode == CompactionDisposition.DELETE.value:
        return CompactionDisposition.DELETE
    return CompactionDisposition.ARCHIVE


async def run_compaction_once(
    *,
    spool_root: Path | None = None,
    output_root: Path | None = None,
    cutoff_date: date | None = None,
    disposition: CompactionDisposition | None = None,
    archive_root: Path | None = None,
) -> CompactionReport:
    """
    Compact all completed NDJSON spool files older than cutoff_date.

    Safe to invoke manually from admin tooling or the arbitrage engine scheduler.
    """
    report = CompactionReport(started_at=_utcnow_iso())
    candidates = discover_completed_spool_files(spool_root, cutoff_date=cutoff_date)

    for record_type, spool_path, spool_date in candidates:
        report.files_processed += 1
        try:
            result = await compact_spool_file(
                spool_path,
                record_type=record_type,
                spool_date=spool_date,
                output_root=output_root,
                disposition=disposition,
                archive_root=archive_root,
            )
        except Exception as exc:
            result = FileCompactionResult(
                record_type=record_type,
                spool_path=spool_path,
                success=False,
                error=str(exc),
            )
            logger.exception("Compaction worker failed | file=%s", spool_path)

        report.results.append(result)
        if result.success:
            report.files_succeeded += 1
            report.rows_written += result.rows_written
        else:
            report.files_failed += 1

    report.finished_at = _utcnow_iso()
    logger.info(
        "Parquet compaction finished | processed=%d success=%d failed=%d rows=%d",
        report.files_processed,
        report.files_succeeded,
        report.files_failed,
        report.rows_written,
    )
    return report


def next_compaction_run_utc(
    *,
    hour: int | None = None,
    minute: int | None = None,
    now: datetime | None = None,
) -> datetime:
    """Compute the next scheduled compaction timestamp in UTC."""
    current = now or _utcnow()
    run_hour = config.PARQUET_COMPACTION_HOUR_UTC if hour is None else hour
    run_minute = config.PARQUET_COMPACTION_MINUTE_UTC if minute is None else minute
    candidate = current.replace(hour=run_hour, minute=run_minute, second=0, microsecond=0)
    if current >= candidate:
        candidate += timedelta(days=1)
    return candidate


def seconds_until_next_compaction(now: datetime | None = None) -> float:
    target = next_compaction_run_utc(now=now)
    current = now or _utcnow()
    return max(0.0, (target - current).total_seconds())


class MidnightParquetCompactor:
    """Background scheduler that runs compaction once per day at midnight UTC."""

    def __init__(
        self,
        *,
        on_compaction_complete: Callable[[CompactionReport], None] | None = None,
    ) -> None:
        self._shutdown = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._on_complete = on_compaction_complete
        self._last_report: CompactionReport | None = None

    @property
    def last_report(self) -> CompactionReport | None:
        return self._last_report

    def request_shutdown(self) -> None:
        self._shutdown.set()

    async def run_once(self) -> CompactionReport:
        try:
            historical = await compact_historical_data()
            report = historical.spool_report or CompactionReport(
                started_at=historical.started_at,
                finished_at=historical.finished_at,
            )
            logger.info(
                "Scheduled historical compaction | sqlite_partitions=%d purged=%d",
                historical.partitions_written,
                historical.rows_purged,
            )
        except Exception:
            logger.exception("Scheduled historical compaction failed at top level.")
            try:
                report = await run_compaction_once()
            except Exception:
                logger.exception("Scheduled parquet compaction failed at top level.")
                report = CompactionReport(
                    started_at=_utcnow_iso(),
                    finished_at=_utcnow_iso(),
                    files_failed=1,
                )

        self._last_report = report
        if self._on_complete is not None:
            try:
                self._on_complete(report)
            except Exception:
                logger.exception("Parquet compaction completion callback failed.")
        return report

    async def run_midnight_loop(self) -> None:
        logger.info(
            "Midnight parquet compactor started | next_run_utc=%s disposition=%s",
            next_compaction_run_utc().isoformat(),
            _compaction_disposition().value,
        )

        while not self._shutdown.is_set():
            sleep_seconds = seconds_until_next_compaction()
            try:
                await asyncio.wait_for(self._shutdown.wait(), timeout=sleep_seconds)
                break
            except TimeoutError:
                pass

            if self._shutdown.is_set():
                break

            await self.run_once()

        logger.info("Midnight parquet compactor stopped.")

    def start_background(self) -> asyncio.Task[None]:
        if self._task is None or self._task.done():
            self._shutdown.clear()
            self._task = asyncio.create_task(
                self.run_midnight_loop(),
                name="midnight-parquet-compactor",
            )
        return self._task

    async def stop(self) -> None:
        self.request_shutdown()
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


_compactor: MidnightParquetCompactor | None = None


def get_parquet_compactor() -> MidnightParquetCompactor | None:
    return _compactor


async def start_midnight_compaction_scheduler() -> MidnightParquetCompactor:
    global _compactor
    if _compactor is None:
        _compactor = MidnightParquetCompactor()
    _compactor.start_background()
    return _compactor


async def stop_midnight_compaction_scheduler() -> None:
    global _compactor
    if _compactor is not None:
        await _compactor.stop()
        _compactor = None


# ── SQLite historical compaction (Cold/Warm storage) ─────────────────────────

@dataclass
class HistoricalDatasetResult:
    dataset: str
    partition_date: date
    parquet_path: Path | None = None
    rows_read: int = 0
    rows_written: int = 0
    rows_purged: int = 0
    success: bool = False
    error: str | None = None


@dataclass
class HistoricalCompactionReport:
    started_at: str
    finished_at: str | None = None
    cutoff_iso: str = ""
    datasets_processed: int = 0
    partitions_written: int = 0
    partitions_failed: int = 0
    rows_written: int = 0
    rows_purged: int = 0
    spool_report: CompactionReport | None = None
    dataset_results: list[HistoricalDatasetResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "cutoff_iso": self.cutoff_iso,
            "datasets_processed": self.datasets_processed,
            "partitions_written": self.partitions_written,
            "partitions_failed": self.partitions_failed,
            "rows_written": self.rows_written,
            "rows_purged": self.rows_purged,
            "spool_report": self.spool_report.to_dict() if self.spool_report else None,
            "dataset_results": [
                {
                    "dataset": item.dataset,
                    "partition_date": item.partition_date.isoformat(),
                    "parquet_path": str(item.parquet_path) if item.parquet_path else None,
                    "rows_read": item.rows_read,
                    "rows_written": item.rows_written,
                    "rows_purged": item.rows_purged,
                    "success": item.success,
                    "error": item.error,
                }
                for item in self.dataset_results
            ],
        }


def _history_parquet_path(
    dataset: str,
    partition_date: date,
    *,
    output_root: Path | None = None,
) -> Path:
    root = output_root or config.HISTORY_PARQUET_DIR
    return (
        root
        / dataset
        / f"year={partition_date.year:04d}"
        / f"month={partition_date.month:02d}"
        / f"day={partition_date.day:02d}"
        / f"{dataset}.parquet"
    )


def _parse_db_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _group_rows_by_partition_date(rows: list[dict[str, Any]]) -> dict[date, list[dict[str, Any]]]:
    grouped: dict[date, list[dict[str, Any]]] = {}
    for row in rows:
        parsed = _parse_db_timestamp(row.get("timestamp"))
        if parsed is None:
            continue
        partition_date = parsed.astimezone(UTC).date()
        grouped.setdefault(partition_date, []).append(row)
    return grouped


def _verify_parquet_file(parquet_path: Path, expected_rows: int) -> bool:
    if expected_rows <= 0:
        return parquet_path.exists()
    try:
        _, _, pq = _load_parquet_dependencies()
        metadata = pq.read_metadata(parquet_path)
        return metadata.num_rows == expected_rows
    except Exception:
        logger.exception("Parquet verification failed | file=%s", parquet_path)
        return False


def _merge_parquet_files(
    existing_path: Path,
    new_rows: list[dict[str, Any]],
    output_path: Path,
) -> tuple[int, int]:
    pd, pa, pq = _load_parquet_dependencies()
    new_frame = pd.DataFrame(new_rows)
    if existing_path.exists():
        existing_frame = pd.read_parquet(existing_path)
        frame = pd.concat([existing_frame, new_frame], ignore_index=True)
    else:
        frame = new_frame
    output_path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(table, output_path, compression="snappy")
    return len(new_rows), len(frame)


def _write_sqlite_partition_sync(
    dataset: str,
    partition_date: date,
    rows: list[dict[str, Any]],
    *,
    output_root: Path | None = None,
) -> HistoricalDatasetResult:
    result = HistoricalDatasetResult(dataset=dataset, partition_date=partition_date)
    result.rows_read = len(rows)
    if not rows:
        result.success = True
        return result

    parquet_path = _history_parquet_path(dataset, partition_date, output_root=output_root)
    temp_path = parquet_path.with_suffix(".parquet.tmp")

    try:
        rows_added, total_rows = _merge_parquet_files(parquet_path, rows, temp_path)
        if not _verify_parquet_file(temp_path, total_rows):
            raise RuntimeError(
                f"Parquet verification failed for {dataset} {partition_date.isoformat()}"
            )
        temp_path.replace(parquet_path)
        result.parquet_path = parquet_path
        result.rows_written = rows_added
        result.success = True
        return result
    except Exception as exc:
        result.success = False
        result.error = str(exc)
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        logger.exception(
            "SQLite partition compaction failed | dataset=%s date=%s",
            dataset,
            partition_date,
        )
        return result


async def _purge_archived_rows(dataset: str, rows: list[dict[str, Any]]) -> int:
    row_ids = [int(row["id"]) for row in rows if row.get("id") is not None]
    if not row_ids:
        return 0
    try:
        from database import (
            delete_order_books_by_ids,
            delete_pricing_logs_by_ids,
            delete_sentiment_logs_by_ids,
        )

        if dataset == "pricing_logs":
            return await delete_pricing_logs_by_ids(row_ids)
        if dataset == "order_books":
            return await delete_order_books_by_ids(row_ids)
        if dataset == "market_sentiment_logs":
            return await delete_sentiment_logs_by_ids(row_ids)
    except Exception:
        logger.exception("SQLite purge failed | dataset=%s rows=%d", dataset, len(row_ids))
    return 0


async def _compact_sqlite_dataset_once(
    dataset: str,
    *,
    cutoff_iso: str,
    output_root: Path | None = None,
) -> list[HistoricalDatasetResult]:
    from database import (
        fetch_archivable_order_books,
        fetch_archivable_pricing_logs,
        fetch_archivable_sentiment_logs,
    )

    fetchers = {
        "pricing_logs": fetch_archivable_pricing_logs,
        "order_books": fetch_archivable_order_books,
        "market_sentiment_logs": fetch_archivable_sentiment_logs,
    }
    fetcher = fetchers.get(dataset)
    if fetcher is None:
        return []

    results: list[HistoricalDatasetResult] = []
    rows = await fetcher(cutoff_iso)
    if not rows:
        return results

    grouped = _group_rows_by_partition_date(rows)
    for partition_date, partition_rows in sorted(grouped.items()):
        compact_result = await asyncio.to_thread(
            _write_sqlite_partition_sync,
            dataset,
            partition_date,
            partition_rows,
            output_root=output_root,
        )
        if compact_result.success:
            purged = await _purge_archived_rows(dataset, partition_rows)
            compact_result.rows_purged = purged
        results.append(compact_result)
    return results


async def compact_sqlite_historical_data(
    *,
    min_age_hours: int | None = None,
    output_root: Path | None = None,
) -> HistoricalCompactionReport:
    """Export and purge SQLite rows older than the configured retention window."""
    from database import compaction_cutoff_iso

    report = HistoricalCompactionReport(
        started_at=_utcnow_iso(),
        cutoff_iso=compaction_cutoff_iso(min_age_hours),
    )

    if not config.SQLITE_HISTORICAL_COMPACTION_ENABLED:
        report.finished_at = _utcnow_iso()
        return report

    datasets = ("pricing_logs", "order_books", "market_sentiment_logs")
    for dataset in datasets:
        report.datasets_processed += 1
        try:
            while True:
                chunk_results = await _compact_sqlite_dataset_once(
                    dataset,
                    cutoff_iso=report.cutoff_iso,
                    output_root=output_root,
                )
                if not chunk_results:
                    break
                for item in chunk_results:
                    report.dataset_results.append(item)
                    if item.success:
                        report.partitions_written += 1
                        report.rows_written += item.rows_written
                        report.rows_purged += item.rows_purged
                        if item.parquet_path is not None:
                            await _trigger_cloud_sync_safe(
                                FileCompactionResult(
                                    record_type=dataset,
                                    spool_path=item.parquet_path,
                                    parquet_path=item.parquet_path,
                                    rows_written=item.rows_written,
                                    success=True,
                                )
                            )
                    else:
                        report.partitions_failed += 1
                        break
                if any(not item.success for item in chunk_results):
                    break
        except Exception:
            logger.exception("SQLite historical compaction failed | dataset=%s", dataset)
            report.partitions_failed += 1

    report.finished_at = _utcnow_iso()
    logger.info(
        "SQLite historical compaction finished | partitions=%d failed=%d rows=%d purged=%d",
        report.partitions_written,
        report.partitions_failed,
        report.rows_written,
        report.rows_purged,
    )
    return report


async def compact_historical_data(
    *,
    min_age_hours: int | None = None,
    include_spool: bool = True,
    output_root: Path | None = None,
    spool_output_root: Path | None = None,
) -> HistoricalCompactionReport:
    """
    Compact pricing logs, order books, and sentiment logs older than 24 hours.

    Also compacts completed hot-spool NDJSON when include_spool=True.
    """
    sqlite_report = await compact_sqlite_historical_data(
        min_age_hours=min_age_hours,
        output_root=output_root or config.HISTORY_PARQUET_DIR,
    )

    if include_spool and config.PARQUET_COMPACTION_ENABLED:
        try:
            sqlite_report.spool_report = await run_compaction_once(
                output_root=spool_output_root or config.HISTORICAL_PARQUET_DIR,
            )
        except Exception:
            logger.exception("Hot-spool compaction failed during historical cycle.")

    return sqlite_report


_background_compaction_task: asyncio.Task[HistoricalCompactionReport] | None = None
_last_background_compaction_at: float = 0.0


async def _run_compaction_background_worker() -> HistoricalCompactionReport:
    try:
        return await compact_historical_data()
    except Exception:
        logger.exception("Background historical compaction failed at top level.")
        return HistoricalCompactionReport(
            started_at=_utcnow_iso(),
            finished_at=_utcnow_iso(),
            partitions_failed=1,
        )


def trigger_historical_compaction_background() -> asyncio.Task[HistoricalCompactionReport] | None:
    """
    Fire-and-forget compaction trigger that does not block the arbitrage loop.
    """
    global _background_compaction_task, _last_background_compaction_at

    now = asyncio.get_running_loop().time()
    if (now - _last_background_compaction_at) < config.COMPACTION_BACKGROUND_COOLDOWN_SECONDS:
        return _background_compaction_task

    if _background_compaction_task is not None and not _background_compaction_task.done():
        return _background_compaction_task

    _last_background_compaction_at = now
    _background_compaction_task = asyncio.create_task(
        _run_compaction_background_worker(),
        name="historical-compaction-background",
    )
    return _background_compaction_task


async def run_midnight_compaction_loop() -> None:
    """Convenience entrypoint for standalone execution."""
    compactor = MidnightParquetCompactor()
    try:
        await compactor.run_midnight_loop()
    finally:
        compactor.request_shutdown()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    try:
        asyncio.run(run_midnight_compaction_loop())
    except KeyboardInterrupt:
        logger.info("Parquet compactor shutdown complete.")


if __name__ == "__main__":
    main()
