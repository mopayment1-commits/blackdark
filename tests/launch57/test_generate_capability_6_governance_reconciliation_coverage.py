"""Behavioral coverage for governance.launch57.generate_capability_6_governance_reconciliation."""

from __future__ import annotations

import copy
import json
from datetime import UTC, datetime

import governance.launch57.generate_capability_6_governance_reconciliation as cap6


def test_find_and_reconcile_register_item():
    register = json.loads(cap6.REGISTER_PATH.read_text(encoding="utf-8"))
    item = copy.deepcopy(cap6._find_register_item(register))
    b3_iv = json.loads(cap6.B3_IV_PATH.read_text(encoding="utf-8"))
    now = datetime.now(UTC).isoformat()
    before = cap6._reconcile_register_item(
        item,
        commit_sha="deadbeef",
        now=now,
        b3_iv=b3_iv,
    )
    assert isinstance(before, dict)
    cap6._verify_item(item, b3_iv)
    assert item["capability_6_governance_reconciliation"]["canonical_owner_module"] == cap6.CANONICAL_OWNER_MODULE
    assert item["capability_6_governance_reconciliation"]["reconciled_commit"] == "deadbeef"
