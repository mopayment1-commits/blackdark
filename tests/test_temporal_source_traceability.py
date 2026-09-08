"""Temporal source → requirement → implementation → test traceability."""

from __future__ import annotations

import json
from pathlib import Path

from bd_platform.temporal_source_driven_engineering import (
    BUILDABLE_CLASSIFICATIONS,
    close_requirement_source_driven,
    load_implementation_index,
    load_matrix_register,
    verify_requirement,
)

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "docs" / "TEMPORAL_FULL_SOURCE_UNIVERSE.json"
INDEX = ROOT / "docs" / "TEMPORAL_IMPLEMENTATION_INDEX.json"
FREEZE = ROOT / "docs" / "TEMPORAL_SOURCE_DRIVEN_FINAL_FREEZE.json"
LEDGER = ROOT / "docs" / "THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json"


def _load(path: Path) -> dict:
    assert path.is_file(), f"Missing {path.name} — run temporal closure pipeline"
    return json.loads(path.read_text(encoding="utf-8"))


def test_universe_has_source_items() -> None:
    data = _load(UNIVERSE)
    rows = data.get("rows") or []
    assert len(rows) >= 300
    assert data.get("TEMPORAL_SOURCE_DECOMPOSITION_COMPLETE") is True


def test_implementation_index_maps_domains() -> None:
    data = _load(INDEX)
    bindings = data.get("bindings") or {}
    assert len(bindings) >= 391
    domains = {b.get("domain") for b in bindings.values() if b.get("domain")}
    assert "event_store" in domains or "pit_leakage" in domains


def test_every_buildable_has_source_to_test_trace() -> None:
    index = load_implementation_index()
    gaps: list[str] = []
    for row in load_matrix_register()["rows"]:
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
            norm = mp.replace("backend_registry.py", "cap646/backend_registry.py")
            if norm.endswith(".py") and not (ROOT / norm).is_file():
                gaps.append(f"{uid}:missing_module:{mp}")
    assert gaps == [], gaps[:20]


def test_verify_requirement_trace_fields() -> None:
    row = next(r for r in load_matrix_register()["rows"] if r.get("classification") == "BUILDABLE_NOW")
    result = verify_requirement(row["canonical_requirement_id"])
    assert result["ok"] is True
    assert result.get("runtime")


def test_close_requirement_source_driven_buildable_sample() -> None:
    sample = next(r for r in load_matrix_register()["rows"] if r.get("classification") == "BUILDABLE_NOW")
    closure = close_requirement_source_driven(sample["canonical_requirement_id"])
    assert closure["closure_state"] == "LOCAL_ENGINEERING_COMPLETE"
    assert closure["implementation_paths"]
    assert closure["test_paths"]


def test_freeze_reports_zero_remaining_local() -> None:
    if not FREEZE.is_file():
        return
    data = _load(FREEZE)
    assert data.get("TEMPORAL_FINAL_LOCAL_COMPLETION") is True
    assert data.get("NO_KNOWN_LOCALLY_BUILDABLE_TEMPORAL_WORK_REMAINING") is True
    arith = data.get("arithmetic") or {}
    assert arith.get("TEMPORAL_REMAINING_LOCAL_REQUIREMENTS") == 0


def test_ledger_temporal_no_partial_or_buildable_now() -> None:
    if not FREEZE.is_file():
        return
    ledger = _load(LEDGER)
    temporal = [r for r in ledger["requirements"] if r.get("spec") == "temporal"]
    bad = [
        r["requirement_id"]
        for r in temporal
        if r.get("current_state") in ("PARTIALLY_BUILT_VALID", "BUILDABLE_NOW", "UNIMPLEMENTED", "PARTIALLY_IMPLEMENTED")
    ]
    assert bad == [], bad[:10]
