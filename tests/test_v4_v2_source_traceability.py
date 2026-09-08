"""v4_v2 source traceability — ISO/IEC/IEEE 29148 mapping tests."""

from __future__ import annotations

import json
from pathlib import Path

from bd_platform.v4_v2_source_driven_engineering import (
    BUILDABLE_CLASSIFICATIONS,
    canonical_binding,
    load_implementation_index,
    load_unique_register,
    verify_requirement,
)

ROOT = Path(__file__).resolve().parents[1]


def test_every_buildable_has_source_to_test_trace() -> None:
    index = load_implementation_index()
    gaps: list[str] = []
    for row in load_unique_register()["rows"]:
        uid = row["canonical_requirement_id"]
        if row.get("classification") not in BUILDABLE_CLASSIFICATIONS:
            continue
        binding = index["bindings"][uid]
        if not binding.get("source_aliases"):
            gaps.append(f"{uid}:no_source_aliases")
        for tp in binding.get("test_paths") or []:
            if not (ROOT / tp).is_file():
                gaps.append(f"{uid}:missing_test:{tp}")
        for mp in binding.get("module_paths") or []:
            if mp.endswith(".py") and not (ROOT / mp).is_file():
                gaps.append(f"{uid}:missing_module:{mp}")
    assert gaps == [], gaps[:20]


def test_verify_requirement_trace_fields() -> None:
    row = next(r for r in load_unique_register()["rows"] if r.get("classification") == "BUILDABLE_NOW")
    result = verify_requirement(row["canonical_requirement_id"])
    assert result["ok"] is True
    assert "binding" in result


def test_ledger_arithmetic_after_source_closure() -> None:
    ledger = json.loads(Path("docs/THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json").read_text(encoding="utf-8"))
    v4 = [r for r in ledger["requirements"] if r.get("spec") == "v4_v2"]
    assert len(v4) == 1846
    remaining = [
        r
        for r in v4
        if r.get("current_state")
        in {"PARTIALLY_BUILT_VALID", "PARTIALLY_IMPLEMENTED", "UNIMPLEMENTED", "UNVERIFIED", "UNWIRED"}
    ]
    assert len(remaining) == 0


def test_maturity_gated_have_local_prerequisites() -> None:
    from bd_platform import v4_v2_phase1_engineering_spine as phase1

    for uid in phase1.MATURITY_GATED_REQUIREMENT_IDS:
        result = verify_requirement(uid)
        assert result.get("closure_state") == "MATURITY_GATED"
        assert result["ok"] is True


def test_canonical_binding_enforcement_tiers() -> None:
    buildable = next(r for r in load_unique_register()["rows"] if r.get("classification") == "BUILDABLE_NOW")
    b = canonical_binding(buildable["canonical_requirement_id"])
    assert b.enforcement_tier in {"REJECT", "PROBE", "DOCUMENT_ONLY"}
    assert b.implementation_intended is True
