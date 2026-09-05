"""Batch06 strangler spine — all non-reused IDs wired."""

from __future__ import annotations

import pytest

from cap646.batch06_dedicated import BATCH06_REUSED_LINK_IDS, EXPECTED_SURFACE
from cap646.batch06_ids import BATCH06_IDS
from cap646.batch06_strangler_spine import STRANGLER_BUILDERS


def test_strangler_covers_non_reused():
    strangler_ids = set(STRANGLER_BUILDERS)
    reused = set(BATCH06_REUSED_LINK_IDS)
    manifest = set(BATCH06_IDS)
    assert strangler_ids | reused == manifest
    assert strangler_ids & reused == set()


@pytest.mark.parametrize("capability_id", sorted(STRANGLER_BUILDERS))
def test_expected_surface_defined(capability_id: int):
    assert capability_id in EXPECTED_SURFACE
    assert EXPECTED_SURFACE[capability_id]
