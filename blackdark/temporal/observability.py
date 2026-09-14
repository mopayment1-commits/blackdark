"""Temporal spine observability helpers."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Mapping

logger = logging.getLogger("BLACKDARK.Temporal.Spine")


@dataclass
class SpineObservability:
    stages: list[dict[str, Any]] = field(default_factory=list)

    def record(self, stage: str, status: str, **metadata: Any) -> None:
        entry = {
            "stage": stage,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            **metadata,
        }
        self.stages.append(entry)
        logger.info("temporal_spine stage=%s status=%s", stage, status, extra={"metadata": metadata})
        if stage == "failed" and status == "pit_contract":
            try:
                from blackdark.temporal.metrics import increment_temporal_metric

                code = str(metadata.get("code", ""))
                if code == "TEMPORAL_LEAKAGE_REJECTED":
                    increment_temporal_metric("temporal_leakage_violations_total")
                else:
                    increment_temporal_metric("temporal_pit_violations_total")
            except Exception:
                pass
        if stage == "persistence_event" and status == "completed":
            try:
                from blackdark.temporal.metrics import increment_temporal_metric

                increment_temporal_metric("temporal_spine_ingest_success_total")
            except Exception:
                pass

    def to_metadata(self) -> dict[str, Any]:
        return {"stages": self.stages, "stage_count": len(self.stages)}
