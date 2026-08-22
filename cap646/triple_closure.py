"""Triple reference closure — CAP646 + Governing Controls + Data Platform."""

from __future__ import annotations

from typing import Any

from cap646.dod import verify_dod
from cap646.functional_dod import verify_functional
from cap646.institutional_controls import verify_all_controls
from cap646.platform_chain import verify_data_platform_chain


_INTERNAL_INCOMPLETE = frozenset(
    {"FUNCTIONALLY_INCOMPLETE", "NOT_READY", "INTERNAL_PARTIAL", "INTERNAL_NOT_IMPLEMENTED"}
)


async def verify_capability_triple(capability_id: int) -> dict[str, Any]:
    structural = await verify_dod(capability_id)
    functional = await verify_functional(capability_id)
    verdict = "VERIFIED_COMPLETE"
    if structural["verdict"] in _INTERNAL_INCOMPLETE:
        verdict = structural["verdict"]
    elif functional["verdict"] in _INTERNAL_INCOMPLETE:
        verdict = functional["verdict"]
    return {
        "id": capability_id,
        "verdict": verdict,
        "structural": structural,
        "functional": functional,
    }


def _tally(rows: list[dict[str, Any]], key: str = "verdict") -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        v = str(row.get(key) or row.get("status") or "UNKNOWN")
        counts[v] = counts.get(v, 0) + 1
    return counts


async def triple_institutional_closure(*, sample_cap_ids: list[int] | None = None) -> dict[str, Any]:
    controls = await verify_all_controls()
    chain = await verify_data_platform_chain()

    cap_counts: dict[str, int] = {}
    functional_incomplete: list[int] = []
    ids = sample_cap_ids or list(range(1, 647))

    for cid in ids:
        fn = await verify_functional(cid)
        cap_counts[fn["verdict"]] = cap_counts.get(fn["verdict"], 0) + 1
        if fn["verdict"] in _INTERNAL_INCOMPLETE:
            functional_incomplete.append(cid)

    control_counts = controls.get("counts") or {}
    internal_incomplete = sum(control_counts.get(k, 0) for k in _INTERNAL_INCOMPLETE)

    cap646_ok = all(cap_counts.get(k, 0) == 0 for k in _INTERNAL_INCOMPLETE)
    controls_ok = internal_incomplete == 0
    chain_ok = chain.get("internal_closure", False)

    verdict = "VERIFIED COMPLETE" if cap646_ok and controls_ok and chain_ok else "NOT READY"

    return {
        "verdict": verdict,
        "cap646": {
            "counts": cap_counts,
            "functional_incomplete_sample": functional_incomplete[:25],
            "internal_closure": cap646_ok,
            "INTERNAL_PARTIAL": cap_counts.get("INTERNAL_PARTIAL", 0),
            "INTERNAL_NOT_IMPLEMENTED": cap_counts.get("INTERNAL_NOT_IMPLEMENTED", 0),
            "FUNCTIONALLY_INCOMPLETE": cap_counts.get("FUNCTIONALLY_INCOMPLETE", 0),
        },
        "governing_controls": controls,
        "data_platform_chain": chain,
        "summary": {
            "INTERNAL_PARTIAL": cap_counts.get("INTERNAL_PARTIAL", 0),
            "INTERNAL_NOT_IMPLEMENTED": cap_counts.get("INTERNAL_NOT_IMPLEMENTED", 0),
            "FUNCTIONALLY_INCOMPLETE": cap_counts.get("FUNCTIONALLY_INCOMPLETE", 0),
            "EXTERNAL_BLOCKED": cap_counts.get("EXTERNAL_BLOCKED", 0) + control_counts.get("EXTERNAL_BLOCKED", 0),
            "VERIFIED_COMPLETE": cap_counts.get("VERIFIED_COMPLETE", 0),
        },
        "references": {
            "cap646": "docs/cap646/CAP646_CATALOG.json",
            "governing": "docs/governing/INSTITUTIONAL_GOVERNING_REFERENCE.md",
            "data_platform": "docs/governing/DATA_PLATFORM_GOVERNING_REFERENCE.md",
        },
    }
