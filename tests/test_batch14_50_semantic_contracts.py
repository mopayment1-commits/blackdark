"""Semantic contracts for all 50 Batch14 capabilities."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from bd_platform.batch14_semantic_contracts import all_contracts, contract_for
from bd_platform.batch14_membership import BATCH14_IDS
from pdf_capability_registry import discover_bindings, execute_binding

ROOT = Path(__file__).resolve().parent.parent


def test_contracts_50_of_50() -> None:
    contracts = all_contracts()
    assert len(contracts) == 50
    assert set(contracts) == set(BATCH14_IDS)


@pytest.mark.parametrize("capability_id", BATCH14_IDS)
def test_semantic_contract_runtime_match(capability_id: int) -> None:
    contract = contract_for(capability_id)
    mod_name, fn_name = discover_bindings()[capability_id]
    payload = asyncio.run(execute_binding(mod_name, fn_name, capability_id=capability_id))
    assert payload.get("capability_id") == capability_id
    assert payload.get("ok") is True, payload
    for key in contract.get("required_keys", set()):
        assert key in payload, f"missing {key} in {capability_id}"
