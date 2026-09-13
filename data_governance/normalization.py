"""Canonical normalization contract (DIG-002, DIG-017, DIG-040)."""

from __future__ import annotations

from typing import Any


def normalize_payload(payload: dict[str, Any], *, surface: str) -> dict[str, Any]:
    out = dict(payload)
    symbol = out.get("symbol") or out.get("asset")
    if symbol:
        out["symbol"] = str(symbol).upper().strip()
        out.setdefault("asset", out["symbol"])
    source = out.get("source_id") or out.get("source")
    if source:
        out["source_id"] = str(source).strip().lower()
        out.setdefault("source", out["source_id"])
    out.setdefault("normalized", True)
    out.setdefault("normalization_surface", surface)
    return out
