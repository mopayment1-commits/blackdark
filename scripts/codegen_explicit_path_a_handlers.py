#!/usr/bin/env python3
"""Generate explicit Path A dedicated handlers from backend_registry bindings (v6 §2.1)."""
from __future__ import annotations

import inspect
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from cap646.backend_registry import resolve_binding  # noqa: E402
from scripts.batch_dedicated_overrides import overrides_for  # noqa: E402
from scripts.batch_rbas_config import BatchRbasConfig  # noqa: E402


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s[:80] or "capability"


def _call_lines(binding: Any, cid: int) -> list[str]:
    mod = binding.module
    ep = binding.entrypoint
    style = binding.param_style
    lines = [f"    from {mod} import {ep}"]
    if style == "none":
        lines.append(f"    _raw = {ep}()")
    elif style == "address":
        lines.append('    _addr_val = str(params.get("address") or address or "").strip()')
        lines.append(f"    _raw = {ep}(_addr_val)")
    elif style == "cert":
        lines.append("    _cert = {")
        lines.append(f'        "symbol": str(params.get("symbol") or symbol or "BTC"),')
        lines.append(f'        "capability_id": {cid},')
        lines.append('        "tier": str(params.get("tier") or "pro"),')
        lines.append("    }")
        lines.append(f"    _raw = {ep}(_cert)")
    elif style == "message":
        lines.append('    _msg = str(params.get("message") or params.get("query") or symbol or "BTC")')
        lines.append(f"    _raw = {ep}(_msg)")
    elif style == "assets":
        lines.append('    _assets = params.get("assets") or [str(params.get("symbol") or symbol or "BTC")]')
        lines.append(f"    _raw = {ep}(assets=_assets)")
    elif style == "limit":
        lines.append('    _limit = int(params.get("limit") or 50)')
        lines.append(f"    _raw = {ep}(_limit)")
    else:
        lines.append('    _sym = str(params.get("symbol") or symbol or "BTC").upper()')
        lines.append(f"    _raw = {ep}(_sym)")
    lines.append("    if hasattr(_raw, '__await__'):")
    lines.append("        _raw = await _raw")
    lines.append("    payload = _raw if isinstance(_raw, dict) else {'success': bool(_raw), 'result': _raw}")
    lines.append("    if 'success' not in payload and not payload.get('error'):")
    lines.append("        payload['success'] = True")
    lines.append("    payload['methodology'] = {")
    lines.append('        "framework": "Path A — explicit backend_registry binding (v6 §2.1)",')
    lines.append(f'        "implementation": "{mod}.{ep}",')
    lines.append('        "methodology_status": "DOCUMENTED",')
    lines.append(f'        "binding_source_resolved": "{binding.source}",')
    lines.append("    }")
    return lines


def handler_source(cid: int, surface: str, binding: Any) -> str:
    body_lines = _call_lines(binding, cid)
    indented = "\n".join(body_lines)
    return (
        f"async def _cap{cid:03d}(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:\n"
        f'    """Path A explicit — {binding.module}.{binding.entrypoint} (v6 real logic)."""\n'
        f"{indented}\n"
        f'    return _wrap({cid}, symbol=symbol, payload_key="{surface}", payload=payload)'
    )


def regenerate_dedicated(cfg: BatchRbasConfig) -> Path:
    n = cfg.batch_num
    bn = f"batch{n:02d}"
    out = ROOT / "cap646" / f"{bn}_dedicated.py"
    catalog = {int(r["id"]): r for r in json.loads((ROOT / "docs/cap646/CAP646_CATALOG.json").read_text())}
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
        binding = resolve_binding(cid)
        handlers.append(handler_source(cid, surface, binding))
        dispatch.append(f"    {cid}: _cap{cid:03d},")

    expected_lines = "\n".join(f"    {cid}: {repr(v)}," for cid, v in sorted(expected.items()))
    header = f'''"""Batch {n:02d} prep dedicated backends — IDs {cfg.id_start}–{cfg.id_end} (v6 Path A explicit)."""

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
    import sys

    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(4, 18))
    for n in nums:
        cfg = BatchRbasConfig(n)
        path = regenerate_dedicated(cfg)
        print(f"Batch {n:02d}: {path.name} explicit Path A ({cfg.count} handlers)")


if __name__ == "__main__":
    main()
