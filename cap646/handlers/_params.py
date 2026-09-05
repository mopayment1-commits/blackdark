"""Shared handler parameter helpers."""

from __future__ import annotations

from typing import Any


def normalize_symbol(params: dict[str, Any]) -> str:
    return str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")
