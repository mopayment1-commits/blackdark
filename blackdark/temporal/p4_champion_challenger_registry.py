"""P4 Champion/Challenger atomic requirement registry (selected scope only)."""

from __future__ import annotations

P4_CHAMPION_CHALLENGER_ATOMIC_REQUIREMENT_IDS: tuple[str, ...] = (
    "TEMP-AR-0230",
    "TEMP-AR-0231",
    "TEMP-AR-0232",
)

P4_CHAMPION_CHALLENGER_EXPECTED_ATOMIC_REQUIREMENTS = len(
    P4_CHAMPION_CHALLENGER_ATOMIC_REQUIREMENT_IDS
)
