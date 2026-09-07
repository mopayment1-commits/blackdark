"""Shared deterministic helpers for batch semantic engines (401–500)."""

from __future__ import annotations

from typing import Any


def semantic_inputs(seed: dict[str, Any], cap_id: int, defaults: dict[str, float]) -> dict[str, float]:
    block = seed.get(f"cap_{cap_id}") or {}
    raw = block.get("semantic_inputs") or block
    out: dict[str, float] = {}
    for key, default in defaults.items():
        out[key] = float(raw.get(key, default))
    return out


def ratio(a: float, b: float, *, scale: float = 100.0) -> float:
    return round(a / max(b, 1e-9) * scale, 4)


def spread(a: float, b: float) -> float:
    return round(a - b, 4)


def weighted(*pairs: tuple[float, float]) -> float:
    num = sum(v * w for v, w in pairs)
    den = sum(w for _, w in pairs)
    return round(num / max(den, 1e-9), 4)
