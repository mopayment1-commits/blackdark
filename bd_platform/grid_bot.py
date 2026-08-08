"""Grid trading bot — free-tier paper grid engine."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.GridBot")

# Fixed store path (never derived from request/env user input).
_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "grid_bots.json"
_ASSET_RE = re.compile(r"^[A-Z0-9]{2,16}$")


def _safe_asset(asset: str) -> str:
    cleaned = str(asset).strip().upper()
    if not _ASSET_RE.fullmatch(cleaned):
        raise ValueError("Invalid asset symbol")
    return cleaned


def _load() -> list[dict[str, Any]]:
    if not _STORE_PATH.exists():
        return []
    try:
        return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, indent=2)
    _STORE_PATH.write_text(payload, encoding="utf-8")


def list_grids() -> dict[str, Any]:
    rows = _load()
    return {"grids": rows, "count": len(rows)}


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
    safe_asset = _safe_asset(asset)
    step = (upper_price - lower_price) / grids
    levels = [round(lower_price + i * step, 8) for i in range(grids + 1)]
    bot = {
        "id": f"grid_{safe_asset}_{int(datetime.now(UTC).timestamp())}",
        "asset": safe_asset,
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
