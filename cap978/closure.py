"""CAP978 institutional closure — 978 capabilities + governing controls + platform chain."""

from __future__ import annotations

from typing import Any

from cap646.institutional_controls import verify_all_controls
from cap646.platform_chain import verify_data_platform_chain
from cap646.triple_closure import _INTERNAL_INCOMPLETE
from cap978.verify import verify_functional_978


async def institutional_closure_978(*, sample: bool = False) -> dict[str, Any]:
    controls = await verify_all_controls()
    chain = await verify_data_platform_chain()

    cap_counts: dict[str, int] = {}
    incomplete: list[int] = []
    ext_counts: dict[str, int] = {}
    ids = range(1, 979) if not sample else list(range(1, 647)) + list(range(647, 679))

    for cid in ids:
        fn = await verify_functional_978(cid)
        cap_counts[fn["verdict"]] = cap_counts.get(fn["verdict"], 0) + 1
        if cid >= 647:
            ext_counts[fn["verdict"]] = ext_counts.get(fn["verdict"], 0) + 1
        if fn["verdict"] in _INTERNAL_INCOMPLETE:
            incomplete.append(cid)

    control_counts = controls.get("counts") or {}
    internal_incomplete = sum(control_counts.get(k, 0) for k in _INTERNAL_INCOMPLETE)
    cap_ok = all(cap_counts.get(k, 0) == 0 for k in _INTERNAL_INCOMPLETE)
    controls_ok = internal_incomplete == 0
    chain_ok = chain.get("internal_closure", False)
    verdict = "VERIFIED COMPLETE" if cap_ok and controls_ok and chain_ok else "NOT READY"

    base_counts = {k: v for k, v in cap_counts.items()}
    return {
        "verdict": verdict,
        "total": 978,
        "cap978": {
            "counts": cap_counts,
            "base_646": base_counts,
            "extension_647_978": ext_counts,
            "incomplete_sample": incomplete[:40],
            "internal_closure": cap_ok,
            "INTERNAL_PARTIAL": cap_counts.get("INTERNAL_PARTIAL", 0),
            "INTERNAL_NOT_IMPLEMENTED": cap_counts.get("INTERNAL_NOT_IMPLEMENTED", 0),
            "FUNCTIONALLY_INCOMPLETE": cap_counts.get("FUNCTIONALLY_INCOMPLETE", 0),
        },
        "governing_controls": controls,
        "data_platform_chain": chain,
        "references": {
            "cap978": "docs/cap978/CAP978_CATALOG.json",
            "cap646": "docs/cap646/CAP646_CATALOG.json",
            "governing": "docs/governing/INSTITUTIONAL_GOVERNING_REFERENCE.md",
            "data_platform": "docs/governing/DATA_PLATFORM_GOVERNING_REFERENCE.md",
            "source_pdf": "Project_978_Capabilities_Grouped_d117.pdf",
        },
    }
