"""
Historical flat file archive (#66) — silent backtest infrastructure.

Partitioned OHLCV/tick archives with checksum manifests.
Users see "Backtest 2+ years" — not flat file branding.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.HistoricalFlatArchive")

ARCHIVE_ROOT = Path("data/archive")
MANIFEST_PATH = ARCHIVE_ROOT / "manifest.json"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def partition_path(*, dataset: str, symbol: str, interval: str, date: str) -> Path:
    """Archive path: data/archive/{dataset}/{symbol}/{interval}/{date}.jsonl"""
    safe_sym = symbol.upper().replace("/", "_")
    return ARCHIVE_ROOT / dataset / safe_sym / interval / f"{date}.jsonl"


def write_partition(
    *,
    dataset: str,
    symbol: str,
    interval: str,
    date: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    path = partition_path(dataset=dataset, symbol=symbol, interval=interval, date=date)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, default=str) + "\n")
    checksum = _sha256_file(path)
    entry = {
        "dataset": dataset,
        "symbol": symbol.upper(),
        "interval": interval,
        "date": date,
        "path": str(path),
        "row_count": len(rows),
        "sha256": checksum,
        "bytes": path.stat().st_size,
        "written_at": _utcnow(),
    }
    _upsert_manifest_entry(entry)
    return entry


def _upsert_manifest_entry(entry: dict[str, Any]) -> None:
    manifest = load_manifest()
    files = manifest.get("files") or []
    key = (entry["dataset"], entry["symbol"], entry["interval"], entry["date"])
    files = [f for f in files if (f.get("dataset"), f.get("symbol"), f.get("interval"), f.get("date")) != key]
    files.append(entry)
    manifest["files"] = files
    manifest["updated_at"] = _utcnow()
    manifest["file_count"] = len(files)
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def load_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return {"version": 1, "files": [], "file_count": 0, "updated_at": None}
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "files": [], "file_count": 0, "updated_at": None, "corrupt": True}


def verify_manifest() -> dict[str, Any]:
    """Verify checksums for all manifest entries."""
    manifest = load_manifest()
    files = manifest.get("files") or []
    verified = 0
    failed: list[dict[str, Any]] = []
    for entry in files:
        path = Path(entry.get("path") or "")
        if not path.exists():
            failed.append({**entry, "reason": "missing_file"})
            continue
        actual = _sha256_file(path)
        if actual != entry.get("sha256"):
            failed.append({**entry, "reason": "checksum_mismatch", "actual_sha256": actual})
            continue
        verified += 1
    return {
        "ok": len(failed) == 0,
        "feature": "#66",
        "verified": verified,
        "failed": failed,
        "total": len(files),
        "timestamp": _utcnow(),
    }


def backtest_coverage_years(*, symbol: str = "BTC", interval: str = "1d") -> dict[str, Any]:
    """How many years of archived OHLCV are available for backtests."""
    sym = symbol.upper()
    manifest = load_manifest()
    dates: list[str] = []
    for entry in manifest.get("files") or []:
        if entry.get("dataset") != "ohlcv":
            continue
        if entry.get("symbol") != sym:
            continue
        if entry.get("interval") != interval:
            continue
        dates.append(str(entry.get("date")))
    dates = sorted(set(dates))
    years = round(len(dates) / 365, 2) if dates else 0.0
    return {
        "ok": bool(dates),
        "feature": "#66",
        "symbol": sym,
        "interval": interval,
        "partition_count": len(dates),
        "years_available": years,
        "meets_2y_backtest": years >= 2.0,
        "user_facing_note": f"Backtest {years:.1f}+ years" if years else "Backtest history building",
        "data_state": "LIVE" if dates else "MISSING",
        "missing_not_zero": True,
    }


async def snapshot_ohlcv_partition(symbol: str, *, interval: str = "1d") -> dict[str, Any]:
    """Fetch recent OHLCV and write a dated partition (ingestion hook)."""
    import aiohttp

    pair = f"{symbol.upper()}USDT"
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": pair, "interval": interval, "limit": 100}
    timeout = aiohttp.ClientTimeout(total=5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return {"ok": False, "error": f"http_{resp.status}"}
                raw = await resp.json()
    except (aiohttp.ClientError, TimeoutError) as exc:
        return {"ok": False, "error": str(exc)}

    rows = []
    for r in raw or []:
        if not isinstance(r, list) or len(r) < 6:
            continue
        rows.append(
            {
                "open_time": int(r[0]),
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
            }
        )
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    entry = write_partition(dataset="ohlcv", symbol=symbol, interval=interval, date=date, rows=rows)
    return {"ok": True, "partition": entry, "row_count": len(rows)}
