"""P6 closure registry and probe aggregation tests."""

from __future__ import annotations

from blackdark.temporal.p6_closure_verification import evaluate_p6_closure_assertions
from blackdark.temporal.p6_requirement_registry import (
    P6_ATOMIC_REQUIREMENT_IDS,
    P6_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P6_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P6_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
    P6_REQUIREMENT_OWNERS,
)


def test_p6_master_inventory_lock() -> None:
    assert P6_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 28
    assert P6_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS == 28
    assert len(P6_ATOMIC_REQUIREMENT_IDS) == 28
    assert P6_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS == ()
    assert len(P6_REQUIREMENT_OWNERS) == 28


def test_p6_closure_probes_pass() -> None:
    result = evaluate_p6_closure_assertions()
    assert result["closure_assertions"]["P6_CLOSED"] is True
