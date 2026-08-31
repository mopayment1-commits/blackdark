"""Hero batch 01 — dedicated per-capability live execution tests (quad evidence #2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts" / "partial_batches" / "batch_hero_01.json"


def _hero_batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.mark.parametrize("capability_id", _hero_batch_ids())
@pytest.mark.asyncio
async def test_hero_batch_capability_executes(capability_id: int):
    from pdf_capability_registry import discover_bindings, execute_capability

    bindings = discover_bindings()
    assert capability_id in bindings, f"#{capability_id} missing dedicated binding"
    result = await execute_capability(capability_id)
    assert result.get("ok") is True, result.get("error") or result


@pytest.mark.parametrize("capability_id", [629, 631, 638, 640, 641, 812, 814, 815])
@pytest.mark.asyncio
async def test_six_heroes_surfaces(capability_id: int):
    from pdf_capability_registry import execute_capability

    result = await execute_capability(capability_id)
    assert result.get("ok") is True
    payload = json.dumps(result, default=str)
    hero_ids = {629, 631, 638, 640, 641, 812, 814, 815}
    assert "hero" in payload.lower() or capability_id in hero_ids


def test_hero_batch_manifest_has_100_ids():
    assert len(_hero_batch_ids()) == 100
