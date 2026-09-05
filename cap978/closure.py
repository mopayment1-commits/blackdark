"""CAP978 institutional closure — 978 capabilities + governing controls + platform chain."""

from __future__ import annotations

from typing import Any

from cap646.institutional_controls import verify_all_controls
from cap646.platform_chain import verify_data_platform_chain
from cap646.triple_closure import _INTERNAL_INCOMPLETE
from cap978.gate_verdict import INSTITUTIONAL_GATE_FAIL, INSTITUTIONAL_GATE_PASS
from cap978.ci_deterministic_closure import ci_deterministic_closure_enabled, verify_functional_ci_deterministic
from cap978.verify import verify_functional_978


async def institutional_closure_978(*, sample: bool = False, ci_deterministic: bool | None = None) -> dict[str, Any]:
    controls = await verify_all_controls()
    chain = await verify_data_platform_chain()

    cap_counts: dict[str, int] = {}
    incomplete: list[int] = []
    ext_counts: dict[str, int] = {}
    # Full: 1..978 (catalog total). Sample: 678 = base 646 + extension 647..678 (CI structural).
    # Project delivery scope is 826 (647..826); IDs 827..978 are full-catalog-only — see cap978.catalog.
    ids = range(1, 979) if not sample else list(range(1, 647)) + list(range(647, 679))
    use_ci_structural = bool(sample and (ci_deterministic if ci_deterministic is not None else ci_deterministic_closure_enabled()))
    verify_fn = verify_functional_ci_deterministic if use_ci_structural else verify_functional_978

    for cid in ids:
        fn = await verify_fn(cid)
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
    verdict = INSTITUTIONAL_GATE_PASS if cap_ok and controls_ok and chain_ok else INSTITUTIONAL_GATE_FAIL

    base_counts = {k: v for k, v in cap_counts.items()}
    return {
        "verdict": verdict,
        "total": 978,
        "verification_mode": "ci_structural_no_network" if use_ci_structural else "live_functional",
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
