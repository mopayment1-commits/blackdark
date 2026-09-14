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

    def to_metadata(self) -> dict[str, Any]:
        return {"stages": self.stages, "stage_count": len(self.stages)}
