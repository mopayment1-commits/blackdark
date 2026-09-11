"""Five-level source authority registry (DIG-001)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

_AUTHORITY_LEVELS = ("L1_SOURCE", "L2_INGEST", "L3_NORMALIZE", "L4_DERIVE", "L5_CONSUME")


@dataclass
class SourceRecord:
    source_id: str
    name: str
    authority_level: str
    license_class: str
    retention_days: int
    live_allowed: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_REGISTRY: dict[str, SourceRecord] = {
    "coingecko": SourceRecord(
        "coingecko",
        "CoinGecko",
        "L1_SOURCE",
        "vendor_terms",
        90,
        metadata={"docs": "https://www.coingecko.com/en/api_terms"},
    ),
    "binance": SourceRecord(
        "binance",
        "Binance Public API",
        "L1_SOURCE",
        "vendor_terms",
        30,
    ),
    "internal_cache": SourceRecord(
        "internal_cache",
        "BLACKDARK Internal Cache",
        "L3_NORMALIZE",
        "internal",
        7,
    ),
}


def register_source(record: SourceRecord) -> SourceRecord:
    if record.authority_level not in _AUTHORITY_LEVELS:
        raise ValueError(f"invalid authority_level: {record.authority_level}")
    _REGISTRY[record.source_id] = record
    return record


def list_sources() -> list[dict[str, Any]]:
    return [r.to_dict() for r in _REGISTRY.values()]


def get_source(source_id: str) -> SourceRecord | None:
    return _REGISTRY.get(source_id)
