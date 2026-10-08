"""Public oracle symbol catalog — same universe registry that feeds normalize_oracle_symbol."""

from __future__ import annotations

from functools import lru_cache

from platform_universe import universe_assets


@lru_cache(maxsize=1)
def primary_oracle_catalog_symbols() -> tuple[str, ...]:
    """Canonical primary symbols from data/universe_registry.json (Oracle resolution path)."""
    symbols: list[str] = []
    seen: set[str] = set()
    for row in universe_assets():
        sym = str(row.get("symbol") or "").upper().strip()
        if not sym or sym in seen:
            continue
        seen.add(sym)
        symbols.append(sym)
    return tuple(sorted(symbols))


def oracle_catalog_payload() -> dict:
    symbols = list(primary_oracle_catalog_symbols())
    return {"count": len(symbols), "symbols": symbols}
