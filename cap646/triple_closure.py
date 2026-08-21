"""Triple reference closure — CAP646 + Governing Controls + Data Platform."""

from __future__ import annotations

from typing import Any

from cap646.dod import verify_dod
from cap646.functional_dod import verify_functional
from cap646.institutional_controls import verify_all_controls
from cap646.platform_chain import verify_data_platform_chain


async def verify_capability_triple(capability_id: int) -> dict[str, Any]:
    structural = await verify_dod(capability_id)
    functional = await verify_functional(capability_id)
    verdict = "VERIFIED_COMPLETE"
    if structural["verdict"] not in {"VERIFIED_COMPLETE", "CANONICALLY_COVERED", "EXTERNAL_BLOCKED", "EXTERNAL_EVIDENCE_REQUIRED"}:
        verdict = structural["verdict"]
    elif functional["verdict"] not in {"VERIFIED_COMPLETE", "CANONICALLY_COVERED", "EXTERNAL_BLOCKED", "EXTERNAL_EVIDENCE_REQUIRED"}:
        verdict = functional["verdict"]
    return {
        "id": capability_id,
        "verdict": verdict,
        "structural": structural,
        "functional": functional,
    }


async def triple_institutional_closure(*, sample_cap_ids: list[int] | None = None) -> dict[str, Any]:
    controls = await verify_all_controls()
    chain = await verify_data_platform_chain()

    cap_counts: dict[str, int] = {}
    functional_incomplete: list[int] = []
    ids = sample_cap_ids or list(range(1, 647))

    for cid in ids:
        fn = await verify_functional(cid)
        cap_counts[fn["verdict"]] = cap_counts.get(fn["verdict"], 0) + 1
        if fn["verdict"] == "FUNCTIONALLY_INCOMPLETE":
            functional_incomplete.append(cid)

    cap646_ok = cap_counts.get("FUNCTIONALLY_INCOMPLETE", 0) == 0 and cap_counts.get("NOT_READY", 0) == 0
    controls_ok = controls.get("internal_closure", False)
    chain_ok = chain.get("internal_closure", False)

    verdict = "VERIFIED COMPLETE" if cap646_ok and controls_ok and chain_ok else "NOT READY"

    return {
        "verdict": verdict,
        "cap646": {
            "counts": cap_counts,
            "functional_incomplete_sample": functional_incomplete[:25],
            "internal_closure": cap646_ok,
        },
        "governing_controls": controls,
        "data_platform_chain": chain,
        "references": {
            "cap646": "docs/cap646/CAP646_CATALOG.json",
            "governing": "docs/governing/INSTITUTIONAL_GOVERNING_REFERENCE.md",
            "data_platform": "docs/governing/DATA_PLATFORM_GOVERNING_REFERENCE.md",
        },
    }
