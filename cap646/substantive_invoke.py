"""Semantic backend invocation for v6 substantive batch handlers."""

from __future__ import annotations

import importlib
from typing import Any

from cap646.backend_executor import _call_entrypoint
from cap646.backend_registry import BackendBinding


async def invoke_substantive(
    module: str,
    entrypoint: str,
    *,
    symbol: str,
    address: str,
    params: dict[str, Any],
    param_style: str,
    capability_id: int = 0,
) -> Any:
    """Invoke a bound backend entrypoint with signature-aware kwargs."""
    fn = getattr(importlib.import_module(module), entrypoint)
    binding = BackendBinding(
        capability_id=capability_id,
        module=module,
        entrypoint=entrypoint,
        surface="",
        param_style=param_style,
        source="substantive_invoke",
    )
    merged = dict(params or {})
    merged.setdefault("symbol", symbol)
    if address:
        merged.setdefault("address", address)
    return await _call_entrypoint(fn, params=merged, binding=binding)
