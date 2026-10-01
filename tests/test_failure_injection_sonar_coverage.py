"""Behavioral coverage for failure.injection (engineering fault paths)."""

from __future__ import annotations

import pytest

from failure.injection import FaultKind, inject_fault


@pytest.mark.parametrize(
    "kind",
    [
        FaultKind.STALE_DATA,
        FaultKind.PARTIAL_DATA,
        FaultKind.CONFLICTING_DATA,
        FaultKind.AI_FAILURE,
        FaultKind.LOST_RESPONSE,
        FaultKind.PROVIDER_FAILURE,
        FaultKind.RECONCILIATION,
        FaultKind.HTTP_429,
        FaultKind.OFFLINE,
        FaultKind.TIMEOUT,
    ],
)
def test_inject_fault_returns_dict(kind: FaultKind):
    out = inject_fault(kind, correlation_id="sonar-cov")
    assert isinstance(out, dict)
    assert out
