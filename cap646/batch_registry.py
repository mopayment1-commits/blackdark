"""Dynamic batch spine registry for runtime routing (batches 01–17)."""
from __future__ import annotations

import importlib
from functools import lru_cache
from typing import Any, Awaitable, Callable

_MAX_BATCH = 17


@lru_cache(maxsize=1)
def batch_id_sets() -> dict[int, frozenset[int]]:
    out: dict[int, frozenset[int]] = {}
    for n in range(1, _MAX_BATCH + 1):
        mod_name = f"cap646.batch{n:02d}_production"
        try:
            mod = importlib.import_module(mod_name)
        except ModuleNotFoundError:
            continue
        ids = getattr(mod, f"BATCH{n:02d}_IDS", None)
        if ids is not None:
            out[n] = frozenset(ids)
    return out


@lru_cache(maxsize=1)
def all_batch_ids() -> frozenset[int]:
    merged: set[int] = set()
    for ids in batch_id_sets().values():
        merged.update(ids)
    return frozenset(merged)


def batch_handler_for(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]] | None:
    for n, ids in sorted(batch_id_sets().items()):
        if capability_id in ids:
            handler_mod = importlib.import_module(f"cap646.handlers.batch{n:02d}")
            return getattr(handler_mod, f"handle_batch{n:02d}_capability")
    return None


def routing_overlap_map() -> dict[int, list[str]]:
    id_to_lists: dict[int, list[str]] = {}
    for n, ids in batch_id_sets().items():
        name = f"BATCH{n:02d}_IDS"
        for cid in ids:
            id_to_lists.setdefault(cid, []).append(name)
    return {cid: names for cid, names in id_to_lists.items() if len(names) > 1}
