"""Partial closure batch 06 — dedicated execute smoke for bound capabilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdf_capability_registry import discover_bindings, execute_capability

_MANIFEST = Path(__file__).resolve().parent.parent / "scripts" / "partial_batches" / "batch_06.json"
_BATCH_IDS: list[int] = json.loads(_MANIFEST.read_text(encoding="utf-8"))["capability_ids"]
_BOUND_IDS = [cid for cid in _BATCH_IDS if cid in discover_bindings()]


@pytest.mark.parametrize("capability_id", _BOUND_IDS)
@pytest.mark.asyncio
async def test_partial_batch_06_capability_executes(capability_id: int):
    binding = discover_bindings()[capability_id]
    result = await execute_capability(capability_id)
    assert result.get("ok") is True, (capability_id, binding, result)
