"""Institutional batch SSOT — 25 capabilities per batch (v6 governing standard)."""

from __future__ import annotations

CAPABILITIES_PER_BATCH: int = 25
TOTAL_CAPABILITIES: int = 826
DEDICATED_RANGE_START: int = 151  # batch07+ generated dedicated wrappers


def total_batch_count() -> int:
    return (TOTAL_CAPABILITIES - 1) // CAPABILITIES_PER_BATCH + 1


def batch_number(capability_id: int) -> int:
    if capability_id < 1 or capability_id > TOTAL_CAPABILITIES:
        raise ValueError(f"capability_id {capability_id} out of range 1–{TOTAL_CAPABILITIES}")
    return (capability_id - 1) // CAPABILITIES_PER_BATCH + 1


def official_batch_name(capability_id: int) -> str:
    return f"batch{batch_number(capability_id):02d}"


def batch_id_range(batch_num: int) -> tuple[int, int]:
    if batch_num < 1 or batch_num > total_batch_count():
        raise ValueError(f"batch_num {batch_num} out of range")
    start = (batch_num - 1) * CAPABILITIES_PER_BATCH + 1
    end = min(batch_num * CAPABILITIES_PER_BATCH, TOTAL_CAPABILITIES)
    return start, end


def batch_ids(batch_num: int) -> frozenset[int]:
    start, end = batch_id_range(batch_num)
    return frozenset(range(start, end + 1))


def all_batch_numbers() -> range:
    return range(1, total_batch_count() + 1)


def legacy_production_batch_for(capability_id: int) -> str | None:
    """Map capability to handcrafted production spine (batch01–03 cover IDs 1–150)."""
    if 1 <= capability_id <= 50:
        return "batch01"
    if 51 <= capability_id <= 100:
        return "batch02"
    if 101 <= capability_id <= 150:
        return "batch03"
    return None


BATCH_RANGE_IDS: frozenset[int] = frozenset(range(DEDICATED_RANGE_START, TOTAL_CAPABILITIES + 1))
