"""Batch11 full-path local integration — cap646 runtime with entitlement checks."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_11_501_550.json"

PRO_USER = {"id": 1, "email": "batch11-fullpath@blackdark.local", "tier": "pro", "role": "user"}


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.mark.parametrize("capability_id", _batch_ids())
@pytest.mark.asyncio
async def test_full_path_allow_via_cap646_runtime(capability_id: int):
    from cap646.runtime import execute_capability

    result = await execute_capability(
        capability_id,
        user=PRO_USER,
        skip_entitlement=False,
        params={"symbol": "BTC"},
    )
    assert result.get("success") is True, result
    assert result.get("capability_id") == capability_id


@pytest.mark.parametrize("capability_id", _batch_ids())
@pytest.mark.asyncio
async def test_entitlement_denied_before_handler(capability_id: int):
    from cap646.runtime import execute_capability

    denied = {
        "allowed": False,
        "reason": "tier_insufficient",
        "required_tier": "elite",
        "capability_id": capability_id,
    }
    with patch("cap646.runtime.entitlement_engine.check", new=AsyncMock(return_value=denied)):
        result = await execute_capability(
            capability_id,
            user={"id": 2, "email": "deny@blackdark.local", "tier": "free"},
            skip_entitlement=False,
        )
    assert result.get("success") is False
    assert result.get("entitlement", {}).get("allowed") is False


def test_batch11_entitlement_requirement_matrix():
    from cap646.catalog import catalog_by_id, is_external
    from cap646.entitlements import _ORG_PERMISSIONS, _TIER_REQUIREMENTS

    cat = catalog_by_id()
    restricted: list[int] = []
    for cid in _batch_ids():
        row = cat.get(cid, {})
        if is_external(cid):
            restricted.append(cid)
            continue
        if _TIER_REQUIREMENTS.get(cid, "free") != "free":
            restricted.append(cid)
            continue
        if _ORG_PERMISSIONS.get(cid) or row.get("feature_key") or row.get("usage_meter_key"):
            restricted.append(cid)
    assert restricted == [], f"unexpected restricted Batch11 IDs: {restricted}"


def test_manifest_count():
    assert len(_batch_ids()) == 50
