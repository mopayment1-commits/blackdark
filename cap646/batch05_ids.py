"""Batch05 ID manifest vs routing spine (avoids circular imports)."""

from __future__ import annotations

# Official catalog rows 201–250 (50 IDs) — RTM / acceptance manifest.
BATCH05_MANIFEST_IDS: frozenset[int] = frozenset(range(201, 251))
OFFICIAL_BATCH05_IDS = BATCH05_MANIFEST_IDS

# Pre-resolved duplicates: gap matrix DUPLICATE/ALREADY_COVERED — must NOT enter batch05 spine.
BATCH05_DUPLICATE_DELEGATION_IDS: frozenset[int] = frozenset({212})

# Runtime + production routing spine (manifest minus duplicate delegation).
BATCH05_IDS: frozenset[int] = BATCH05_MANIFEST_IDS - BATCH05_DUPLICATE_DELEGATION_IDS
