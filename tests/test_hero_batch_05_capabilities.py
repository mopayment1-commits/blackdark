"""Hero batch 05 — capabilities 401–500 live execution tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts" / "partial_batches" / "batch_05_401_500.json"


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.mark.parametrize("capability_id", _batch_ids())
@pytest.mark.asyncio
async def test_batch_05_capability_executes(capability_id: int):
    from pdf_capability_registry import discover_bindings, execute_capability

    assert capability_id in discover_bindings(), f"missing binding for {capability_id}"
    result = await execute_capability(capability_id)
    assert result.get("ok") is True, result.get("error") or result


def test_batch_05_manifest_count():
    assert len(_batch_ids()) == 100
