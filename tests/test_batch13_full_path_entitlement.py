"""Batch13 full-path local integration — cap646 runtime with entitlement checks."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "scripts/partial_batches/batch_13_601_650.json"

PRO_USER = {"id": 1, "email": "batch13-fullpath@blackdark.local", "tier": "pro", "role": "user"}


def _batch_ids() -> list[int]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [int(x) for x in data["capability_ids"]]


@pytest.mark.parametrize("capability_id", _batch_ids())
@pytest.mark.asyncio
async def test_full_path_allow_via_cap646_runtime(capability_id: int) -> None:
    from cap646.runtime import execute_capability

    result = await execute_capability(
        capability_id,
        user=PRO_USER,
        skip_entitlement=False,
        params={"symbol": "BTC"},
    )
    if capability_id in {647, 648, 649, 650}:
        assert result.get("success") is False
        ent = result.get("entitlement") or {}
        inner = result.get("result") or result
        assert ent.get("allowed") is False or inner.get("classification") == "EXTERNAL_DEPENDENCY_BLOCKED"
        return
    assert result.get("success") is True, result
    if capability_id == 613:
        payload = result.get("result") or result
        assert payload.get("canonical_reuse_of") == 88 or result.get("backend_entrypoint") == "cap_088"
        return
    assert result.get("capability_id") == capability_id or (result.get("result") or {}).get("capability_id") == capability_id


@pytest.mark.parametrize("capability_id", _batch_ids())
@pytest.mark.asyncio
async def test_entitlement_denied_before_handler(capability_id: int) -> None:
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
