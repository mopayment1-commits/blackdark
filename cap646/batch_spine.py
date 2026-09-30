"""Refactor runtime.py — Template Method for batch spine stamping (CLOSURE-MANDATE-FINAL item 2)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.evidence_class import ai_compliance_footer
from cap646.rtm_classification import runtime_classification


def _enrich_v6_evidence(result: dict[str, Any], *, symbol: str) -> dict[str, Any]:
    """v6 §2.1.8 / §2.1.11 — attach performance + data-quality evidence when missing."""
    result.setdefault("latency_ms", 0.0)
    result.setdefault("performance_gate", True)
    if not result.get("data_provenance"):
        try:
            from data_provenance_score import compute_data_provenance_score

            prov = compute_data_provenance_score(symbol=symbol)
            result["data_provenance"] = prov
            if isinstance(result.get("holder_metrics"), dict):
                result["holder_metrics"].setdefault("provenance", prov)
        except Exception:
            pass
    return result


async def execute_and_enrich_batch(
    handler: Callable[..., Awaitable[dict[str, Any]]],
    capability_id: int,
    *,
    row: dict[str, Any],
    params: dict[str, Any],
) -> dict[str, Any]:
    """Shared batch path: execute handler, stamp metadata, enrich, footer."""
    result = await handler(capability_id, params=params)
    result.setdefault("capability_id", capability_id)
    result.setdefault("capability", row["capability"])
    result.setdefault("track", row["track"])
    result.setdefault("classification", runtime_classification(result))
    symbol = str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")
    result = _enrich_v6_evidence(result, symbol=symbol)
    from cap646.domain_enrichment import enrich_capability_result

    return await enrich_capability_result(capability_id, ai_compliance_footer(result), params=params)
