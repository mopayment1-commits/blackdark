"""Independent reference oracles for Batch13 parameterized semantics (shared core)."""

from __future__ import annotations


def _ratio(a: float, b: float, *, scale: float = 100.0) -> float:
    return round(a / max(b, 1e-9) * scale, 4)


def _spread(a: float, b: float) -> float:
    return round(a - b, 4)


def _weighted(*pairs: tuple[float, float]) -> float:
    num = sum(v * w for v, w in pairs)
    den = sum(w for _, w in pairs)
    return round(num / max(den, 1e-9), 4)


_SPREAD_IDS = {608, 612, 617}
_RATIO_AB_IDS = {604, 613, 633, 634, 635}
_WEIGHTED_IDS = {606, 607, 621, 622, 626, 628, 636, 643}


def independent_primary(cap_id: int, rule: str, inputs: dict[str, float], symbol: str = "ETH") -> float:
    i = inputs
    keys = list(i.keys())
    if len(keys) < 3:
        return round(float(list(i.values())[0]), 4)
    a, b, c = keys[0], keys[1], keys[2]
    if cap_id in _SPREAD_IDS:
        return _spread(i[a], i[b])
    if cap_id in _RATIO_AB_IDS:
        return round(_ratio(i[a], i[b]), 4)
    if cap_id in _WEIGHTED_IDS:
        return _weighted((i[a], 0.5), (i[b], 0.3), (i[c], 0.2))
    return round(_ratio(i[a], i[c]), 4)

