"""Launch-57 Identity, Authentication & Profile baseline tests."""

from __future__ import annotations

import json
from pathlib import Path

from launch57.identity_auth_common import (
    INTERNAL_IDENTITY_COMPONENTS,
    acceptance_criteria_status,
    attach_identity_auth_envelope,
    build_enabled_auth_methods,
    build_identity_touchpoint_matrix,
    record_identity_auth_signal,
    resolve_auth_context,
    sanitize_identity_for_public,
    scan_identity_log_leakage,
    verify_auth_vs_entitlement_separation,
    verify_private_state_access,
    verify_public_private_boundary,
    verify_step_up_required,
)


def test_internal_components_registry():
    from launch57.identity_auth_common import build_identity_component_registry

    registry = build_identity_component_registry()
    assert len(registry) == len(INTERNAL_IDENTITY_COMPONENTS)
    for row in registry:
        assert row["launch_scope"] == "LAUNCH57"


def test_anonymous_private_state_denied():
    ctx = resolve_auth_context({"user_key": "anonymous"})
    result = verify_private_state_access(launch_item_id=49, auth_context=ctx)
    assert result["allowed"] is False
    assert result["reason"] == "anonymous_private_state_denied"


def test_authenticated_private_state_allowed():
    ctx = resolve_auth_context({"user_key": "user-a", "subject_id": "user-a"})
    result = verify_private_state_access(
        launch_item_id=49,
        auth_context=ctx,
        resource_owner_id="user-a",
    )
    assert result["allowed"] is True


def test_cross_user_private_state_denied():
    ctx = resolve_auth_context({"user_key": "user-a", "subject_id": "user-a"})
    result = verify_private_state_access(
        launch_item_id=32,
        auth_context=ctx,
        resource_owner_id="user-b",
    )
    assert result["allowed"] is False


def test_auth_entitlement_separation():
    sep = verify_auth_vs_entitlement_separation(authenticated=True, entitled=False)
    assert sep["separation_enforced"] is True
    assert sep["auth_alone_insufficient"] is True
    assert sep["auth_without_entitlement_denied"] is True


def test_public_boundary_detects_private_fields():
    check = verify_public_private_boundary(
        {"email": "user@example.com", "symbol": "BTC"},
        surface_type="public",
    )
    assert check["boundary_ok"] is False
    assert "email" in check["private_fields_leaked"]


def test_sanitize_identity_for_public():
    cleaned = sanitize_identity_for_public(
        {"email": "user@example.com", "symbol": "BTC", "price": 1.0}
    )
    assert "email" not in cleaned
    assert cleaned.get("public_safe_identity_projection") is True


def test_log_leakage_scan_detects_password():
    scan = scan_identity_log_leakage({"password": "secret-value", "symbol": "BTC"})
    assert scan["ok"] is False
    assert any("password" in issue for issue in scan["issues"])


def test_step_up_fail_closed_without_token():
    result = verify_step_up_required(
        operation="account_delete",
        step_up_token=None,
        subject_id="user-1",
    )
    assert result["fail_closed"] is True
    assert result["satisfied"] is False


def test_attach_envelope_reports_anonymous_private_surface():
    body = {
        "launch_item_id": 50,
        "success": True,
        "discipline_mirror": {"rows": []},
    }
    out = attach_identity_auth_envelope(
        body,
        launch_item_id=50,
        surface_type="private",
        params={"user_key": "anonymous"},
    )
    assert out["success"] is True
    envelope = out["launch57_identity_auth"]
    assert envelope["private_state_access"]["allowed"] is False
    assert envelope["private_state_access"]["reason"] == "anonymous_private_state_denied"


def test_attach_envelope_public_surface():
    body = {
        "launch_item_id": 46,
        "success": True,
        "guest_trust": {"anonymous_state": "ANONYMOUS"},
    }
    out = attach_identity_auth_envelope(
        body,
        launch_item_id=46,
        surface_type="public",
        params={"user_key": "anonymous"},
    )
    assert out["success"] is True
    envelope = out["launch57_identity_auth"]
    assert envelope["auth_context"]["anonymous"] is True
    assert envelope["public_private_boundary"]["private_by_default"] is True


def test_enabled_auth_methods():
    methods = build_enabled_auth_methods()
    assert any(m["method"] == "email_password" for m in methods)


def test_touchpoint_matrix_covers_private_and_public():
    matrix = build_identity_touchpoint_matrix()
    by_id = {row["launch_item_id"]: row for row in matrix}
    assert by_id[32]["private_state"] is True
    assert by_id[46]["anonymous_allowed"] is True
    assert by_id[49]["wired"] is True


def test_record_identity_signal(tmp_path, monkeypatch):
    store = tmp_path / "signals.jsonl"
    monkeypatch.setattr(
        "launch57.identity_auth_common._SIGNAL_STORE",
        store,
    )
    row = record_identity_auth_signal(
        signal_type="private_access_denied",
        launch_item_id=49,
        detail="anonymous attempt",
    )
    assert row["signal_type"] == "private_access_denied"
    lines = store.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["launch_item_id"] == 49


def test_acceptance_criteria_engineering_gate():
    acceptance = acceptance_criteria_status()
    assert acceptance["ac01_immutable_user_identity"] is True
    assert acceptance["ac10_cross_user_fails_closed"] is True
    assert acceptance["ac12_private_state_protected"] is True
    assert acceptance["ac20_no_false_pass_live"] is True
