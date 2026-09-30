"""From-scratch domain execution — v6 deepest meaning (semantic backend + goal payload + evidence)."""

from __future__ import annotations

import time
from typing import Any

from cap646.dedicated_common import wrap
from cap646.evidence_class import ai_compliance_footer


async def execute_from_scratch(
    capability_id: int,
    *,
    expected_surface: dict[int, str],
    symbol: str,
    address: str,
    params: dict[str, Any],
    payload_key: str,
    capability_name: str,
    track: str = "T04",
) -> dict[str, Any]:
    from cap646.batch_dedicated_invoke import invoke_semantic_backend
    from data_provenance_score import compute_data_provenance_score

    merged = dict(params or {})
    merged.setdefault("symbol", symbol)
    merged.setdefault("address", address)

    t0 = time.perf_counter()
    domain_result = await invoke_semantic_backend(capability_id, params=merged)
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    goal_payload: dict[str, Any] = {
        "capability_name": capability_name,
        "track": track,
        "domain_result": domain_result,
        "execution_path": "v6_from_scratch_semantic_domain",
        "provenance": prov,
        "freshness_class": prov.get("freshness_class"),
        "lineage": f"catalog→semantic→{payload_key}",
    }
    if isinstance(domain_result, dict):
        for key in (
            "leaderboard",
            "metrics",
            "alerts",
            "data",
            "result",
            "analysis",
            "report",
            "score",
            "status",
        ):
            if key in domain_result:
                goal_payload[f"goal_{key}"] = domain_result[key]

    body = wrap(
        capability_id,
        expected_surface=expected_surface,
        symbol=symbol,
        payload_key=payload_key,
        payload=goal_payload,
        extra={
            "latency_ms": latency_ms,
            "performance_gate": True,
            "data_provenance": prov,
            "binding_path": "from_scratch_semantic_domain",
            "build_method": "v6_from_scratch",
        },
    )
    return ai_compliance_footer(body)
