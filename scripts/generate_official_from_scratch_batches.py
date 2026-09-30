#!/usr/bin/env python3
"""Generate official 25-cap batch dedicated modules (batch02–batch34) for from-scratch build."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.backend_registry import _slug
from cap646.batch_constants import batch_id_range, total_batch_count
from cap646.catalog import catalog_by_id, is_duplicate


def _payload_key(surface: str) -> str:
    return surface[:64] if len(surface) <= 64 else surface[:61] + "_x"


def _scan_legacy_handlers() -> dict[int, tuple[str, str]]:
    """Map capability_id → (source_module, handler_function_name)."""
    mapping: dict[int, tuple[str, str]] = {}
    for path in sorted((ROOT / "cap646").glob("batch*_dedicated.py")):
        if path.stem.startswith("official_batch"):
            continue
        mod = f"cap646.{path.stem}"
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"^\s*(\d+):\s*(_cap\d+[_a-z0-9]*)", text, re.MULTILINE):
            mapping[int(m.group(1))] = (mod, m.group(2))
    return mapping


def _generate_handler(cid: int, surface: str, name: str, track: str, legacy: dict[int, tuple[str, str]]) -> str:
    pkey = _payload_key(surface)
    fn = f"_cap{cid}"
    if cid in legacy:
        src_mod, src_fn = legacy[cid]
        return f'''async def {fn}(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from {src_mod} import {src_fn} as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)
'''
    safe_name = name.replace('"', "'")
    return f'''async def {fn}(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_from_scratch import execute_from_scratch
    return await execute_from_scratch(
        {cid},
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        address=address,
        params=params,
        payload_key="{pkey}",
        capability_name="{safe_name}",
        track="{track}",
    )
'''


def generate_official_batch(batch_num: int, legacy: dict[int, tuple[str, str]]) -> Path:
    start, end = batch_id_range(batch_num)
    ids = [i for i in range(start, end + 1) if catalog_by_id().get(i) and not is_duplicate(i)]
    out = ROOT / "cap646" / f"official_batch{batch_num:02d}_dedicated.py"

    surfaces: dict[int, str] = {}
    names: dict[int, str] = {}
    tracks: dict[int, str] = {}
    for cid in ids:
        row = catalog_by_id()[cid]
        surfaces[cid] = _slug(row["capability"])
        names[cid] = row["capability"]
        tracks[cid] = row["track"]

    lines = [
        f'"""Official batch {batch_num:02d} — from-scratch dedicated backends (IDs {start}–{end})."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, Awaitable, Callable",
        "",
        "from cap646.dedicated_common import addr as _addr",
        "from cap646.dedicated_common import execute_dedicated_caps",
        "from cap646.dedicated_common import sym as _sym",
        "",
        f"OFFICIAL_BATCH{batch_num:02d}_IDS: frozenset[int] = frozenset(range({start}, {end + 1}))",
        f"BATCH{batch_num:02d}_DEDICATED_IDS: frozenset[int] = frozenset({{{', '.join(str(i) for i in ids)}}})",
        f"BATCH{batch_num:02d}_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()",
        "",
        "EXPECTED_SURFACE: dict[int, str] = {",
    ]
    for cid in ids:
        lines.append(f'    {cid}: "{surfaces[cid]}",')
    lines.append("}")
    lines.append("")

    for cid in ids:
        lines.append(_generate_handler(cid, surfaces[cid], names[cid], tracks[cid], legacy).rstrip())
        lines.append("")

    lines.append("_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {")
    for cid in ids:
        lines.append(f"    {cid}: _cap{cid},")
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:")
    lines.append("    return await execute_dedicated_caps(")
    lines.append("        capability_id,")
    lines.append("        params=params,")
    lines.append(f"        dedicated_ids=BATCH{batch_num:02d}_DEDICATED_IDS,")
    lines.append(f"        overlap_batch01_ids=BATCH{batch_num:02d}_OVERLAP_BATCH01_IDS,")
    lines.append("        dispatch=_DISPATCH,")
    lines.append(f'        overlap_error="batch01 overlap for official batch{batch_num:02d}",')
    lines.append(f'        not_dedicated_error=f"official batch{batch_num:02d}: not dedicated",')
    lines.append("    )")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def generate_test(batch_num: int) -> Path:
    start, end = batch_id_range(batch_num)
    ids = [i for i in range(start, end + 1) if catalog_by_id().get(i) and not is_duplicate(i)]
    out = ROOT / "tests" / "cap646" / f"test_official_batch{batch_num:02d}_from_scratch.py"
    content = f'''"""From-scratch tests — official batch{batch_num:02d} (IDs {start}–{end})."""

from __future__ import annotations

import pytest

from cap646.v6_from_scratch_dod import verify_from_scratch

BATCH_IDS = {ids}


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch{batch_num:02d}_from_scratch(capability_id: int):
    report = await verify_from_scratch(capability_id)
    assert report["PASS_FROM_SCRATCH"] is True, report


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_official_batch{batch_num:02d}_execute(capability_id: int):
    from cap646.official_batch_production import execute

    result = await execute(
        capability_id,
        params={{"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"}},
    )
    assert result["success"] is True, result
    assert result.get("latency_ms") is not None or result.get("performance_gate")
'''
    out.write_text(content, encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-batch", type=int, default=2)
    parser.add_argument("--to-batch", type=int, default=total_batch_count())
    parser.add_argument("--batch", type=int)
    args = parser.parse_args()

    legacy = _scan_legacy_handlers()
    batches = [args.batch] if args.batch else list(range(args.from_batch, args.to_batch + 1))

    for b in batches:
        if b == 1:
            continue
        p = generate_official_batch(b, legacy)
        t = generate_test(b)
        print(f"wrote {p.name} + {t.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
