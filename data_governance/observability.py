"""Data operations observability (DIG-042)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("BLACKDARK.DataGovernance")


def emit_governance_event(surface: str, payload: dict[str, Any]) -> None:
    logger.info(
        "governance_material_write",
        extra={
            "surface": surface,
            "source_id": payload.get("source_id") or payload.get("source"),
            "symbol": payload.get("symbol") or payload.get("asset"),
        },
    )
