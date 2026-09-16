#!/usr/bin/env python3
"""Generate tests/cap646/test_capability_build_batchNN.py if missing."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = '''"""Build Batch {batch:02d} — capability IDs {start}–{end} runtime proof (v6 build executor)."""

from __future__ import annotations

import pytest

BUILD_BATCH_{batch:02d}_IDS = list(range({start}, {end_plus}))


@pytest.mark.parametrize("capability_id", BUILD_BATCH_{batch:02d}_IDS)
@pytest.mark.asyncio
async def test_build_batch{batch:02d}_runtime_success(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(
        capability_id,
        skip_entitlement=True,
        params={{
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "tier": "pro",
        }},
    )
    assert result.get("success") is True, result
    assert result.get("surface"), result


@pytest.mark.parametrize("capability_id", BUILD_BATCH_{batch:02d}_IDS)
@pytest.mark.asyncio
async def test_build_batch{batch:02d}_bcbs_provenance_fields(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(
        capability_id,
        skip_entitlement=True,
        params={{
            "symbol": "BTC",
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "tier": "pro",
        }},
    )
    assert result.get("data_source") or result.get("source"), result
    assert result.get("timestamp"), result


@pytest.mark.parametrize("capability_id", BUILD_BATCH_{batch:02d}_IDS)
def test_build_batch{batch:02d}_hero_binding(capability_id: int):
    from cap646.build826_heroes import hero_binding_for

    binding = hero_binding_for(capability_id)
    assert binding["hero_binding_status"] == "BOUND", binding
    assert binding["primary_hero"], binding
'''


def ensure(build_batch: int) -> Path:
    start = (build_batch - 1) * 25 + 1
    end = min(build_batch * 25, 826)
    path = ROOT / f"tests/cap646/test_capability_build_batch{build_batch:02d}.py"
    if path.is_file():
        return path
    path.write_text(
        TEMPLATE.format(batch=build_batch, start=start, end=end, end_plus=end + 1),
        encoding="utf-8",
    )
    return path


def main() -> int:
    batch = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    if batch < 1:
        print("usage: ensure_build_batch_test.py <build_batch>")
        return 1
    path = ensure(batch)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
