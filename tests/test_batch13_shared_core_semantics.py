"""Batch13 shared-core semantic distinctness tests."""

from __future__ import annotations

import pytest

from bd_platform.batch13_semantic_engine import CAPABILITY_SEMANTIC_SPECS, compute_semantic_extra, shared_core_ids
from bd_platform.batch13_membership import parameterized_ids


@pytest.mark.parametrize("cap_id", parameterized_ids())
def test_shared_core_semantic_payload(cap_id: int) -> None:
    payload = compute_semantic_extra(cap_id, symbol="ETH", seed={})
    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
    assert payload["semantic_rule"] == spec["rule"]
    assert payload["feature"] == spec["feature"]
    assert payload["formula_visible"] is True


def test_shared_core_count() -> None:
    assert len(shared_core_ids()) == len(parameterized_ids())
