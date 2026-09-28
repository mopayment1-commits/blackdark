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
        normalized = layer.normalize_payload(
            source=vendor,
            dataset="inbound",
            raw=out,
            asset_hint=str(out.get("symbol") or out.get("asset") or ""),
        )
        out.update(normalized)
    except Exception:
        out["canonical_id"] = out.get("canonical_id") or f"bd:UNMAPPED:{vendor}"
        out["normalization_error"] = "normalization_failed"
    out["normalization_version"] = NORMALIZATION_VERSION
    return out


def normalization_report(symbol: str = "BTC") -> dict[str, Any]:
    try:
        import asyncio

        from blackdark.canonical.layer import get_canonical_layer

        layer = get_canonical_layer()
        result = asyncio.run(layer.query(input=symbol))
        return {"symbol": symbol, "resolved": bool(result), "normalization_version": NORMALIZATION_VERSION}
    except Exception:
        return {"symbol": symbol, "resolved": False, "error": "normalization_unavailable"}
