#!/usr/bin/env python3
"""Regenerate batch dedicated handlers with Path A catalog_binding_executor (real SSOT logic)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.batch_dedicated_overrides import overrides_for  # noqa: E402
from scripts.batch_rbas_config import BatchRbasConfig  # noqa: E402


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s[:80] or "capability"


def regenerate_dedicated(cfg: BatchRbasConfig) -> Path:
    n = cfg.batch_num
    bn = f"batch{n:02d}"
    out = ROOT / "cap646" / f"{bn}_dedicated.py"
    catalog_path = ROOT / "docs" / "cap646" / "CAP646_CATALOG.json"
    catalog = {int(r["id"]): r for r in json.loads(catalog_path.read_text(encoding="utf-8"))}
    custom = overrides_for(n)

    expected: dict[int, str] = {}
    handlers: list[str] = []
    dispatch: list[str] = []

    for cid in cfg.id_range:
        if cid in custom:
            surface, handler_src = custom[cid]
            expected[cid] = surface
            handlers.append(handler_src)
            dispatch.append(f"    {cid}: _cap{cid:03d},")
            continue
        row = catalog.get(cid, {})
        name = str(row.get("capability") or f"Capability {cid}")
        surface = slug(name)
        expected[cid] = surface
        handlers.append(
            f'''async def _cap{cid:03d}(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    """Path A — SSOT catalog_binding_executor (backend_registry)."""
    from cap646.catalog_binding_executor import execute_catalog_binding

    payload = await execute_catalog_binding({cid}, symbol=symbol, address=address, params=params)
    return _wrap({cid}, symbol=symbol, payload_key="{surface}", payload=payload)'''
        )
        dispatch.append(f"    {cid}: _cap{cid:03d},")

    expected_lines = "\n".join(f"    {cid}: {repr(v)}," for cid, v in sorted(expected.items()))
    header = f'''"""Batch {n:02d} prep dedicated backends — IDs {cfg.id_start}–{cfg.id_end} (Run 021 Path A)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym

BATCH{n:02d}_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
OFFICIAL_BATCH{n:02d}_IDS: frozenset[int] = frozenset(range({cfg.id_start}, {cfg.id_end + 1}))
BATCH{n:02d}_DEDICATED_IDS: frozenset[int] = OFFICIAL_BATCH{n:02d}_IDS

EXPECTED_SURFACE: dict[int, str] = {{
'''
    footer = f'''
}}

_base_wrap = make_wrap_binding(EXPECTED_SURFACE)


def _wrap(
    capability_id: int,
    *,
    symbol: str,
    payload_key: str,
    payload: Any,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Batch wrap — BCBS 239 top-level provenance."""
    merged: dict[str, Any] = dict(extra or {{}})
    if isinstance(payload, dict):
        src = payload.get("data_source") or payload.get("source")
        if src and not merged.get("data_source"):
            merged["data_source"] = src
        ts = payload.get("timestamp") or payload.get("attached_at")
        if ts and not merged.get("timestamp"):
            merged["timestamp"] = ts
        meth = payload.get("methodology")
        if meth and not merged.get("methodology"):
            merged["methodology"] = meth
    if not merged.get("data_source"):
        merged["data_source"] = f"cap646.{bn}_dedicated#cap{{capability_id:03d}}"
    if not merged.get("timestamp"):
        merged["timestamp"] = datetime.now(UTC).isoformat()
    return _base_wrap(
        capability_id, symbol=symbol, payload_key=payload_key, payload=payload, extra=merged,
    )


'''
    dispatch_block = (
        f"_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {{\n"
        + "\n".join(dispatch)
        + "\n}\n\n\n"
    )
    execute_block = f'''async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH{n:02d}_DEDICATED_IDS,
        overlap_batch01_ids=BATCH{n:02d}_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="{bn}: ID in batch01 overlap — CROSS-SPINE-001",
        not_dedicated_error="capability not in {bn} dedicated set",
    )
'''
    content = header + expected_lines + footer + "\n\n".join(handlers) + "\n\n" + dispatch_block + execute_block
    out.write_text(content, encoding="utf-8")
    return out


def main() -> None:
    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(4, 13))
    for n in nums:
        cfg = BatchRbasConfig(n)
        path = regenerate_dedicated(cfg)
        print(f"Batch {n:02d}: {path.name} ({cfg.count} handlers — catalog_binding_executor)")


if __name__ == "__main__":
    main()
