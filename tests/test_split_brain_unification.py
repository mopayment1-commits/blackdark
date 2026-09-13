"""Split-brain remediation — pdf audit path delegates to cap646 production."""

from __future__ import annotations

import pytest

SPLIT_BRAIN_SAMPLE = [1, 3, 17, 45]


@pytest.mark.parametrize("cap_id", SPLIT_BRAIN_SAMPLE)
@pytest.mark.asyncio
async def test_pdf_registry_delegates_to_cap646(cap_id: int):
    from pdf_capability_registry import execute_capability

    result = await execute_capability(cap_id)
    assert result.get("split_brain_unified") is True
    assert result.get("audit_path") == "cap646.runtime.execute_capability"
    assert result.get("ok") is True or result.get("success") is True
