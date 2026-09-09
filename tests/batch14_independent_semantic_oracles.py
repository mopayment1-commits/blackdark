"""Independent reference oracles for Batch14 parameterized semantics (shared core)."""

from __future__ import annotations


def _ratio(a: float, b: float, *, scale: float = 100.0) -> float:
    return round(a / max(b, 1e-9) * scale, 4)


def _spread(a: float, b: float) -> float:
    return round(a - b, 4)


def _weighted(*pairs: tuple[float, float]) -> float:
    num = sum(v * w for v, w in pairs)
    den = sum(w for _, w in pairs)
    return round(num / max(den, 1e-9), 4)


def independent_primary(cap_id: int, rule: str, inputs: dict[str, float], symbol: str = "ETH") -> float:
    i = inputs
    keys = list(i.keys())
    if len(keys) < 3:
        return round(float(list(i.values())[0]), 4)
    a, b, c = keys[0], keys[1], keys[2]
    blob = rule.lower()
    if "spread" in blob or "arbitrage" in blob:
        return _spread(i[a], i[b])
    if any(x in blob for x in ("tvl", "volume", "yield", "stablecoin", "bridge", "unlock")):
        return round(_ratio(i[a], i[b]), 4)
    if any(x in blob for x in ("research", "analyst", "risk", "developer")):
        return _weighted((i[a], 0.5), (i[b], 0.3), (i[c], 0.2))
    return round(_ratio(i[a], i[c]), 4)
