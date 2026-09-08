"""Shared CAP978 extension facade dispatcher — Sonar-safe reuse for batch facades."""

from __future__ import annotations

import importlib
import inspect
import json
from pathlib import Path
from typing import Any, Callable


def load_canonical_map(map_path: Path) -> dict[int, tuple[int, str, str, dict[str, Any]]]:
    raw = json.loads(map_path.read_text(encoding="utf-8"))
    return {int(k): (v[0], v[1], v[2], dict(v[3] or {})) for k, v in raw.items()}


def execute_extension_facade(
    *,
    capability_id: int,
    canonical_map: dict[int, tuple[int, str, str, dict[str, Any]]],
    facade_layer: str,
    attach_metadata: Callable[[dict[str, Any], int], None],
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec = canonical_map.get(capability_id)
    if spec is None:
        return {"ok": False, "error": "unknown_extension_facade_capability", "capability_id": capability_id}
    canonical_id, mod_path, fn_name, extra_kwargs = spec
    mod = importlib.import_module(mod_path)
    canonical_fn = getattr(mod, fn_name)
    call_kwargs: dict[str, Any] = dict(extra_kwargs)
    sig = inspect.signature(canonical_fn)
    if "symbol" in sig.parameters:
        call_kwargs.setdefault("symbol", symbol)
    if seed is not None and "seed" in sig.parameters:
        call_kwargs["seed"] = seed
    if inspect.iscoroutinefunction(canonical_fn):
        import asyncio
        import concurrent.futures

        def _run_coro() -> Any:
            return asyncio.run(canonical_fn(**call_kwargs))

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            canonical = _run_coro()
        else:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                canonical = pool.submit(_run_coro).result()
    else:
        canonical = canonical_fn(**call_kwargs)
    if not isinstance(canonical, dict):
        canonical = {"result": canonical}
    payload = {
        **canonical,
        "ok": canonical.get("ok", True),
        "capability_id": capability_id,
        "canonical_reuse_of": canonical_id,
        "facade_layer": facade_layer,
        "attribution": f"BLACKDARK {facade_layer} → {mod_path}.{fn_name}",
        "analysis_only": True,
        "no_execution": True,
    }
    attach_metadata(payload, cap_id=capability_id)
    return payload
