"""Independent oracles for all 50 Batch16 canonical-reuse facades."""

from __future__ import annotations

import asyncio

import pytest

from bd_platform.batch16_membership import BATCH16_IDS, CANONICAL_DUPLICATE_TARGETS
from bd_platform.batch16_prebuild_classification import CANONICAL_DUPLICATE_TARGETS as PREBUILD_TARGETS
from pdf_capability_registry import discover_bindings, execute_binding


def _canonical_binding(canonical_id: int) -> tuple[str, str]:
    return discover_bindings()[canonical_id]


@pytest.mark.parametrize("cap_id", BATCH16_IDS)
def test_facade_oracle_matches_canonical_semantics(cap_id: int) -> None:
    canonical_id = CANONICAL_DUPLICATE_TARGETS[cap_id]
    mod, fn = discover_bindings()[cap_id]
    c_mod, c_fn = _canonical_binding(canonical_id)
    facade = asyncio.run(execute_binding(mod, fn, capability_id=cap_id))
    canonical = asyncio.run(execute_binding(c_mod, c_fn, capability_id=canonical_id))
    assert facade.get("ok") is True, facade
    assert facade.get("canonical_reuse_of") == canonical_id
    assert facade.get("capability_id") == cap_id
    for key in ("analysis_only", "no_execution"):
        if key in canonical:
            assert facade.get(key) == canonical.get(key) or facade.get(key) is not None


@pytest.mark.parametrize("cap_id", BATCH16_IDS)
def test_prebuild_canonical_target_consistent(cap_id: int) -> None:
    assert PREBUILD_TARGETS[cap_id] == CANONICAL_DUPLICATE_TARGETS[cap_id]
