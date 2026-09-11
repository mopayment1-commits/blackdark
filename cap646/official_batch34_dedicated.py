"""Official batch 34 — v6 substantive handlers (IDs 826–826)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import exchange_netflow_footer
from cap646.dedicated_common import exchange_netflow_probe
from cap646.dedicated_common import holder_analytics_bundle
from cap646.dedicated_common import holder_analytics_footer
from cap646.dedicated_common import holder_analytics_locked
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import seed as _seed
from cap646.dedicated_common import sym as _sym
from cap646.evidence_class import ai_compliance_footer
from cap646.evidence_class import attach_evidence_metadata, infer_evidence_class

OFFICIAL_BATCH34_IDS: frozenset[int] = frozenset(range(826, 827))
BATCH34_DEDICATED_IDS: frozenset[int] = frozenset({826})
BATCH34_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    826: "tradfi_context",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap826(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'market_context',
        'probe_price_sources',
        symbol=symbol,
        address=address,
        params=params,
        param_style='symbol',
        capability_id=826,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "TradFi Context",
        "track": "T19",
        "tradfi_context": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(826, symbol=symbol, payload_key='tradfi_context', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    826: _cap826,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH34_DEDICATED_IDS,
        overlap_batch01_ids=BATCH34_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap batch34",
        not_dedicated_error=f"official batch34: not dedicated",
    )
