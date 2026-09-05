#!/usr/bin/env python3
"""Canonical Batch05 per-ID classification partition (IDs 201-250).

#212 is CLOSED_DUPLICATE_DELEGATION only — never also CLOSED_REUSED_LINK.
residual_7 is a disposition group (6 REUSED-LINK + 1 DUPLICATE), not a class.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

EXPECTED_RANGE = frozenset(range(201, 251))
CLOSED_REUSED_LINK_IDS = frozenset({206, 214, 226, 228, 232, 245})
CLOSED_DUPLICATE_DELEGATION_IDS = frozenset({212})
STRANGLER_IDS = EXPECTED_RANGE - CLOSED_REUSED_LINK_IDS - CLOSED_DUPLICATE_DELEGATION_IDS
RESIDUAL_7_IDS = CLOSED_REUSED_LINK_IDS | CLOSED_DUPLICATE_DELEGATION_IDS
CANONICAL_CLASSES = (
    "STRANGLER",
    "CLOSED_REUSED_LINK",
    "CLOSED_DUPLICATE_DELEGATION",
)


def class_for_id(cid: int) -> str:
    if cid in CLOSED_DUPLICATE_DELEGATION_IDS:
        return "CLOSED_DUPLICATE_DELEGATION"
    if cid in CLOSED_REUSED_LINK_IDS:
        return "CLOSED_REUSED_LINK"
    if cid in EXPECTED_RANGE:
        return "STRANGLER"
    raise ValueError(f"id {cid} outside Batch05 range 201-250")


def partition_from_rows(rows: list[dict[str, Any]], decision_key: str = "duplicate_decision") -> dict[str, Any]:
    seen: dict[int, list[str]] = {cid: [] for cid in EXPECTED_RANGE}
    for row in rows:
        cid = int(row["capability_id"])
        decision = row.get(decision_key)
        if cid in seen and decision in CANONICAL_CLASSES:
            seen[cid].append(str(decision))

    duplicate_classification_ids = sorted(cid for cid, labels in seen.items() if len(labels) != 1)
    missing_ids = sorted(cid for cid, labels in seen.items() if not labels)
    extra_ids = sorted({int(r["capability_id"]) for r in rows} - EXPECTED_RANGE)
    by_class: dict[str, list[int]] = {name: [] for name in CANONICAL_CLASSES}
    for cid, labels in seen.items():
        if len(labels) == 1:
            by_class[labels[0]].append(cid)
    for name in by_class:
        by_class[name] = sorted(by_class[name])

    counts = {name: len(ids) for name, ids in by_class.items()}
    unique_ids = len(EXPECTED_RANGE)
    classification_total = sum(counts.values())
    assertions = {
        "unique_ids": unique_ids,
        "duplicate_classification_ids": duplicate_classification_ids,
        "missing_ids": missing_ids,
        "extra_ids": extra_ids,
        "classification_total": classification_total,
        "counts_match_expected": counts
        == {
            "STRANGLER": 43,
            "CLOSED_REUSED_LINK": 6,
            "CLOSED_DUPLICATE_DELEGATION": 1,
        },
        "id_212_class": class_for_id(212),
        "id_212_not_reused_link": 212 not in by_class["CLOSED_REUSED_LINK"],
        "residual_7_is_not_a_classification": True,
        "all_pass": (
            unique_ids == 50
            and classification_total == 50
            and duplicate_classification_ids == []
            and missing_ids == []
            and extra_ids == []
            and counts["STRANGLER"] == 43
            and counts["CLOSED_REUSED_LINK"] == 6
            and counts["CLOSED_DUPLICATE_DELEGATION"] == 1
            and by_class["CLOSED_DUPLICATE_DELEGATION"] == [212]
            and by_class["CLOSED_REUSED_LINK"] == sorted(CLOSED_REUSED_LINK_IDS)
        ),
    }
    return {
        "STRANGLER": {"count": counts["STRANGLER"], "ids": by_class["STRANGLER"]},
        "CLOSED_REUSED_LINK": {
            "count": counts["CLOSED_REUSED_LINK"],
            "ids": by_class["CLOSED_REUSED_LINK"],
            "note": "#212 is NOT in this list",
        },
        "CLOSED_DUPLICATE_DELEGATION": {
            "count": counts["CLOSED_DUPLICATE_DELEGATION"],
            "ids": by_class["CLOSED_DUPLICATE_DELEGATION"],
        },
        "residual_7_disposition_group": {
            "note": "Disposition group only — 6 CLOSED_REUSED_LINK + 1 CLOSED_DUPLICATE_DELEGATION. Not a seventh class.",
            "ids": sorted(RESIDUAL_7_IDS),
            "count": 7,
        },
        "counts": counts,
        "assertions": assertions,
    }


def assert_runtime_sets(reused_link_ids: frozenset[int], duplicate_ids: frozenset[int], manifest_ids: frozenset[int]) -> None:
    assert manifest_ids == EXPECTED_RANGE
    assert duplicate_ids == CLOSED_DUPLICATE_DELEGATION_IDS
    assert reused_link_ids == CLOSED_REUSED_LINK_IDS
    assert reused_link_ids.isdisjoint(duplicate_ids)
    assert Counter(
        [
            *["STRANGLER"] * len(manifest_ids - reused_link_ids - duplicate_ids),
            *["CLOSED_REUSED_LINK"] * len(reused_link_ids),
            *["CLOSED_DUPLICATE_DELEGATION"] * len(duplicate_ids),
        ]
    ) == Counter({"STRANGLER": 43, "CLOSED_REUSED_LINK": 6, "CLOSED_DUPLICATE_DELEGATION": 1})
