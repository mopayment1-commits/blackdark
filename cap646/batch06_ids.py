"""Batch06 ID manifest vs routing spine (official catalog 251–300)."""

from __future__ import annotations

BATCH06_MANIFEST_IDS: frozenset[int] = frozenset(range(251, 301))
OFFICIAL_BATCH06_IDS = BATCH06_MANIFEST_IDS

# No duplicate-delegation exclusions from manifest — REUSED-LINK facades remain addressable.
BATCH06_DUPLICATE_DELEGATION_IDS: frozenset[int] = frozenset()

BATCH06_IDS: frozenset[int] = BATCH06_MANIFEST_IDS - BATCH06_DUPLICATE_DELEGATION_IDS
