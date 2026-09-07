"""Execute all Batch13 capability handlers — operational layer coverage."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from pdf_capability_registry import discover_bindings, execute_binding, execute_capability

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_13_601_650.json"
EXTERNAL_IDS = {647, 648, 649, 650}


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_operational_layer_direct_execute(capability_id: int) -> None:
    mod_name, fn_name = discover_bindings()[capability_id]
    out = asyncio.run(execute_binding(mod_name, fn_name, capability_id=capability_id))
    assert isinstance(out, dict)
    assert out.get("capability_id") == capability_id
    if capability_id in EXTERNAL_IDS:
        assert out.get("ok") is False
    else:
        assert out.get("ok") is True, out


@pytest.mark.parametrize("capability_id", _batch_ids())
def test_pdf_registry_execute(capability_id: int) -> None:
    out = asyncio.run(execute_capability(capability_id))
    assert isinstance(out, dict)
    if capability_id in EXTERNAL_IDS:
        assert out.get("ok") is False
        assert out.get("classification") == "EXTERNAL_DEPENDENCY_BLOCKED"
    else:
        assert out.get("ok") is True, out


def test_reset_batch13_operational_intelligence_state() -> None:
    from bd_platform.batch13_operational_intelligence_layer import reset_batch13_operational_intelligence_state

    assert reset_batch13_operational_intelligence_state() is None
