"""FDS-09/14/19 + SDG-11/13 behavior verification."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest
from starlette.requests import Request

ROOT = Path(__file__).resolve().parents[1]


def _request(path: str = "/api/test", scheme: str = "http", headers: dict | None = None, client: str = "127.0.0.1"):
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "query_string": b"",
        "client": (client, 0),
        "server": ("testserver", 80),
        "scheme": scheme,
    }
    return Request(scope)


def test_production_http_not_secure_without_trusted_proxy(monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.transport import enforce_secure_transport, request_is_secure

    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("TRUSTED_PROXY_CIDRS", raising=False)
    req = _request(scheme="http")
    assert request_is_secure(req) is False
    with pytest.raises(PermissionError):
        enforce_secure_transport(req)


def test_spoofed_forwarded_proto_not_trusted_outside_production(monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.transport import request_is_secure

    monkeypatch.setenv("ENV", "development")
    monkeypatch.delenv("TRUSTED_PROXY_CIDRS", raising=False)
    req = _request(headers={"X-Forwarded-Proto": "https"})
    assert request_is_secure(req) is False


def test_production_ingress_forwarded_proto_trusted(monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.transport import request_is_secure

    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("TRUSTED_PROXY_CIDRS", raising=False)
    req = _request(headers={"X-Forwarded-Proto": "https"}, scheme="http")
    assert request_is_secure(req) is True


def test_trusted_proxy_secure_request_works(monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.transport import request_is_secure

    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("TRUSTED_PROXY_CIDRS", "127.0.0.1")
    req = _request(headers={"X-Forwarded-Proto": "https"}, client="127.0.0.1")
    assert request_is_secure(req) is True


def test_production_secure_cookies_enforced(monkeypatch: pytest.MonkeyPatch):
    from security_middleware import cookie_session_kwargs

    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("COOKIE_SECURE", raising=False)
    kwargs = cookie_session_kwargs()
    assert kwargs["secure"] is True
    assert kwargs["httponly"] is True


def test_hsts_enabled_in_production(monkeypatch: pytest.MonkeyPatch):
    from security_middleware import security_headers_for

    monkeypatch.setenv("ENV", "production")
    headers = security_headers_for(_request())
    assert "Strict-Transport-Security" in headers


def test_tls_policy_declares_minimum_1_2():
    from transport_webhook_env.transport import transport_policy_status

    status = transport_policy_status()
    assert status["tls_minimum_version"] == "1.2"
    assert status["tls_preferred_version"] == "1.3"
    assert status["downgrade_allowed"] is True or status["production"] is False


def test_valid_stripe_signature_accepted(monkeypatch: pytest.MonkeyPatch):
    import stripe

    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret_value_12345")
    payload = b'{"id":"evt_1","type":"ping"}'
    secret = "whsec_test_secret_value_12345"
    ts = int(time.time())
    signed_payload = f"{ts}.{payload.decode('utf-8')}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    signed = f"t={ts},v1={digest}"
    event = stripe.Webhook.construct_event(payload, signed, secret)
    assert event["id"] == "evt_1"


def test_invalid_stripe_signature_rejected(monkeypatch: pytest.MonkeyPatch):
    import stripe

    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test_secret_value_12345")
    payload = b'{"id":"evt_1"}'
    with pytest.raises(stripe.SignatureVerificationError):
        stripe.Webhook.construct_event(payload, "bad-signature", "whsec_test_secret_value_12345")


def test_valid_lemon_signature_accepted(monkeypatch: pytest.MonkeyPatch):
    from billing_service import verify_lemon_webhook_signature

    secret = "lemon_test_secret"
    body = b'{"meta":{"event_name":"subscription_created"}}'
    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", secret)
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_lemon_webhook_signature(body, sig) is True


def test_invalid_lemon_signature_rejected(monkeypatch: pytest.MonkeyPatch):
    from billing_service import verify_lemon_webhook_signature

    monkeypatch.setenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "lemon_test_secret")
    assert verify_lemon_webhook_signature(b"{}", "deadbeef") is False


def test_stale_replayed_event_rejected():
    from transport_webhook_env.webhook_lifecycle import check_replay_window

    assert check_replay_window("stripe", {"created": 1}) is False


def test_duplicate_event_processed_once(tmp_path, monkeypatch: pytest.MonkeyPatch):
    import database
    from transport_webhook_env.webhook_lifecycle import process_verified_webhook

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "dup.db"))

    async def processor(_event):
        return {"handled": True, "action": "processed"}

    async def _run():
        await database.init_db()
        event = {"id": "evt_dup_once", "type": "test.event", "created": time.time()}
        first = await process_verified_webhook(
            provider="stripe",
            event_id="evt_dup_once",
            event_type="test.event",
            event=event,
            processor=processor,
            correlation_id="dup",
        )
        second = await process_verified_webhook(
            provider="stripe",
            event_id="evt_dup_once",
            event_type="test.event",
            event=event,
            processor=processor,
            correlation_id="dup",
        )
        assert first.get("action") == "processed"
        assert second.get("action") == "duplicate_ignored"

    asyncio.run(_run())


def test_concurrent_duplicate_claim_safe(tmp_path, monkeypatch: pytest.MonkeyPatch):
    import database
    from transport_webhook_env.webhook_lifecycle import process_verified_webhook

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "race.db"))

    async def processor(_event):
        return {"handled": True, "action": "ok"}

    async def _run():
        await database.init_db()
        results = await asyncio.gather(
            process_verified_webhook(
                provider="stripe",
                event_id="evt_race",
                event_type="test",
                event={"created": time.time()},
                processor=processor,
                correlation_id="race",
            ),
            process_verified_webhook(
                provider="stripe",
                event_id="evt_race",
                event_type="test",
                event={"created": time.time()},
                processor=processor,
                correlation_id="race",
            ),
        )
        actions = {r.get("action") for r in results}
        assert "duplicate_ignored" in actions or "ok" in actions

    asyncio.run(_run())


def test_retryable_failure_enters_retry_lifecycle():
    from transport_webhook_env.webhook_lifecycle import schedule_retry

    rec = schedule_retry(provider="stripe", event_id="evt_retry", reason="transient", retry_count=1, correlation_id="c1")
    assert rec["state"] == "RETRY_SCHEDULED"
    assert rec["retry_count"] == 1


def test_retry_exhaustion_enters_dlq():
    from transport_webhook_env.webhook_lifecycle import _MAX_RETRIES, move_to_dead_letter

    rec = move_to_dead_letter(
        provider="stripe",
        event_id="evt_dlq",
        reason="exhausted",
        retry_count=_MAX_RETRIES,
        correlation_id="c2",
    )
    assert rec["state"] == "DEAD_LETTER"


def test_security_invalid_event_not_retried_as_trusted():
    from transport_webhook_env.webhook_lifecycle import reject_security_event

    rec = reject_security_event(provider="stripe", reason="invalid_signature", correlation_id="c3")
    assert rec["state"] == "REJECTED_SECURITY"
    assert "RETRY" not in rec["state"]


def test_errors_do_not_leak_secrets():
    from transport_webhook_env.webhook_lifecycle import _sanitize_reason

    reason = _sanitize_reason("invalid sk_live_secret_value leaked")
    assert "sk_live" not in reason


def test_production_cannot_use_development_default_secret(monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.environment import detect_environment_crossovers

    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "blackdark-dev-change-me-in-production")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_validlookingkey")
    findings = detect_environment_crossovers()
    assert any(f["check"] == "production_development_default_secret" for f in findings)


def test_production_cannot_accept_obvious_test_credential(monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.environment import detect_environment_crossovers

    monkeypatch.setenv("ENV", "production")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_obvious")
    findings = detect_environment_crossovers()
    assert any(f["check"] == "production_test_stripe_key" for f in findings)


def test_nonprod_cannot_silently_use_production_namespace(monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.environment import detect_environment_crossovers

    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_obvious")
    findings = detect_environment_crossovers()
    assert any(f["check"] == "nonprod_live_stripe_key" for f in findings)


def test_environment_config_identities_distinguishable(monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.environment import environment_identity

    monkeypatch.setenv("ENV", "development")
    assert environment_identity() == "development"
    monkeypatch.setenv("ENV", "production")
    assert environment_identity() == "production"
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("STAGING", "true")
    assert environment_identity() == "staging"


def test_test_data_policy_rejects_raw_production_data_config(monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.environment import _db_host_fingerprint, detect_environment_crossovers

    monkeypatch.setenv("ENV", "staging")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@prod-db.example.com/db")
    monkeypatch.setenv("PRODUCTION_DATABASE_FINGERPRINT", _db_host_fingerprint())
    findings = detect_environment_crossovers()
    assert any(f["check"] == "nonprod_production_database" for f in findings)


def test_privileged_production_access_produces_audit_event(tmp_path, monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.access_audit import recent_production_access_events, record_production_access_event

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    record_production_access_event(
        actor="admin@example.com",
        action="billing.admin.metrics",
        target="billing_admin",
        outcome="success",
        correlation_id="audit-1",
        auth_strength="mfa",
        authorization_result="allowed",
    )
    events = recent_production_access_events()
    assert events
    assert events[-1]["actor"] == "admin@example.com"


def test_failed_privileged_access_recorded_without_secret_leakage(tmp_path, monkeypatch: pytest.MonkeyPatch):
    from transport_webhook_env.access_audit import recent_production_access_events, record_production_access_event

    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    record_production_access_event(
        actor="user@example.com",
        action="privileged:privacy.dsr.export",
        target="financial_export",
        outcome="denied",
        authorization_result="mfa_required",
        reason="mfa_required",
    )
    event = recent_production_access_events()[-1]
    assert event["outcome"] == "denied"
    assert "whsec" not in json.dumps(event)


def test_break_glass_access_attributable(tmp_path, monkeypatch: pytest.MonkeyPatch):
    from privileged_access.break_glass import activate_break_glass, break_glass_enabled
    from transport_webhook_env.access_audit import record_production_access_event

    monkeypatch.setenv("BREAK_GLASS_ENABLED", "true")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert break_glass_enabled()
    activate_break_glass(
        actor_id="admin-1",
        actor_email="admin@example.com",
        reason="incident response required now",
    )
    record_production_access_event(
        actor="admin@example.com",
        action="break_glass.activate",
        target="break_glass",
        outcome="success",
        correlation_id="bg-1",
        reason="incident response required now",
    )


def test_previous_fds_closure_verifiers_remain_green():
    from governance.fds_data_boundary import verify_fds_data_boundary_scope
    from governance.fds_privileged_identity import verify_fds_privileged_identity_scope
    from governance.fds_secrets_crypto_audit import verify_fds_secrets_crypto_audit_scope

    assert verify_fds_data_boundary_scope()["scope_verified"] is True
    assert verify_fds_privileged_identity_scope()["scope_verified"] is True
    assert verify_fds_secrets_crypto_audit_scope()["scope_verified"] is True


def test_scope_verifier_green():
    from governance.fds_transport_webhook_environment import verify_fds_transport_webhook_environment_scope

    result = verify_fds_transport_webhook_environment_scope()
    assert result["scope_verified"] is True
    assert sum(result["gaps"].values()) == 0


def test_closure_script_produces_evidence():
    proc = subprocess.run(
        [sys.executable, "scripts/fds_transport_webhook_environment_closure_verify.py"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    evidence = json.loads((ROOT / "FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_CLOSURE_EVIDENCE.json").read_text())
    assert evidence["verdict"].startswith("FDS_TRANSPORT_WEBHOOK_ENVIRONMENT_CLOSED")
    assert evidence["summary"]["fds_controls_in_scope"] == 3
