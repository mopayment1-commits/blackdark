"""SPEC_04 — Capability Library adversarial tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from launch57.capability_library_spec_common import (
    DOMAIN,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    independent_verification,
)


@pytest.fixture
async def billing_user():
    from database import create_user, init_db

    await init_db()
    email = f"spec04-billing-{datetime.now(UTC).timestamp()}@blackdark.test"
    uid = await create_user(email, "pbkdf2_sha256$260000$deadbeef$" + "a" * 64, "Spec04 Test")
    return {"id": uid, "email": email}


@pytest.fixture()
def client():
    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_requirements_register_nonempty():
    reqs = build_requirements_register()
    assert len(reqs) >= 20
    assert all(r["mandatory"] for r in reqs)


def test_runtime_truth_all_yes():
    truth = build_runtime_truth_table()
    assert truth
    nos = [r for r in truth if r["status"] != "YES"]
    assert not nos, nos


def test_library_scope_exactly_57():
    from launch57.capability_library_common import verify_library_scope

    scope = verify_library_scope()
    assert scope["exactly_57"] is True
    assert scope["parked_exposed"] == 0


def test_anonymous_search_no_handler_module(client):
    res = client.get("/api/launch57/capability-library", params={"q": "oracle"})
    assert res.status_code == 200
    lib = res.json().get("capability_library") or {}
    for row in lib.get("results") or []:
        assert "handler_module" not in row


def test_anonymous_detail_no_implementation_leak(client):
    res = client.get("/api/launch57/capability-library/4", params={"user_key": "anonymous"})
    assert res.status_code == 200
    record = (res.json().get("capability_library_detail") or {}).get("record") or {}
    assert "handler_module" not in record
    assert record.get("public_safe_projection") is True


def test_free_user_tier_param_cannot_unlock_paid_detail(client):
    res = client.get(
        "/api/launch57/capability-library/4",
        params={"user_key": "user-1", "subject_id": "user-1", "tier": "pro"},
    )
    assert res.status_code == 200
    detail = res.json().get("capability_library_detail") or {}
    record = detail.get("record") or {}
    assert "handler_module" not in record
    vis = detail.get("visibility") or {}
    assert vis.get("paid_detail") is False


@pytest.mark.asyncio
async def test_verified_pro_unlocks_implementation_detail(billing_user):
    from datetime import UTC, datetime, timedelta

    from billing.subscription_engine import activate_checkout
    from launch57.edge_ui_batch1 import capability_library_detail

    uid = int(billing_user["id"])
    email = billing_user["email"]
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    await activate_checkout(
        email=email,
        plan="pro",
        provider="stripe",
        provider_subscription_id=f"sub_spec04_{suffix}",
        user_id=uid,
        period_end=(datetime.now(UTC) + timedelta(days=30)).isoformat(),
        provider_event_id=f"evt_spec04_{suffix}",
    )
    out = await capability_library_detail(
        symbol="BTC",
        params={"launch_number": 4, "user_key": str(uid), "subject_id": str(uid), "tier": "pro"},
    )
    record = (out.get("capability_library_detail") or {}).get("record") or {}
    assert record.get("handler_module")


def test_parked_injection_rejected(client):
    res = client.get("/api/launch57/capability-library", params={"include_parked": "true"})
    assert res.status_code == 200
    body = res.json()
    lib = body.get("capability_library") or {}
    assert lib.get("results") == [] or body.get("success") is False


def test_secondary_layer_not_primary_home(client):
    res = client.get("/api/launch57/capability-library")
    lib = res.json().get("capability_library") or {}
    assert lib.get("secondary_layer") is True
    assert lib.get("not_primary_home") is True


def test_command_home_remains_authenticated(client):
    res = client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 401


def test_compare_anonymous_no_primary_consumer(client):
    res = client.get("/api/launch57/capability-library/compare", params={"compare": "4,5"})
    assert res.status_code == 200
    rows = (res.json().get("capability_library_compare") or {}).get("comparison") or []
    assert len(rows) == 2
    for row in rows:
        assert "primary_consumer" not in row


@pytest.mark.asyncio
async def test_capability_library_search_handler_not_in_guard_results():
    from launch57.edge_ui_batch1 import capability_library_search

    out = await capability_library_search(symbol="BTC", params={"query": "Oracle"})
    results = (out.get("capability_library") or {}).get("results") or []
    assert results
    for row in results:
        assert "handler_module" not in row


def test_independent_verification_passes():
    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True
    assert iv["passed_count"] == iv["probe_count"]


def test_final_status_closed_local():
    status = build_final_status(skip_tests=True)
    assert status["closure_status"] == "CLOSED_LOCAL"
    assert status["PASS_ENGINEERING"] is True
    assert status["LOCAL_ENGINEERING_GAP_COUNT"] == 0
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True
    assert status["library_scope_ok"] is True
    assert status["entitlement_align_ok"] is True


def test_spec04_artifact_paths_exist():
    gov = Path("governance/launch57/SPEC_04_CAPABILITY_LIBRARY")
    for name in (
        "REQUIREMENTS_REGISTER.json",
        "RUNTIME_TRUTH_TABLE.md",
        "LOCAL_CLOSURE_REPORT.md",
        "INDEPENDENT_VERIFICATION.json",
        "FINAL_STATUS.json",
    ):
        path = gov / name
        assert path.exists(), f"missing {path}"
        if name.endswith(".json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload.get("domain") == DOMAIN or payload.get("artifact", "").startswith("SPEC_04")
