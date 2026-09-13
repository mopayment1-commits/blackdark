"""Regression: Arkham connector validates address before URL path join."""

from __future__ import annotations

import pytest

from blackdark.ingestion.arkham_connector import _safe_address_segment


def test_safe_address_segment_accepts_alphanumeric():
    assert _safe_address_segment("0xAbCd1234") == "0xAbCd1234"


def test_safe_address_segment_rejects_traversal():
    with pytest.raises(ValueError):
        _safe_address_segment("../evil")
