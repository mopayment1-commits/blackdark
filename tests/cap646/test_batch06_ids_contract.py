"""Batch06 ID manifest contract tests."""

from __future__ import annotations

from cap646.batch06_ids import BATCH06_IDS, BATCH06_MANIFEST_IDS, OFFICIAL_BATCH06_IDS


def test_batch06_manifest_is_251_300():
    assert BATCH06_MANIFEST_IDS == frozenset(range(251, 301))
    assert OFFICIAL_BATCH06_IDS == BATCH06_MANIFEST_IDS
    assert len(BATCH06_MANIFEST_IDS) == 50


def test_batch06_spine_equals_manifest():
    assert BATCH06_IDS == BATCH06_MANIFEST_IDS
    assert len(BATCH06_IDS) == 50
