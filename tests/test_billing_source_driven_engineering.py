"""Billing source-driven engineering traceability tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_all_bill_requirements_accounted():
    from bd_platform.billing_source_driven_engineering import all_bill_ids, load_universe

    universe = load_universe()
    ids = {r["requirement_id"] for r in universe["requirements"]}
    assert ids == set(all_bill_ids())
    assert universe["SOURCE_REQUIREMENTS_ACCOUNTED_FOR"] == "100%"


def test_implementation_index_covers_all_bills():
    from bd_platform.billing_source_driven_engineering import all_bill_ids, load_index

    index = load_index()
    bindings = index.get("bindings", {})
    assert set(bindings.keys()) == set(all_bill_ids())


def test_canonical_modules_exist():
    from bd_platform.billing_source_driven_engineering import load_index

    index = load_index()
    critical = [
        "billing/event_inbox.py",
        "billing/entitlement_state.py",
        "billing/reconciliation.py",
        "billing/break_glass.py",
        "billing/webhook_resolver.py",
        "docs/SUBSCRIPTION_LEGAL_BASIS.md",
    ]
    all_paths = set()
    for binding in index["bindings"].values():
        all_paths.update(binding.get("module_paths") or [])
    for path in critical:
        assert path in all_paths
        assert (ROOT / path).is_file()


def test_no_parallel_billing_authorities():
    from bd_platform.billing_source_driven_engineering import billing_source_driven_status

    status = billing_source_driven_status(head="test", pytest_ok=True)
    assert status["PARALLEL_BILLING_AUTHORITIES"] == []
    assert status["PARALLEL_ENTITLEMENT_AUTHORITIES"] == []
    assert status["SPLIT_BRAIN_STATE_OWNERSHIP"] == []


def test_legal_basis_doc_exists():
    doc = ROOT / "docs/SUBSCRIPTION_LEGAL_BASIS.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "United States" in text
    assert "European Economic Area" in text
    assert "does **not** claim" in text


def test_spec_and_ledger_in_repo():
    assert (ROOT / "docs/BLACKDARK_INSTITUTIONAL_BILLING_SUBSCRIPTION_ENTITLEMENT_SPEC_v1.md").is_file()
    ledger = json.loads((ROOT / "docs/BILLING_IMPLEMENTATION_LEDGER.json").read_text(encoding="utf-8"))
    assert len(ledger["requirements"]) == 62
