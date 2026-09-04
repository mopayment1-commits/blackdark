"""Batch05 acceptance contract — ISO 29148 triple-match guard."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"
RULE_PROOF = ROOT / "docs/BATCH05_RULE_COUNT_ASSERT_PROOF.txt"
MECE_OVERLAP = ROOT / "docs/BATCH05_MECE_OVERLAP_214_245_DECISION.json"


def test_acceptance_covers_50_ids():
    doc = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    assert doc["pre_probe"] is True
    assert len(doc["rows"]) == 50
    ids = {r["capability_id"] for r in doc["rows"]}
    assert ids == set(range(201, 251))


def test_rule_count_proof_file():
    assert RULE_PROOF.is_file()
    text = RULE_PROOF.read_text(encoding="utf-8")
    assert "assert_rule_count_triple_match: end" in text
    assert text.count(" OK") >= 50


@pytest.mark.parametrize("capability_id", list(range(201, 251)))
def test_each_row_has_domain_rules(capability_id: int):
    doc = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    row = next(r for r in doc["rows"] if r["capability_id"] == capability_id)
    assert row["domain_rules"], f"ID {capability_id}: domain_rules must not be empty"
    assert row["expected_surface"]
    assert row["status"] in {
        "NOT_COMPLETE",
        "REUSED-LINK",
        "PRODUCTION-ALIGNED",
        "OVERLAP-PARTIAL",
        "PAID_VENDOR_DESIGNED",
    }


def test_cap214_reused_link_batch01():
    doc = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    row = next(r for r in doc["rows"] if r["capability_id"] == 214)
    assert row["status"] == "REUSED-LINK"
    assert row["production_spine"] == "batch01"
    assert row["binding_function"] == "_cap214_watchlists"
    assert row["time_decision"] == "Migrate"
    fields = {r["field"] for r in row["domain_rules"]}
    assert "catalog_link.binding" in fields
    assert "watchlists.count" in fields


def test_cap245_reused_link_batch01():
    doc = json.loads(ACCEPTANCE.read_text(encoding="utf-8"))
    row = next(r for r in doc["rows"] if r["capability_id"] == 245)
    assert row["status"] == "REUSED-LINK"
    assert row["production_spine"] == "batch01"
    assert row["functional_gap"]["catalog_name"] == "Market Health & Freshness"
    assert row["time_decision"] == "Migrate"


def test_mece_overlap_decision_exists():
    doc = json.loads(MECE_OVERLAP.read_text(encoding="utf-8"))
    assert len(doc["pairs"]) == 2
    for pair in doc["pairs"]:
        assert pair["time_decision"] == "Migrate"
        assert pair["closure_status"] == "REUSED-LINK"
