#!/usr/bin/env python3
"""Generate cap646/batch05_dedicated.py for official Batch 05 (IDs 201–250)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "cap646" / "batch05_dedicated.py"


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s[:80] or "capability"


def main() -> None:
    import json

    catalog_path = ROOT / "docs" / "cap646" / "CAP646_CATALOG.json"
    catalog = {int(r["id"]): r for r in json.loads(catalog_path.read_text(encoding="utf-8"))}
    expected: dict[int, str] = {}
    handlers: list[str] = []
    dispatch: list[str] = []

    for cid in range(201, 251):
        row = catalog.get(cid, {})
        name = str(row.get("capability") or f"Capability {cid}")
        surface = slug(name)
        expected[cid] = surface
        handlers.append(
            f"""async def _cap{cid:03d}(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying({cid}, params={{**params, "symbol": symbol}})
    return _wrap({cid}, symbol=symbol, payload_key="{surface}", payload=payload)"""
        )
        dispatch.append(f"    {cid}: _cap{cid:03d},")

    expected_lines = "\n".join(f"    {cid}: {json_quote(v)}," for cid, v in sorted(expected.items()))
    header = '''"""Batch 05 prep dedicated backends — IDs 201–250 (Run 013 opening)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from cap646.batch05_underlying import invoke_underlying
from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym

BATCH05_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()  # 214/245 resolved Run 013
OFFICIAL_BATCH05_IDS: frozenset[int] = frozenset(range(201, 251))
BATCH05_DEDICATED_IDS: frozenset[int] = OFFICIAL_BATCH05_IDS

EXPECTED_SURFACE: dict[int, str] = {
'''
    footer = '''
}

_base_wrap = make_wrap_binding(EXPECTED_SURFACE)


def _wrap(
    capability_id: int,
    *,
    symbol: str,
    payload_key: str,
    payload: Any,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Batch05 wrap — BCBS 239 top-level provenance (Run 013)."""
    merged: dict[str, Any] = dict(extra or {})
    if isinstance(payload, dict):
        src = payload.get("data_source") or payload.get("source")
        if src and not merged.get("data_source"):
            merged["data_source"] = src
        ts = payload.get("timestamp") or payload.get("attached_at")
        if ts and not merged.get("timestamp"):
            merged["timestamp"] = ts
    if not merged.get("data_source"):
        merged["data_source"] = f"cap646.batch05_dedicated#cap{capability_id:03d}"
    if not merged.get("timestamp"):
        merged["timestamp"] = datetime.now(UTC).isoformat()
    return _base_wrap(
        capability_id, symbol=symbol, payload_key=payload_key, payload=payload, extra=merged,
    )


'''
    dispatch_block = "_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {\n" + "\n".join(dispatch) + "\n}\n\n\n"
    execute_block = '''async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH05_DEDICATED_IDS,
        overlap_batch01_ids=BATCH05_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch05: ID in batch01 overlap — CROSS-SPINE-001",
        not_dedicated_error="capability not in batch05 dedicated set",
    )
'''
    content = header + expected_lines + footer + "\n\n".join(handlers) + "\n\n" + dispatch_block + execute_block
    OUT.write_text(content, encoding="utf-8")
    print(f"Wrote {OUT} ({len(expected)} handlers)")


def json_quote(s: str) -> str:
    return repr(s)


if __name__ == "__main__":
    main()
