"""Normalization contract facade — delegates to blackdark/canonical SSOT."""

from __future__ import annotations

from typing import Any

NORMALIZATION_VERSION = "canonical_layer_v1"


def normalize_payload(payload: dict[str, Any], *, vendor: str = "unknown") -> dict[str, Any]:
    """Attach canonical identity without destroying source-native values."""
    out = dict(payload)
    out["_source_native"] = {k: v for k, v in payload.items() if not str(k).startswith("_")}
    try:
        from blackdark.canonical.layer import get_canonical_layer

        layer = get_canonical_layer()
        normalized = layer.normalize_payload(out, vendor=vendor)
        out.update(normalized)
    except Exception as exc:
        out["canonical_id"] = out.get("canonical_id") or f"bd:UNMAPPED:{vendor}"
        out["normalization_error"] = str(exc)
    out["normalization_version"] = NORMALIZATION_VERSION
    return out


def normalization_report(symbol: str = "BTC") -> dict[str, Any]:
    try:
        from blackdark.canonical.layer import get_canonical_layer

        layer = get_canonical_layer()
        result = layer.query(symbol)
        return {"symbol": symbol, "resolved": bool(result), "normalization_version": NORMALIZATION_VERSION}
    except Exception as exc:
        return {"symbol": symbol, "resolved": False, "error": str(exc)}
