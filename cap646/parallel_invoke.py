"""Invoke inventory-documented parallel backend paths for split-brain contract tests."""

from __future__ import annotations

import importlib
import inspect
import re
from typing import Any

_CAP_ENTRY = re.compile(r"^cap_(\d+)$")


async def invoke_inventory_backend(backend: str, *, params: dict[str, Any]) -> dict[str, Any]:
    """Call inventory ``backend`` (e.g. cap646.batch02_production.cap_051)."""
    if not backend or "." not in backend:
        return {"success": False, "error": "missing_backend", "backend": backend}
    module_path, entry = backend.rsplit(".", 1)
    merged = dict(params)
    symbol = str(merged.get("symbol") or merged.get("asset") or "BTC").upper().replace("/USDT", "")
    merged.setdefault("symbol", symbol)

    cap_match = _CAP_ENTRY.match(entry)
    if cap_match and module_path.endswith("_production"):
        mod = importlib.import_module(module_path)
        cid = int(cap_match.group(1))
        execute = getattr(mod, "execute")
        return await execute(cid, params=merged)

    mod = importlib.import_module(module_path)
    fn = getattr(mod, entry)
    if inspect.iscoroutinefunction(fn):
        sig = inspect.signature(fn)
        if "params" in sig.parameters:
            if "symbol" in sig.parameters:
                return await fn(symbol=symbol, params=merged)
            return await fn(params=merged)
        if "symbol" in sig.parameters:
            return await fn(symbol=symbol)
        return await fn()
    if "symbol" in inspect.signature(fn).parameters:
        return fn(symbol=symbol)
    return fn()
