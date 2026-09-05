"""Refactor runtime.py — Template Method for batch spine stamping (CLOSURE-MANDATE-FINAL item 2)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.evidence_class import ai_compliance_footer
from cap646.rtm_classification import runtime_classification


async def execute_and_enrich_batch(
    handler: Callable[..., Awaitable[dict[str, Any]]],
    capability_id: int,
    *,
    row: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, Any]:
    """Shared batch path: execute handler, stamp metadata, enrich, footer."""
    try:
        result = await handler(capability_id, params=params)
    except Exception as exc:
        result = {
            "success": False,
            "error": str(exc),
            "handler": getattr(handler, "__name__", "unknown"),
        }
    result.setdefault("capability_id", capability_id)
    result.setdefault("capability", row["capability"])
    result.setdefault("track", row["track"])
    result.setdefault("classification", runtime_classification(result))
    from cap646.domain_enrichment import enrich_capability_result

    return await enrich_capability_result(capability_id, ai_compliance_footer(result), params=params)
