"""Canonical asset schema — stable IDs and reference metadata."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

REGISTRY_VERSION = 1
CANONICAL_PREFIX = "bd"


@dataclass(frozen=True)
class CanonicalAsset:
    """Stable reference record for a tradable asset."""

    canonical_id: str
    symbol: str
    label: str
    aliases: tuple[str, ...] = ()
    sector: str | None = None
    external_ids: dict[str, str] = field(default_factory=dict)
    contracts: dict[str, dict[str, Any]] = field(default_factory=dict)
    registry_version: int = REGISTRY_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, row: dict[str, Any]) -> CanonicalAsset:
        aliases = row.get("aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]
        return cls(
            canonical_id=str(row["canonical_id"]),
            symbol=str(row["symbol"]).upper(),
            label=str(row.get("label") or row["symbol"]),
            aliases=tuple(str(a).upper() for a in aliases),
            sector=row.get("sector"),
            external_ids=dict(row.get("external_ids") or {}),
            contracts=dict(row.get("contracts") or {}),
            registry_version=int(row.get("registry_version") or REGISTRY_VERSION),
        )


@dataclass(frozen=True)
class ResolveResult:
    """Outcome of resolving arbitrary input to a canonical asset."""

    found: bool
    input: str
    canonical_id: str | None = None
    symbol: str | None = None
    asset: CanonicalAsset | None = None
    matched_via: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "found": self.found,
            "input": self.input,
            "canonical_id": self.canonical_id,
            "symbol": self.symbol,
            "matched_via": self.matched_via,
        }
        if self.asset:
            payload["asset"] = self.asset.to_dict()
        return payload


def make_canonical_id(symbol: str) -> str:
    return f"{CANONICAL_PREFIX}:{symbol.upper()}"
