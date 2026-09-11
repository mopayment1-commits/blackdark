#!/usr/bin/env python3
"""Generate cap646 batch spine trio + handler for official batch N (Run 021)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.batch_dedicated_overrides import overrides_for  # noqa: E402
from scripts.batch_rbas_config import BatchRbasConfig, batch_id_range  # noqa: E402


def slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s[:80] or "capability"


def write_production(cfg: BatchRbasConfig) -> Path:
    n = cfg.batch_num
    bn = f"batch{n:02d}"
    path = ROOT / "cap646" / f"{bn}_production.py"
    ids_expr = f"frozenset(range({cfg.id_start}, {cfg.id_end + 1}))"
    content = f'''"""Batch {n:02d} prep — production spine for official Batch {n:02d} (IDs {cfg.id_start}–{cfg.id_end})."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

BATCH{n:02d}_IDS: frozenset[int] = {ids_expr}
BATCH{n:02d}_PREP_IDS = BATCH{n:02d}_IDS

from cap646.{bn}_dedicated import BATCH{n:02d}_DEDICATED_IDS
from cap646.evidence_class import ai_compliance_footer


def batch{n:02d}_entrypoint(capability_id: int) -> str:
    return f"cap_{{capability_id:03d}}"


def _stamp_{bn}(result: dict[str, Any], capability_id: int) -> dict[str, Any]:
    result["backend_module"] = "cap646.{bn}_production"
    result["backend_entrypoint"] = batch{n:02d}_entrypoint(capability_id)
    result["binding_source"] = "explicit_option_a"
    result["production_spine"] = "{cfg.spine_name}"
    return result


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id not in BATCH{n:02d}_IDS:
        raise ValueError(f"capability {{capability_id}} is not in {bn} prep production spine")
    params = dict(params or {{}})
    if capability_id in BATCH{n:02d}_DEDICATED_IDS:
        from cap646.{bn}_dedicated import execute as execute_dedicated
        result = await execute_dedicated(capability_id, params=params)
        return _stamp_{bn}(result, capability_id)
    raise ValueError(f"{cfg.spine_name}: unmapped capability {{capability_id}}")


def _make_cap_entrypoint(capability_id: int) -> Callable[..., Awaitable[dict[str, Any]]]:
    async def _entry(
        symbol: str = "BTC",
        *,
        params: dict[str, Any] | None = None,
        capability_id: int = capability_id,
    ) -> dict[str, Any]:
        merged = dict(params or {{}})
        merged.setdefault("symbol", symbol)
        return await execute(capability_id, params=merged)

    _entry.__name__ = batch{n:02d}_entrypoint(capability_id)
    _entry.__doc__ = f"Batch{n:02d} prep production entrypoint for capability #{{capability_id}}."
    return _entry


for _cid in BATCH{n:02d}_IDS:
    globals()[batch{n:02d}_entrypoint(_cid)] = _make_cap_entrypoint(_cid)
'''
    path.write_text(content, encoding="utf-8")
    return path


def write_underlying(cfg: BatchRbasConfig) -> Path:
    n = cfg.batch_num
    bn = f"batch{n:02d}"
    src = ROOT / "cap646" / "batch06_underlying.py"
    dst = ROOT / "cap646" / f"{bn}_underlying.py"
    text = src.read_text(encoding="utf-8")
    text = text.replace("batch06", bn).replace("Batch06", f"Batch{n:02d}")
    dst.write_text(text, encoding="utf-8")
    return dst


def write_dedicated(cfg: BatchRbasConfig) -> Path:
    n = cfg.batch_num
    bn = f"batch{n:02d}"
    out = ROOT / "cap646" / f"{bn}_dedicated.py"
    catalog_path = ROOT / "docs" / "cap646" / "CAP646_CATALOG.json"
    catalog = {int(r["id"]): r for r in json.loads(catalog_path.read_text(encoding="utf-8"))}
    expected: dict[int, str] = {}
    handlers: list[str] = []
    dispatch: list[str] = []

    custom = overrides_for(n)
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
            f"""async def _cap{cid:03d}(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying({cid}, params={{**params, "symbol": symbol}})
    return _wrap({cid}, symbol=symbol, payload_key="{surface}", payload=payload)"""
        )
        dispatch.append(f"    {cid}: _cap{cid:03d},")

    expected_lines = "\n".join(f"    {cid}: {repr(v)}," for cid, v in sorted(expected.items()))
    header = f'''"""Batch {n:02d} prep dedicated backends — IDs {cfg.id_start}–{cfg.id_end} (Run 021)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from cap646.{bn}_underlying import invoke_underlying
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


def write_handler(cfg: BatchRbasConfig) -> Path:
    n = cfg.batch_num
    bn = f"batch{n:02d}"
    path = ROOT / "cap646" / "handlers" / f"{bn}.py"
    content = f'''"""Batch {n:02d} prep handler — routes IDs {cfg.id_start}–{cfg.id_end} to {bn} production spine."""

from __future__ import annotations

from typing import Any

from cap646.{bn}_production import execute
from cap646.handlers._batch_route import route_batch_capability


async def handle_{bn}_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    return await route_batch_capability(execute, capability_id, params=params)
'''
    path.write_text(content, encoding="utf-8")
    return path


def generate_batch(batch_num: int) -> dict[str, Path]:
    cfg = BatchRbasConfig(batch_num)
    cfg.audit_dir.mkdir(parents=True, exist_ok=True)
    return {
        "production": write_production(cfg),
        "underlying": write_underlying(cfg),
        "dedicated": write_dedicated(cfg),
        "handler": write_handler(cfg),
    }


def main() -> None:
    nums = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else list(range(7, 18))
    for n in nums:
        paths = generate_batch(n)
        cfg = BatchRbasConfig(n)
        print(f"Batch {n:02d} ({cfg.id_start}-{cfg.id_end}): {', '.join(p.name for p in paths.values())}")


if __name__ == "__main__":
    main()
