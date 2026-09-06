"""Batch08 full-path local integration — cap646 runtime with entitlement checks."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts" / "partial_batches" / "batch_08_351_400.json"

PRO_USER = {"id": 1, "email": "batch08-fullpath@blackdark.local", "tier": "pro", "role": "user"}


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
    if result.get("requested_capability_id") == capability_id:
        assert result.get("duplicate_of") is not None
        assert result.get("classification") == "DUPLICATE/ALREADY_COVERED"
    else:
        assert result.get("capability_id") == capability_id


@pytest.mark.parametrize("capability_id", _batch_ids())
@pytest.mark.asyncio
async def test_full_path_gateway_execute(capability_id: int):
    from cap646.institutional_gateway import gateway_execute

    result = await gateway_execute(
        capability_id,
        user=PRO_USER,
        params={"symbol": "BTC"},
    )
    assert result.get("success") is True, result
    assert "gateway" in result


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
    assert "surface" not in result or result.get("classification") != "PRODUCTION-ALIGNED"


@pytest.mark.parametrize("capability_id", [351, 369, 379])
@pytest.mark.asyncio
async def test_execute_unified_get_path(capability_id: int):
    from cap978.unified import execute_unified

    result = await execute_unified(
        capability_id,
        user=PRO_USER,
        params={"symbol": "BTC", "tier": "pro"},
    )
    assert result.get("success") is True, result


def test_manifest_count():
    assert len(_batch_ids()) == 50
