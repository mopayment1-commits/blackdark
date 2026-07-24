"""Simple whale detection stub for quick API testing."""

from __future__ import annotations

import asyncio
from typing import Any


async def detect_whale(symbol: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "whale_score": 75,
        "alert": "Large buy detected",
    }


if __name__ == "__main__":
    print("Done")
