"""Schema evolution registry and breaking-change detection."""

from __future__ import annotations

from typing import Any

PARSER_VERSIONS: dict[str, str] = {
    "binance_spot": "1.0.0",
    "coingecko_prices": "1.0.0",
    "kraken_spot": "1.0.0",
    "oracle_payload": "1.0.0",
}


def validate_schema(*, source_id: str, payload: dict[str, Any], required_fields: list[str] | None = None) -> dict[str, Any]:
    required = required_fields or []
    missing = [f for f in required if f not in payload]
    unknown = [k for k in payload if k.startswith("_unknown_")]
    compatible = not missing
    return {
        "source_id": source_id,
        "parser_version": PARSER_VERSIONS.get(source_id, "1.0.0"),
        "compatible": compatible,
        "missing_fields": missing,
        "unknown_fields": unknown,
        "quarantine": not compatible,
    }


def schema_evolution_status() -> dict[str, Any]:
    return {"parsers_registered": len(PARSER_VERSIONS), "silent_break_paths": []}
