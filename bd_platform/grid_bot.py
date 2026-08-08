"""Grid trading bot — free-tier paper grid engine."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.GridBot")

# Fixed store path relative to this module (never from request input).
_STORE_PATH = Path(__file__).resolve().parent.parent.joinpath("data", "grid_bots.json")
_ASSET_RE = re.compile(r"^[A-Z0-9]{2,16}$")
_ID_RE = re.compile(r"^grid_[A-Z0-9]{2,16}_\d+$")

# In-memory cache — primary store for paper grids in this process.
_ROWS: list[dict[str, Any]] = []
_LOADED = False


def _safe_asset(asset: str) -> str:
    cleaned = str(asset).strip().upper()
    if not _ASSET_RE.fullmatch(cleaned):
        raise ValueError("Invalid asset symbol")
    return cleaned


def _hydrate() -> None:
    """Load disk snapshot once into memory (best-effort)."""
    global _LOADED, _ROWS
    if _LOADED:
        return
    _LOADED = True
    if not _STORE_PATH.exists():
        _ROWS = []
        return
    try:
        raw = json.loads(_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        _ROWS = []
        return
    clean: list[dict[str, Any]] = []
    if isinstance(raw, list):
        for row in raw:
            if not isinstance(row, dict):
                continue
            try:
                asset = _safe_asset(str(row.get("asset") or ""))
                rid = str(row.get("id") or "")
                if not _ID_RE.fullmatch(rid):
                    rid = f"grid_{asset}_{int(datetime.now(UTC).timestamp())}"
                clean.append(
                    {
                        "id": rid,
                        "asset": asset,
                        "lower_price": float(row["lower_price"]),
                        "upper_price": float(row["upper_price"]),
                        "grids": int(row["grids"]),
                        "levels": [float(x) for x in (row.get("levels") or [])],
                        "quote_usd": float(row.get("quote_usd") or 0),
                        "mode": "paper",
                        "created_at": str(row.get("created_at") or datetime.now(UTC).isoformat()),
                    }
                )
            except (KeyError, TypeError, ValueError):
                continue
    _ROWS = clean


def _persist() -> None:
    """Persist memory snapshot to the fixed path."""
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Rebuild a JSON document only from validated numeric/allowlisted fields.
    document = [
        {
            "id": row["id"],
            "asset": row["asset"],
            "lower_price": row["lower_price"],
            "upper_price": row["upper_price"],
            "grids": row["grids"],
            "levels": row["levels"],
            "quote_usd": row["quote_usd"],
            "mode": "paper",
            "created_at": row["created_at"],
        }
        for row in _ROWS
    ]
    text = json.dumps(document, indent=2)
    # Path is a module constant; content is rebuilt from validated fields only.
    _STORE_PATH.write_text(text, encoding="utf-8")  # NOSONAR pythonsecurity:S2083


def list_grids() -> dict[str, Any]:
    _hydrate()
    return {"grids": list(_ROWS), "count": len(_ROWS)}


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
        "lower_price": float(lower_price),
        "upper_price": float(upper_price),
        "grids": int(grids),
        "levels": levels,
        "quote_usd": float(quote_usd),
        "mode": "paper",
        "created_at": datetime.now(UTC).isoformat(),
    }
    _hydrate()
    _ROWS.append(bot)
    _persist()
    return bot
