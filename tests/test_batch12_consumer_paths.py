"""Batch12 consumer-path evidence — cap646 runtime to canonical implementation."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from pdf_capability_registry import discover_bindings, execute_capability

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_12_551_600.json"


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_consumer_path_execute_capability(capability_id: int):
    mod, fn = discover_bindings()[capability_id]
    out = asyncio.run(execute_capability(capability_id))
    assert out.get("ok") is True, out
    assert out.get("capability_id") == capability_id
    assert mod
    assert fn


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_no_orphan_generic_only(capability_id: int):
    out = asyncio.run(execute_capability(capability_id))
    keys = set(out.keys()) - {"ok", "capability_id", "symbol", "timestamp", "disclaimer", "analysis_only", "no_execution"}
    assert len(keys) >= 2, out
