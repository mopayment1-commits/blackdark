#!/usr/bin/env python3
"""Generate cap646/batchNN_dedicated.py for official batches 04–17 (v6 institutional pattern)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.backend_registry import _slug
from cap646.batch_constants import CAPABILITIES_PER_BATCH, batch_id_range, total_batch_count
from cap646.catalog import catalog_by_id, is_duplicate


def _payload_key(surface: str) -> str:
    return surface[:64] if len(surface) <= 64 else surface[:61] + "_x"


def generate_batch(batch_num: int) -> Path:
    start, end = batch_id_range(batch_num)
    ids = [i for i in range(start, end + 1) if catalog_by_id().get(i) and not is_duplicate(i)]

    mod_name = f"batch{batch_num:02d}_dedicated"
    out = ROOT / "cap646" / f"{mod_name}.py"

    surfaces: dict[int, str] = {}
    for cid in ids:
        row = catalog_by_id()[cid]
        surfaces[cid] = _slug(row["capability"])

    lines = [
        f'"""Official Batch {batch_num:02d} dedicated backends — goal-specific payloads (v6 §2.1).',
        f"",
        f"Auto-generated — institutional 25-cap batch {batch_num:02d} (IDs {start}–{end}).",
        f'"""',
        f"",
        f"from __future__ import annotations",
        f"",
        f"from typing import Any, Awaitable, Callable",
        f"",
        f"from cap646.dedicated_common import addr as _addr",
        f"from cap646.dedicated_common import execute_dedicated_caps",
        f"from cap646.dedicated_common import make_wrap_binding",
        f"from cap646.dedicated_common import sym as _sym",
        f"from cap646.dedicated_common import wrap_with_backend",
        f"",
        f"OFFICIAL_BATCH{batch_num:02d}_IDS: frozenset[int] = frozenset(range({start}, {end + 1}))",
        f"BATCH{batch_num:02d}_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()",
        f"BATCH{batch_num:02d}_DEDICATED_IDS: frozenset[int] = frozenset({{{', '.join(str(i) for i in ids)}}})",
        f"",
        f"GENERIC_SURFACES = frozenset(",
        f'    {{"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}}',
        f")",
        f"",
        f"EXPECTED_SURFACE: dict[int, str] = {{",
    ]
    for cid in ids:
        lines.append(f'    {cid}: "{surfaces[cid]}",')
    lines.append("}")
    lines.append("")
    lines.append("_wrap = make_wrap_binding(EXPECTED_SURFACE)")
    lines.append("")

    handler_defs: list[str] = []
    dispatch_entries: list[str] = []

    for cid in ids:
        surface = surfaces[cid]
        pkey = _payload_key(surface)
        fn_name = f"_cap{cid}"
        handler_defs.append(
            f"""async def {fn_name}(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        {cid},
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="{pkey}",
        params=params,
    )
"""
        )
        dispatch_entries.append(f"    {cid}: {fn_name},")

    lines.extend(handler_defs)
    lines.append("_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {")
    lines.extend(dispatch_entries)
    lines.append("}")
    lines.append("")
    lines.append("")
    lines.append("async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:")
    lines.append("    return await execute_dedicated_caps(")
    lines.append(f"        capability_id,")
    lines.append("        params=params,")
    lines.append(f"        dedicated_ids=BATCH{batch_num:02d}_DEDICATED_IDS,")
    lines.append(f"        overlap_batch01_ids=BATCH{batch_num:02d}_OVERLAP_BATCH01_IDS,")
    lines.append("        dispatch=_DISPATCH,")
    lines.append(f'        overlap_error="batch01 overlap for batch{batch_num:02d}",')
    lines.append(f'        not_dedicated_error=f"batch{batch_num:02d}: not a dedicated capability",')
    lines.append("    )")
    lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, help="Batch number (07–34 for generated dedicated)")
    parser.add_argument("--all", action="store_true", help="Generate all 25-cap batches 07–34 (151–826)")
    args = parser.parse_args()

    first_dedicated_batch = (151 - 1) // CAPABILITIES_PER_BATCH + 1  # batch07
    batches = list(range(first_dedicated_batch, total_batch_count() + 1)) if args.all else [args.batch]
    for b in batches:
        if b < first_dedicated_batch or b > total_batch_count():
            print(f"skip invalid batch {b}")
            continue
        path = generate_batch(b)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
