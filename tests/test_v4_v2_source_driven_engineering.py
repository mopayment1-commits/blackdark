"""v4_v2 source-driven engineering tests."""

from __future__ import annotations

import json
from pathlib import Path

from bd_platform.v4_v2_persistent_registries import (
    enforce_source_rights,
    lineage_registry_status,
    pit_registry_status,
    register_lineage,
    register_source_rights,
    resolve_lineage,
)
from bd_platform.v4_v2_source_driven_engineering import (
    BUILDABLE_CLASSIFICATIONS,
    canonical_binding,
    close_requirement_source_driven,
    load_implementation_index,
    load_unique_register,
    resolve_unique_id,
    source_driven_status,
    verify_buildable_universe,
    verify_requirement,
)
from temporal_leakage_firewall import TemporalLeakageError, assert_no_temporal_leakage


def test_source_driven_status_bootstraps_registries() -> None:
    status = source_driven_status()
    assert status["live_promotion"] is False
    assert status["lineage"]["row_count"] >= 0
    assert status["source_rights"]["row_count"] >= 0


def test_persistent_lineage_and_rights_enforcement() -> None:
    register_lineage(entity_type="dataset", entity_id="test_dataset", version="v1")
    chain = resolve_lineage(entity_type="dataset", entity_id="test_dataset")
    assert chain
    register_source_rights(source_id="test_source", redistribution=False)
    blocked = enforce_source_rights(source_id="test_source", operation="redistribute")
    assert blocked["allowed"] is False
    allowed = enforce_source_rights(source_id="test_source", operation="read")
    assert allowed["allowed"] is True


def test_source_alias_resolution_roundtrip() -> None:
    unique = load_unique_register()
    row = unique["rows"][0]
    alias = row["source_aliases"][0]
    uid = resolve_unique_id(alias)
    assert uid == row["canonical_requirement_id"]


def test_implementation_index_covers_all_unique_ids() -> None:
    index = load_implementation_index()
    bindings = index.get("bindings", {})
    unique_ids = {r["canonical_requirement_id"] for r in load_unique_register()["rows"]}
    assert len(bindings) == len(unique_ids)
    assert set(bindings) == unique_ids


def test_buildable_requirements_have_bindings() -> None:
    index = load_implementation_index()
    for row in load_unique_register()["rows"]:
        if row.get("classification") not in BUILDABLE_CLASSIFICATIONS:
            continue
        binding = index["bindings"][row["canonical_requirement_id"]]
        assert binding["module_paths"]
        assert binding["test_paths"]


def test_verify_buildable_universe_passes() -> None:
    report = verify_buildable_universe()
    assert report["ok"] is True, report.get("failures", [])[:10]


def test_pit_firewall_rejects_lookahead_independently() -> None:
    assert_no_temporal_leakage(
        event_time="2026-01-01T00:00:00+00:00",
        evaluation_cutoff="2026-01-02T00:00:00+00:00",
        context="valid_pit",
    )
    try:
        assert_no_temporal_leakage(
            event_time="2026-01-03T00:00:00+00:00",
            evaluation_cutoff="2026-01-02T00:00:00+00:00",
            context="lookahead_probe",
        )
        raise AssertionError("expected TemporalLeakageError")
    except TemporalLeakageError:
        pass


def test_close_requirement_source_driven_buildable_sample() -> None:
    sample = next(r for r in load_unique_register()["rows"] if r.get("classification") == "BUILDABLE_NOW")
    closure = close_requirement_source_driven(sample["canonical_requirement_id"])
    assert closure["closure_state"] == "LOCAL_ENGINEERING_COMPLETE"
    assert closure["implementation_paths"]


def test_full_source_universe_artifact_exists() -> None:
    path = Path("docs/V4_V2_FULL_SOURCE_UNIVERSE.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["V4_V2_SOURCE_DECOMPOSITION_COMPLETE"] is True
    assert payload["source_item_count"] > 2000
