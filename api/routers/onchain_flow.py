"""On-chain flow classification API (D-09)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from exchange_internal_flow_filter import classify_flow

router = APIRouter(prefix="/api/v1/onchain", tags=["onchain-flow-d09"])


@router.get("/flow-classification")
async def flow_classification(
    from_address: str = Query(..., alias="from"),
    to_address: str = Query(..., alias="to"),
    exchange: str | None = None,
    amount_usd: float | None = None,
    is_deposit: bool = False,
    is_withdrawal: bool = False,
    graph_hops: int = Query(0, ge=0, le=20),
):
    return classify_flow(
        from_address=from_address,
        to_address=to_address,
        exchange=exchange,
        amount_usd=amount_usd,
        is_deposit=is_deposit,
        is_withdrawal=is_withdrawal,
        graph_hops=graph_hops,
    )
