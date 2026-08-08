"""Grid trading bot — free-tier paper grid engine."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.GridBot")

_STORE = config.DATA_DIR / "grid_bots.json"


def _load() -> list[dict[str, Any]]:
    if not _STORE.exists():
        return []
    try:
        return json.loads(_STORE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    _STORE.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def list_grids() -> dict[str, Any]:
    return {"grids": _load(), "count": len(_load())}


def create_grid(
    *,
    asset: str,
    lower_price: float,
    upper_price: float,
    grids: int = 10,
    quote_usd: float = 1000,
) -> dict[str, Any]:
    if lower_price >= upper_price or grids < 2:
        raise ValueError("Invalid grid parameters")
    step = (upper_price - lower_price) / grids
    levels = [round(lower_price + i * step, 8) for i in range(grids + 1)]
    bot = {
        "id": f"grid_{asset}_{int(datetime.now(UTC).timestamp())}",
        "asset": asset.upper(),
        "lower_price": lower_price,
        "upper_price": upper_price,
        "grids": grids,
        "levels": levels,
        "quote_usd": quote_usd,
        "mode": "paper",
        "created_at": datetime.now(UTC).isoformat(),
    }
    rows = _load()
    rows.append(bot)
    _save(rows)
    return bot
