"""P5 closure registry and probe aggregation tests."""

from __future__ import annotations

from blackdark.temporal.p5_closure_verification import evaluate_p5_closure_assertions
from blackdark.temporal.p5_requirement_registry import (
    P5_ATOMIC_REQUIREMENT_IDS,
    P5_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P5_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
    P5_REQUIREMENT_OWNERS,
)


def test_p5_master_inventory_lock() -> None:
    assert P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 43
    assert P5_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS == 43
    assert len(P5_ATOMIC_REQUIREMENT_IDS) == 43
    assert P5_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS == ("TEMP-AR-0261",)
    assert len(P5_REQUIREMENT_OWNERS) == 43


def test_p5_closure_probes_pass() -> None:
    result = evaluate_p5_closure_assertions()
    assert result["closure_assertions"]["P5_CLOSED"] is True
