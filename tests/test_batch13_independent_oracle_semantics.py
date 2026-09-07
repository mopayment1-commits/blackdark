"""Independent oracle parity for Batch13 shared core."""

from __future__ import annotations

import math

import pytest

from bd_platform.batch13_semantic_engine import CAPABILITY_SEMANTIC_SPECS, compute_semantic_extra
from bd_platform.batch13_membership import parameterized_ids
from tests.batch13_independent_semantic_oracles import independent_primary


@pytest.mark.parametrize("cap_id", parameterized_ids())
def test_oracle_matches_production(cap_id: int) -> None:
    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
    inputs = dict(spec["defaults"])
    rule = spec["rule"]
    expected = independent_primary(cap_id, rule, inputs, symbol="ETH")
    payload = compute_semantic_extra(cap_id, symbol="ETH", seed={})
    actual = payload[rule]
    assert math.isfinite(float(actual))
    assert math.isfinite(float(expected))
    assert actual == expected
