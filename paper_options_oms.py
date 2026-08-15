"""
BLACKDARK — Paper Options OMS (honest paper desk, not live venue FILL).

Closes MKT-OPT / EX-OMS journeys without claiming live money execution.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import config

_STORE = Path(getattr(config, "DATA_DIR", Path("data"))) / "options_oms.jsonl"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _append(row: dict[str, Any]) -> None:
    _STORE.parent.mkdir(parents=True, exist_ok=True)
    with _STORE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def _read_all(limit: int = 200) -> list[dict[str, Any]]:
    if not _STORE.exists():
        return []
    rows: list[dict[str, Any]] = []
    with _STORE.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-limit:]


def create_paper_order(
    *,
    user_email: str,
    asset: str = "BTC",
    side: str = "buy",
    option_type: str = "call",
    quantity: float = 1.0,
    limit_price: float | None = None,
) -> dict[str, Any]:
    order = {
        "id": f"oms_{uuid.uuid4().hex[:12]}",
        "mode": "paper",
        "live_fill": False,
        "user_email": user_email,
        "asset": str(asset).upper(),
        "side": str(side).lower(),
        "option_type": str(option_type).lower(),
        "quantity": float(quantity),
        "limit_price": limit_price,
        "status": "filled_paper",
        "filled_at": _utcnow(),
        "created_at": _utcnow(),
        "note": "Paper OMS fill — not a live venue FILL. Not financial advice.",
    }
    _append(order)
    return order


def list_paper_orders(*, user_email: str | None = None, limit: int = 50) -> dict[str, Any]:
    rows = _read_all(limit=500)
    if user_email:
        rows = [r for r in rows if r.get("user_email") == user_email]
    rows = rows[-limit:]
    return {
        "surface": "paper_options_oms",
        "mode": "paper",
        "live_fill": False,
        "count": len(rows),
        "orders": list(reversed(rows)),
        "api": {
            "list": "GET /api/options/oms",
            "create": "POST /api/options/oms",
        },
        "disclaimer": "Paper desk only — does not claim EX-LIVE venue FILL.",
    }


def oms_status() -> dict[str, Any]:
    rows = _read_all(limit=500)
    return {
        "surface": "paper_options_oms",
        "mode": "paper",
        "live_fill": False,
        "orders_total": len(rows),
        "store": str(_STORE),
        "ready": True,
    }
