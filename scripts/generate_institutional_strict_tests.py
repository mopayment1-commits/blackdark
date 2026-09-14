#!/usr/bin/env python3
"""Generate strict institutional pytest for all 34 batches."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch_constants import batch_id_range, total_batch_count
from cap646.catalog import catalog_by_id, is_duplicate


def main() -> int:
    tests_dir = ROOT / "tests" / "cap646"
    tests_dir.mkdir(parents=True, exist_ok=True)

    for batch_num in range(1, total_batch_count() + 1):
        start, end = batch_id_range(batch_num)
        ids = [i for i in range(start, end + 1) if catalog_by_id().get(i) and not is_duplicate(i)]
        path = tests_dir / f"test_institutional_batch{batch_num:02d}_strict.py"
        path.write_text(
            f'''"""Mandatory v6 strict institutional tests — batch{batch_num:02d} (IDs {start}–{end})."""

from __future__ import annotations

import pytest

from cap646.institutional_official_production import execute, expected_surface
from cap646.v6_strict_closure import verify_strict_institutional

BATCH_IDS = {ids}


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_institutional_strict_closure(capability_id: int):
    report = await verify_strict_institutional(capability_id)
    assert report.get("PASS_INSTITUTIONAL_STRICT") is True, report


@pytest.mark.parametrize("capability_id", BATCH_IDS)
@pytest.mark.asyncio
async def test_institutional_execute_surface(capability_id: int):
    result = await execute(
        capability_id,
        params={{"symbol": "BTC", "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "tier": "pro"}},
    )
    assert result["success"] is True, result
    assert result["surface"] == expected_surface(capability_id)
    assert result.get("compliance_footer")
''',
            encoding="utf-8",
        )
        print(f"batch{batch_num:02d}: {len(ids)} tests")

    all_ids = [i for i in range(1, 827) if catalog_by_id().get(i) and not is_duplicate(i)]
    (tests_dir / "test_institutional_all_batches_strict.py").write_text(
        f'"""Aggregate strict test index — {len(all_ids)} capabilities."""\n\nBATCH_ALL_IDS = {all_ids}\n',
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
