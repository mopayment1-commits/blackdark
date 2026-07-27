"""Repository layer — oracle predictions (thin wrapper over database)."""

from __future__ import annotations

from typing import Any

from database import fetch_labeled_oracle_predictions, insert_oracle_prediction


async def insert_prediction(
    asset: str,
    price_at_prediction: float,
    verdict: str,
    opportunity_score: int,
    confidence: int,
    **kwargs: Any,
) -> int:
    return await insert_oracle_prediction(
        asset,
        price_at_prediction,
        verdict,
        opportunity_score,
        confidence,
        **kwargs,
    )


async def fetch_labeled(*, limit: int = 500, include_synthetic: bool = False) -> list[dict[str, Any]]:
    return await fetch_labeled_oracle_predictions(limit=limit, include_synthetic=include_synthetic)
