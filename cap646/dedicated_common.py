"""Shared helpers for batch dedicated modules — Extract Function (CLOSURE-MANDATE-FINAL item 3)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cap646.evidence_class import ai_compliance_footer

_ROOT = Path(__file__).resolve().parents[1]
_SEED_PATH = _ROOT / "data/legal_retail_commercial_seed.json"


def seed() -> dict[str, Any]:
    if _SEED_PATH.is_file():
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    return {}


def sym(params: dict[str, Any]) -> str:
    return str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")


def addr(params: dict[str, Any]) -> str:
    return str(params.get("address") or params.get("wallet") or "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb").strip()


def success_from(payload: Any) -> bool:
    if isinstance(payload, dict):
        if "success" in payload:
            return bool(payload.get("success"))
        if "ok" in payload:
            return bool(payload.get("ok"))
        return bool(payload)
    return bool(payload)


def wrap(
    capability_id: int,
    *,
    expected_surface: dict[int, str],
    symbol: str,
    payload_key: str,
    payload: Any,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "capability_id": capability_id,
        "surface": expected_surface[capability_id],
        "symbol": symbol,
        payload_key: payload,
        "success": success_from(payload),
    }
    if extra:
        body.update(extra)
    return ai_compliance_footer(body)
