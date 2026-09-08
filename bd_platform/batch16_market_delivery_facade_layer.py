"""Batch16 market/delivery facade layer — capabilities #751–#800."""

from __future__ import annotations

import importlib
import inspect
import json
import logging
from pathlib import Path
from typing import Any

from bd_platform.batch16_three_spec_foundations import attach_three_spec_metadata

logger = logging.getLogger("BLACKDARK.Batch16MarketDeliveryFacade")

_MAP_PATH = Path(__file__).resolve().parents[1] / "scripts/partial_batches/batch_16_canonical_map.json"


def _load_canonical_map() -> dict[int, tuple[int, str, str, dict[str, Any]]]:
    raw = json.loads(_MAP_PATH.read_text(encoding="utf-8"))
    return {int(k): (v[0], v[1], v[2], dict(v[3] or {})) for k, v in raw.items()}


_CANONICAL_MAP = _load_canonical_map()


def reset_batch16_market_delivery_state() -> None:
    return None


def execute_batch16_facade(
    *,
    capability_id: int,
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Canonical-reuse dispatcher for CAP978 extension IDs 751-800."""
    spec = _CANONICAL_MAP.get(capability_id)
    if spec is None:
        return {"ok": False, "error": "unknown_batch16_capability", "capability_id": capability_id}
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
        "facade_layer": "batch16_market_delivery_facade",
        "attribution": f"BLACKDARK batch16 facade → {mod_path}.{fn_name}",
        "analysis_only": True,
        "no_execution": True,
    }
    attach_three_spec_metadata(payload, cap_id=capability_id)
    return payload
