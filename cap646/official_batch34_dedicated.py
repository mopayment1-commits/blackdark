"""Official batch 34 — from-scratch dedicated backends (IDs 826–826)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH34_IDS: frozenset[int] = frozenset(range(826, 827))
BATCH34_DEDICATED_IDS: frozenset[int] = frozenset({826})
BATCH34_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    826: "tradfi_context",
}

async def _cap826(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch34_dedicated import _cap826 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

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
        overlap_error="batch01 overlap for official batch34",
        not_dedicated_error=f"official batch34: not dedicated",
    )
