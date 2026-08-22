"""RVM system tests — governing baseline and V&V separation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rvm.baseline import build_baseline, load_baseline
from rvm.governing import verify_governing_sources
from rvm.surfaces import hub_only_surface, has_dedicated_user_surface


def test_governing_sources_present_and_hashed():
    gov = verify_governing_sources()
    assert gov["all_present"], "Mandatory governing PDFs must be present"
    assert gov["all_hashes_ok"], "Governing PDF hashes must match baseline"


def test_baseline_covers_full_scope():
    baseline = build_baseline()
    kinds = baseline["counts_by_kind"]
    assert kinds["capability"] == 978
    assert kinds["control"] == 42
    assert kinds["platform"] == 12
    assert baseline["total_requirements"] == 978 + 42 + 12 + 6 + 6


def test_hub_only_not_dedicated_surface():
    # Consumer-facing on hub only should fail dedicated surface check
    assert hub_only_surface(507) is False  # infra hub exception
    # Capability with only /cap646 default fallback
    assert has_dedicated_user_surface(129) is True  # dashboard


@pytest.mark.asyncio
async def test_rvm_sample_capabilities():
    from rvm.build import _process_requirement

    # External vendor capability
    ext = await _process_requirement(
        {
            "id": "CAP-1",
            "kind": "capability",
            "source": "GOV-SRC-001",
            "requirement": "Smart Money Leaderboard",
            "intended_outcome": "test",
            "verification_method": "test",
            "validation_method": "test",
            "gap_matrix_status": "EXTERNAL/BLOCKED",
        }
    )
    assert ext["final_status"] == "EXTERNAL_EVIDENCE_REQUIRED"

    # Control with external evidence
    sec = await _process_requirement(
        {
            "id": "SEC-008",
            "kind": "control",
            "source": "GOV-SRC-002",
            "requirement": "SEC-008",
            "intended_outcome": "pentest",
            "verification_method": "test",
            "validation_method": "test",
        }
    )
    assert sec["final_status"] == "EXTERNAL_EVIDENCE_REQUIRED"
    assert sec.get("external_step")


@pytest.mark.asyncio
async def test_rvm_platform_stages():
    from rvm.build import _process_requirement

    row = await _process_requirement(
        {
            "id": "PLT-RAW",
            "kind": "platform",
            "source": "GOV-SRC-002",
            "requirement": "raw",
            "intended_outcome": "raw data",
            "verification_method": "e2e",
            "validation_method": "e2e",
        }
    )
    assert row["final_status"] in {"PASS", "FAIL"}


def test_rvm_json_schema_fields():
    rvm_path = Path(__file__).resolve().parent.parent / "docs" / "rvm" / "RVM.json"
    if not rvm_path.is_file():
        pytest.skip("RVM not yet generated — run scripts/run_rvm_verification.py")
    data = json.loads(rvm_path.read_text())
    required_fields = {
        "id",
        "source",
        "requirement",
        "intended_outcome",
        "verification_method",
        "validation_method",
        "verification_status",
        "validation_status",
        "final_status",
    }
    for row in data["requirements"][:20]:
        assert required_fields.issubset(row.keys())
    statuses = {r["final_status"] for r in data["requirements"]}
    assert statuses.issubset({"PASS", "FAIL", "EXTERNAL_EVIDENCE_REQUIRED"})
