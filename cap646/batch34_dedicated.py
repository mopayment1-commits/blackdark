"""Official Batch 34 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 34 (IDs 826–826).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH34_IDS: frozenset[int] = frozenset(range(826, 827))
BATCH34_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH34_DEDICATED_IDS: frozenset[int] = frozenset({826})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

EXPECTED_SURFACE: dict[int, str] = {
    826: "tradfi_context",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap826(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        826,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="tradfi_context",
        params=params,
    )

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
        overlap_error="batch01 overlap for batch34",
        not_dedicated_error=f"batch34: not a dedicated capability",
    )
