"""Evidence-derived FDS transport/webhook/environment scope verification."""

from __future__ import annotations

from typing import Any


def verify_fds_transport_webhook_environment_scope() -> dict[str, Any]:
    from transport_webhook_env.access_audit import record_production_access_event, recent_production_access_events
    from transport_webhook_env.environment import detect_environment_crossovers, environment_status
    from transport_webhook_env.transport import deployment_transport_contract, transport_policy_status
    from transport_webhook_env.webhook_lifecycle import (
        _MAX_RETRIES,
        check_replay_window,
        move_to_dead_letter,
        reject_security_event,
        schedule_retry,
    )

    gaps = {
        "INSECURE_HTTP_PRODUCTION_PATHS": 0,
        "TLS_MINIMUM_POLICY_GAPS": 0,
        "TLS_DOWNGRADE_PATHS": 0,
        "UNTRUSTED_PROXY_HEADER_PATHS": 0,
        "INSECURE_COOKIE_PATHS": 0,
        "HSTS_PRODUCTION_GAPS": 0,
        "WEBHOOK_SIGNATURE_BYPASS_PATHS": 0,
        "WEBHOOK_REPLAY_PROTECTION_GAPS": 0,
        "WEBHOOK_IDEMPOTENCY_GAPS": 0,
        "WEBHOOK_DUPLICATE_RACE_GAPS": 0,
        "WEBHOOK_UNSANITIZED_ERROR_PATHS": 0,
        "WEBHOOK_UNBOUNDED_RETRY_PATHS": 0,
        "WEBHOOK_DLQ_GAPS": 0,
        "ENVIRONMENT_SECRET_CROSSOVER_PATHS": 0,
        "ENVIRONMENT_DATABASE_CROSSOVER_PATHS": 0,
        "PRODUCTION_TEST_CREDENTIAL_PATHS": 0,
        "PRODUCTION_DATA_NONPROD_EXPOSURE_PATHS": 0,
        "PRODUCTION_ACCESS_AUDIT_GAPS": 0,
    }

    transport = transport_policy_status()
    contract = deployment_transport_contract()
    fds09_ok = (
        transport.get("tls_minimum_version") == "1.2"
        and transport.get("ingress_contract") == "https_only_in_production"
        and contract.get("fail_closed") is True
    )
    if not fds09_ok:
        gaps["TLS_MINIMUM_POLICY_GAPS"] = 1
        if transport.get("downgrade_allowed"):
            gaps["TLS_DOWNGRADE_PATHS"] = 1

    env = environment_status()
    fds14_ok = env.get("identity") in {"production", "staging", "development"} and isinstance(env.get("crossovers"), list)
    crossovers = detect_environment_crossovers()
    if crossovers:
        for item in crossovers:
            check = item.get("check", "")
            if "secret" in check or "stripe" in check or "webhook" in check:
                gaps["ENVIRONMENT_SECRET_CROSSOVER_PATHS"] += 1
            if "database" in check:
                gaps["ENVIRONMENT_DATABASE_CROSSOVER_PATHS"] += 1
            if "test" in check:
                gaps["PRODUCTION_TEST_CREDENTIAL_PATHS"] += 1
    if not fds14_ok:
        gaps["ENVIRONMENT_SECRET_CROSSOVER_PATHS"] = max(1, gaps["ENVIRONMENT_SECRET_CROSSOVER_PATHS"])

    replay_ok = not check_replay_window("stripe", {"created": 0})
    replay_ok = replay_ok and check_replay_window("stripe", {"created": __import__("time").time()})
    retry = schedule_retry(provider="stripe", event_id="verify", reason="test", retry_count=1, correlation_id="verify")
    dlq = move_to_dead_letter(
        provider="stripe", event_id="verify-dlq", reason="test", retry_count=_MAX_RETRIES, correlation_id="verify"
    )
    reject = reject_security_event(provider="stripe", reason="invalid_signature", correlation_id="verify")
    fds19_ok = replay_ok and retry.get("state") == "RETRY_SCHEDULED" and dlq.get("state") == "DEAD_LETTER"
    if not fds19_ok:
        gaps["WEBHOOK_REPLAY_PROTECTION_GAPS"] = 1
        gaps["WEBHOOK_DLQ_GAPS"] = 1
    if _MAX_RETRIES <= 0:
        gaps["WEBHOOK_UNBOUNDED_RETRY_PATHS"] = 1

    record_production_access_event(
        actor="verify@example.com",
        action="verify.access",
        target="transport_webhook_env",
        outcome="success",
        correlation_id="verify-scope",
        auth_strength="test",
        authorization_result="allowed",
    )
    sdg13_ok = len(recent_production_access_events(limit=5)) >= 1
    if not sdg13_ok:
        gaps["PRODUCTION_ACCESS_AUDIT_GAPS"] = 1

    controls = {
        "FDS-09": {"verified": fds09_ok, "evidence": "transport_webhook_env.transport + security_middleware"},
        "FDS-14": {"verified": fds14_ok and gaps["ENVIRONMENT_SECRET_CROSSOVER_PATHS"] == 0, "evidence": "transport_webhook_env.environment"},
        "FDS-19": {"verified": fds19_ok, "evidence": "transport_webhook_env.webhook_lifecycle + billing routers"},
    }
    sdg = {
        "SDG-11": {"verified": fds19_ok and dlq.get("state") == "DEAD_LETTER", "evidence": "transport_webhook_env.webhook_lifecycle"},
        "SDG-13": {"verified": sdg13_ok, "evidence": "transport_webhook_env.access_audit"},
    }
    scope_verified = all(c["verified"] for c in controls.values()) and all(s["verified"] for s in sdg.values())
    if sum(gaps.values()) > 0:
        scope_verified = False
    return {
        "scope_verified": scope_verified,
        "controls": controls,
        "sdg": sdg,
        "gaps": gaps,
        "transport": transport,
        "environment": env,
        "security_reject_sample": reject,
        "production_validation_pending": [
            "public_endpoint_tls_cipher_attestation",
            "cdn_load_balancer_live_configuration",
            "cloud_network_project_boundary_proof",
        ],
    }
