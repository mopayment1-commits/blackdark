"""Wave execution order — dependency-based, frozen against CAP646_GAP_MATRIX."""

from __future__ import annotations

from cap646.catalog import matrix_by_id

WAVE_A: tuple[int, ...] = (
    631, 630, 338, 500, 642, 47, 103, 48, 584, 610, 612, 568, 569, 574, 161, 644, 645, 646,
)

WAVE_B: tuple[int, ...] = (
    17, 629, 245, 60, 86, 88, 126, 205, 235, 252, 263, 85, 124, 5, 279, 354, 615, 581, 591, 592,
)

WAVE_C: tuple[int, ...] = (
    507, 534, 214, 636, 478, 525, 267, 483, 508, 509, 510, 537, 538, 356, 330,
)


def _wave_d_ids() -> tuple[int, ...]:
    covered = set(WAVE_A) | set(WAVE_B) | set(WAVE_C)
    out: list[int] = []
    for cid in range(1, 647):
        if cid in covered:
            continue
        row = matrix_by_id()[cid]
        cls = row.get("final_classification", "")
        if cls in {"DUPLICATE/ALREADY_COVERED", "EXTERNAL/BLOCKED"}:
            continue
        out.append(cid)
    return tuple(out)


WAVE_D: tuple[int, ...] = _wave_d_ids()

USER_FACING: frozenset[int] = frozenset(
    {
        17, 47, 48, 60, 103, 129, 175, 245, 507, 534, 214, 629, 642,
        631, 630, 338, 500, 584, 644, 646,
    }
)

INSTITUTIONAL_ONLY: frozenset[int] = frozenset({568, 569, 574, 161, 645, 644, 646, 103, 641, 638})

EXTERNAL_IDS: frozenset[int] = frozenset({45, 331, 332, 337})

EXTERNAL_EVIDENCE_SLOTS: frozenset[int] = frozenset({645})
SIGNED_INFRA_SLOTS: frozenset[int] = frozenset({644})

WAVES: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("A", WAVE_A),
    ("B", WAVE_B),
    ("C", WAVE_C),
    ("D", WAVE_D),
)

ALL_WAVES: tuple[int, ...] = WAVE_A + WAVE_B + WAVE_C + WAVE_D
