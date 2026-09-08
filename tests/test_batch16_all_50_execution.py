"""Execute all Batch16 capability handlers — extension analytics layer coverage."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from pdf_capability_registry import discover_bindings, execute_binding, execute_capability

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_16_751_800.json"


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_extension_layer_direct_execute(capability_id: int) -> None:
    mod_name, fn_name = discover_bindings()[capability_id]
    out = asyncio.run(execute_binding(mod_name, fn_name, capability_id=capability_id))
    assert isinstance(out, dict)
    assert out.get("capability_id") == capability_id
    assert out.get("ok") is True, out


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_pdf_registry_execute(capability_id: int) -> None:
    out = asyncio.run(execute_capability(capability_id))
    assert isinstance(out, dict)
    assert out.get("ok") is True, out


def test_reset_batch16_market_delivery_state() -> None:
    from bd_platform.batch16_market_delivery_facade_layer import reset_batch16_market_delivery_state

    assert reset_batch16_market_delivery_state() is None
