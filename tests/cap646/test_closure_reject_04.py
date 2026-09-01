"""CLOSURE-REJECT-04 — spine path coverage + HMAC closure guard tests."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest


@pytest.mark.asyncio
async def test_runtime_execute_batch01_spine(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "rt.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.runtime import execute_capability

    for cid in (1, 5, 47, 50):
        result = await execute_capability(cid, params={"symbol": "BTC", "kind": "spot_futures"})
        assert result.get("success") is True or result.get("classification")
        assert result.get("classification") in {"PRODUCTION-ALIGNED", "NOT_COMPLETE", None}


@pytest.mark.asyncio
async def test_runtime_execute_batch02_spine(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "rt2.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.runtime import execute_capability

    for cid in (51, 53, 57, 85, 100):
        result = await execute_capability(cid, params={"symbol": "BTC", "kind": "spot_futures"})
        assert result.get("success") is True or result.get("classification")
        assert "VERIFIED_COMPLETE" not in str(result.get("classification"))


@pytest.mark.asyncio
async def test_runtime_classification_bans_verified_complete():
    from cap646.rtm_classification import runtime_classification

    assert runtime_classification({"success": True}) == "PRODUCTION-ALIGNED"
    assert runtime_classification({"success": False}) == "NOT_COMPLETE"
    assert "VERIFIED_COMPLETE" not in runtime_classification({"success": True})


@pytest.mark.asyncio
async def test_cap978_verify_emits_legacy_namespace_only(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "v.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap978.unified import execute_unified
    from cap978.verify import verify_functional_978
    from cap646.runtime import _runtime_classification

    report = await verify_functional_978(53)
    assert "verdict" in report
    unified = await execute_unified(53, user={"email": "t@x.com", "tier": "pro"}, params={"symbol": "BTC"})
    from cap646.rtm_classification import runtime_classification

    assert runtime_classification(unified) in {"PRODUCTION-ALIGNED", "NOT_COMPLETE"}
    assert unified.get("classification") != "VERIFIED_COMPLETE"


@pytest.mark.asyncio
async def test_batch01_dedicated_handlers(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "b1.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.batch01_dedicated import execute

    result = await execute(6, params={"symbol": "BTC"})
    assert result.get("success") is True


@pytest.mark.asyncio
async def test_batch02_dedicated_cap053(tmp_path, monkeypatch):
    import config
    import database

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "b2.db"))
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    await database.init_db()

    from cap646.batch02_dedicated import _cap053

    result = await _cap053(symbol="BTC", address="", params={"kind": "spot_futures"})
    assert result.get("success") is True
    assert result.get("surface") == "btc_to_macro_coupling"


def test_closure_guard_blocks_without_secret(tmp_path, monkeypatch):
    from cap646.closure_guard import ClosureGuardError, assert_owner_approval_for_closure

    monkeypatch.delenv("INSTITUTIONAL_OWNER_APPROVAL_SECRET", raising=False)
    monkeypatch.delenv("INSTITUTIONAL_OWNER_APPROVAL_TOKEN", raising=False)
    with pytest.raises(ClosureGuardError, match="SECRET"):
        assert_owner_approval_for_closure(requested_status="INSTITUTIONAL_CLOSED")


def test_closure_guard_blocks_with_wrong_token(tmp_path, monkeypatch):
    import hashlib
    import hmac

    from cap646.closure_guard import ClosureGuardError, assert_owner_approval_for_closure

    monkeypatch.setenv("INSTITUTIONAL_OWNER_APPROVAL_SECRET", "test-secret")
    monkeypatch.setenv("INSTITUTIONAL_OWNER_APPROVAL_TOKEN", "wrong")
    with pytest.raises(ClosureGuardError, match="mismatch"):
        assert_owner_approval_for_closure(requested_status="INSTITUTIONAL_CLOSED")


def test_closure_guard_allows_valid_token(monkeypatch):
    import hashlib
    import hmac

    from cap646.closure_guard import assert_owner_approval_for_closure

    secret = "test-secret"
    token = hmac.new(secret.encode(), b"INSTITUTIONAL_CLOSED", hashlib.sha256).hexdigest()
    monkeypatch.setenv("INSTITUTIONAL_OWNER_APPROVAL_SECRET", secret)
    monkeypatch.setenv("INSTITUTIONAL_OWNER_APPROVAL_TOKEN", token)
    assert_owner_approval_for_closure(requested_status="INSTITUTIONAL_CLOSED")


def test_progress_104_numerator():
    data = json.loads(Path("docs/PROGRESS_114_ID_MAPPING.json").read_text(encoding="utf-8"))
    assert data["numerator"] == 104
    assert all(1 <= i <= 100 or i in {338, 500, 507, 534} for i in data["included_ids"])
    assert 214 not in data["included_ids"]
    assert 245 not in data["included_ids"]
    assert 103 not in data["included_ids"]


def test_entitlement_proofs_no_batch03_ids():
    for rel in ("docs/BATCH01_ENTITLEMENT_GATEWAY_PROOF.json", "docs/BATCH02_ENTITLEMENT_GATEWAY_PROOF.json"):
        proofs = json.loads(Path(rel).read_text(encoding="utf-8"))["proofs"]
        for p in proofs:
            cid = int(p["capability_id"])
            assert not (101 <= cid <= 150), f"Batch03 leak {cid} in {rel}"
