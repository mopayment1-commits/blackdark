"""
Canonical Data Layer (#29) — normalize, store, query reference data.

Integrated with Asset Metadata (#16). Infrastructure only — not a user surface.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any

from blackdark.canonical.registry import all_canonical_assets, registry_stats
from blackdark.canonical.resolver import resolve_asset
from blackdark.canonical.store import (
    fetch_latest_canonical_record,
    insert_canonical_record,
    sync_registry_to_db,
)
from blackdark.data.response_metadata import dataset_response

logger = logging.getLogger("BLACKDARK.CanonicalLayer")

_RETENTION_DAYS = 730  # ≥2 years policy target for canonical record store


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


class CanonicalDataLayer:
    """Collect → clean/normalize → store → query pipeline for reference data."""

    def __init__(self) -> None:
        self._bootstrapped = False

    async def bootstrap(self, *, persist: bool = True) -> dict[str, Any]:
        stats = registry_stats()
        if persist:
            sync_result = await sync_registry_to_db()
            stats = {**stats, **sync_result}
        self._bootstrapped = True
        return stats

    def normalize_payload(
        self,
        *,
        source: str,
        dataset: str,
        raw: dict[str, Any],
        asset_hint: str | None = None,
    ) -> dict[str, Any]:
        """Attach canonical asset identity to any inbound vendor payload."""
        hint = (
            asset_hint
            or raw.get("symbol")
            or raw.get("asset")
            or raw.get("base")
            or raw.get("coin_id")
            or ""
        )
        resolved = resolve_asset(str(hint))
        normalized = {
            "source": source,
            "dataset": dataset,
            "canonical_id": resolved.canonical_id,
            "symbol": resolved.symbol,
            "resolve_found": resolved.found,
            "matched_via": resolved.matched_via,
            "normalized_at": _utcnow(),
            "raw": raw,
        }
        if resolved.asset:
            normalized["reference"] = {
                "label": resolved.asset.label,
                "sector": resolved.asset.sector,
                "external_ids": resolved.asset.external_ids,
            }
        return normalized

    async def ingest(
        self,
        *,
        source: str,
        dataset: str,
        raw: dict[str, Any],
        asset_hint: str | None = None,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        if not self._bootstrapped:
            await self.bootstrap(persist=True)
        normalized = self.normalize_payload(
            source=source, dataset=dataset, raw=raw, asset_hint=asset_hint
        )
        row_id = None
        if normalized.get("canonical_id"):
            row_id = await insert_canonical_record(
                canonical_id=str(normalized["canonical_id"]),
                dataset=dataset,
                source=source,
                payload=normalized,
            )
        normalized["record_id"] = row_id
        normalized["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        return normalized

    async def query(
        self,
        *,
        input: str,
        dataset: str = "reference",
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        resolved = resolve_asset(input)
        if not resolved.canonical_id:
            return dataset_response(
                count=0,
                data=[],
                dataset=dataset,
                symbol=input,
                extra={"resolve": resolved.to_dict(), "latency_ms": 0},
            )
        latest = await fetch_latest_canonical_record(
            canonical_id=resolved.canonical_id,
            dataset=dataset,
        )
        latency = round((time.perf_counter() - t0) * 1000, 2)
        rows = [latest] if latest else []
        if resolved.asset and not latest:
            rows = [{"reference": resolved.asset.to_dict(), "synthetic": True}]
        return dataset_response(
            count=len(rows),
            data=rows,
            dataset=dataset,
            symbol=resolved.symbol,
            extra={
                "canonical_id": resolved.canonical_id,
                "resolve": resolved.to_dict(),
                "latency_ms": latency,
                "sla_met": latency <= 1000,
                "retention_policy_days": _RETENTION_DAYS,
            },
        )

    def status(self) -> dict[str, Any]:
        assets = all_canonical_assets()
        stats = registry_stats()
        return {
            "ok": True,
            "surface": "canonical_data_layer",
            "bootstrapped": self._bootstrapped,
            "asset_metadata": stats,
            "assets_loaded": len(assets),
            "retention_policy_days": _RETENTION_DAYS,
            "pipeline": ["collect", "normalize", "store", "query"],
            "timestamp": _utcnow(),
        }


@lru_cache(maxsize=1)
def get_canonical_layer() -> CanonicalDataLayer:
    return CanonicalDataLayer()
