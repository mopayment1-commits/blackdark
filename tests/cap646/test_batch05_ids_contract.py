"""Contract tests for batch05 ID manifest and routing spine (coverage + regression guard)."""

from __future__ import annotations

import pytest

from cap646.batch05_dedicated import (
    BATCH05_DEDICATED_IDS,
    BATCH05_REUSED_LINK_BATCH01_IDS,
    BATCH05_REUSED_LINK_BATCH02_IDS,
    BATCH05_REUSED_LINK_INTERNAL_IDS,
    BATCH05_REUSED_LINK_IDS,
    EXPECTED_SURFACE,
)
from cap646.batch05_ids import (
    BATCH05_DUPLICATE_DELEGATION_IDS,
    BATCH05_IDS,
    BATCH05_MANIFEST_IDS,
    OFFICIAL_BATCH05_IDS,
)
from cap646.batch05_production import BATCH05_IDS as PROD_BATCH05_IDS


def test_batch05_manifest_is_official_range():
    assert OFFICIAL_BATCH05_IDS == BATCH05_MANIFEST_IDS
    assert OFFICIAL_BATCH05_IDS == frozenset(range(201, 251))
    assert len(OFFICIAL_BATCH05_IDS) == 50


def test_batch05_duplicate_delegation_excluded_from_routing_spine():
    assert BATCH05_DUPLICATE_DELEGATION_IDS == frozenset({212})
    assert 212 in OFFICIAL_BATCH05_IDS
    assert 212 not in BATCH05_IDS
    assert len(BATCH05_IDS) == 49


def test_batch05_production_spine_matches_ids_module():
    assert PROD_BATCH05_IDS == BATCH05_IDS


def test_batch05_dedicated_ids_match_routing_spine():
    assert BATCH05_DEDICATED_IDS == BATCH05_IDS


def test_batch05_reused_link_partition():
    assert BATCH05_REUSED_LINK_IDS == (
        BATCH05_REUSED_LINK_BATCH01_IDS
        | BATCH05_REUSED_LINK_BATCH02_IDS
        | BATCH05_REUSED_LINK_INTERNAL_IDS
    )
    assert BATCH05_REUSED_LINK_BATCH01_IDS == frozenset({214, 245})
    assert BATCH05_REUSED_LINK_BATCH02_IDS == frozenset({206, 228, 226})
    assert BATCH05_REUSED_LINK_INTERNAL_IDS == frozenset({232})
    assert len(BATCH05_REUSED_LINK_IDS) == 6
    for cid in BATCH05_REUSED_LINK_IDS:
        assert cid in BATCH05_IDS
        assert cid in EXPECTED_SURFACE


def test_batch05_duplicate_not_in_reused_link():
    assert BATCH05_DUPLICATE_DELEGATION_IDS.isdisjoint(BATCH05_REUSED_LINK_IDS)


@pytest.mark.parametrize("capability_id", sorted(BATCH05_IDS))
def test_batch05_expected_surface_registered(capability_id: int):
    assert capability_id in EXPECTED_SURFACE
    assert isinstance(EXPECTED_SURFACE[capability_id], str)
    assert EXPECTED_SURFACE[capability_id]


def test_batch05_manifest_minus_duplicate_equals_spine():
    assert BATCH05_MANIFEST_IDS - BATCH05_DUPLICATE_DELEGATION_IDS == BATCH05_IDS
