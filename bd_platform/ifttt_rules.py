"""IFTTT-style user rule builder."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import config


def _path():
    return config.DATA_DIR / "ifttt_rules.json"


def _load() -> list[dict[str, Any]]:
    p = _path()
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def list_rules() -> dict[str, Any]:
    return {"rules": _load(), "count": len(_load())}


def create_rule(*, if_condition: str, then_action: str, enabled: bool = True) -> dict[str, Any]:
    rule = {
        "id": f"rule_{int(datetime.now(UTC).timestamp())}",
        "if": if_condition,
        "then": then_action,
        "enabled": enabled,
        "created_at": datetime.now(UTC).isoformat(),
    }
    rows = _load()
    rows.append(rule)
    _save(rows)
    return rule


async def evaluate_rules() -> dict[str, Any]:
    from scan_coordinator import get_shared_scan

    triggered: list[dict[str, Any]] = []
    scan = await get_shared_scan(profitable_only=True, prefer_live=False)
    top = scan.get("top_opportunity") or {}
    profit = float(top.get("net_profit_usdt") or 0)

    for rule in _load():
        if not rule.get("enabled"):
            continue
        cond = str(rule.get("if") or "").lower()
        if "profit" in cond and profit >= 0.25:
            triggered.append({**rule, "matched_value": profit})

    return {"evaluated": len(_load()), "triggered": triggered, "scan_ms": scan.get("scan_ms")}
