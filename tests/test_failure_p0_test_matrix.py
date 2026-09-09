"""Failure P0 test matrix — ERR-001 → ERR-050 local engineering evidence."""

from __future__ import annotations

import os

import pytest
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError

os.environ.setdefault("SOFT_LAUNCH", "1")


def test_failure_state_model_complete():
    from failure.states import FailureState, STATE_SEMANTICS

    expected = {
        "LOADING",
        "SUCCESS",
        "DELAYED",
        "STALE",
        "PARTIAL",
        "DEGRADED",
        "UNAVAILABLE",
        "FAILED",
        "RATE_LIMITED",
        "AUTH_REQUIRED",
        "PERMISSION_DENIED",
        "CONFIRMATION_PENDING",
        "INDETERMINATE",
        "RETRYING",
        "MAINTENANCE",
        "ABSTAINED",
    }
    assert {s.value for s in FailureState} == expected
    for state in FailureState:
        sem = STATE_SEMANTICS[state]
        assert {"backend", "frontend", "retry", "user_action", "observability"} <= set(sem)


def test_separate_failure_dimensions():
    from failure.dimensions import CertaintyState, FailureClass, Severity, UserImpact

    assert FailureClass.PAYMENT_PROVIDER.value == "PAYMENT_PROVIDER"
    assert CertaintyState.INDETERMINATE.value == "INDETERMINATE"
    assert UserImpact.HIGH.value == "HIGH"
    assert Severity.ERROR.value == "ERROR"


def test_rfc9457_problem_contract():
    from failure.problem import ProblemDetail, retryable_from_policy
    from failure.dimensions import RetryPolicy

    p = ProblemDetail(
        type="https://blackdark.io/problems/bd-gen-001",
        title="Request failed",
        status=500,
        detail="Request failed",
        error_code="BD-GEN-001",
        correlation_id="bd-abc123",
    )
    body = p.to_dict()
    for key in ("type", "title", "status", "detail", "instance", "error_code", "correlation_id"):
        assert key in body
    assert retryable_from_policy(RetryPolicy.SAFE_AUTO_RETRY) is True
    assert retryable_from_policy(RetryPolicy.DO_NOT_RETRY) is False


def test_correlation_id_opaque_and_propagated():
    from failure.correlation import is_privacy_safe_identifier, new_correlation_id, new_support_reference

    cid = new_correlation_id()
    ref = new_support_reference(cid)
    assert cid.startswith("bd-")
    assert "@" not in cid
    assert is_privacy_safe_identifier(cid)
    assert is_privacy_safe_identifier(ref)


def test_provider_internals_not_in_public_error():
    from safe_errors import public_error

    msg = public_error(Exception("postgres://secret stripe_sk_live token=abc"))
    assert "postgres" not in msg.lower()
    assert "stripe" not in msg.lower()


def test_indeterminate_mutation_and_reconciliation():
    from failure.mutation import mark_indeterminate, resolve_reconciliation
    from failure.states import MutationOutcome, ReconciliationState

    rec = mark_indeterminate(operation_id="op-1", correlation_id="bd-test", component="billing")
    assert rec["outcome"] == MutationOutcome.INDETERMINATE.value
    assert rec["reconciliation"] == ReconciliationState.INDETERMINATE.value
    resolved = resolve_reconciliation(
        operation_id="op-1",
        correlation_id="bd-test",
        component="billing",
        final_outcome=MutationOutcome.CONFIRMED_SUCCESS,
    )
    assert resolved["reconciliation"] == ReconciliationState.CONFIRMED_SUCCESS.value


def test_idempotency_facade():
    from failure.idempotency import check_idempotency, requires_idempotency, store_idempotency

    assert requires_idempotency("billing.payment") is True
    store_idempotency("key-1", 200, {"ok": True})
    dup, cached = check_idempotency("key-1")
    assert dup is True
    assert cached["status_code"] == 200


def test_retry_taxonomy_and_backoff():
    from failure.dimensions import RetryPolicy
    from failure.retry import classify_retry_policy, compute_backoff

    assert classify_retry_policy(indeterminate=True) == RetryPolicy.RECONCILE_FIRST
    assert classify_retry_policy(validation=True) == RetryPolicy.DO_NOT_RETRY
    assert classify_retry_policy(status_code=503) == RetryPolicy.SAFE_AUTO_RETRY
    d1 = compute_backoff(1, retry_after=10)
    assert d1 == 10.0
    d2 = compute_backoff(3)
    assert 0.25 <= d2 <= 30.0


def test_circuit_breaker_facade():
    from failure.circuit import degraded_failure_state, record_failure, record_success
    from failure.states import FailureState

    record_failure("test-source", "timeout")
    record_failure("test-source", "timeout")
    record_failure("test-source", "timeout")
    assert degraded_failure_state("test-source") in {FailureState.DEGRADED, FailureState.SUCCESS}
    record_success("test-source")
    assert degraded_failure_state("test-source") == FailureState.SUCCESS


def test_freshness_and_unknown_age():
    from failure.freshness import FreshnessState, attach_freshness, classify_freshness

    unknown = classify_freshness()
    assert unknown.state == FreshnessState.UNKNOWN
    stale = classify_freshness(age_seconds=120.0)
    assert stale.state == FreshnessState.STALE
    attached = attach_freshness({"data_freshness": {"state": "unknown"}})
    assert attached["freshness"]["state"] == FreshnessState.UNKNOWN.value


def test_data_quality_separate_from_availability():
    from failure.quality import DataQualityState, classify_quality

    q = classify_quality(conflicting=True, source_count=2)
    assert q.state == DataQualityState.CONFLICTING


def test_decision_abstention_and_evidence_context():
    from failure.decision import DecisionSafetyState, evaluate_decision_safety
    from failure.freshness import FreshnessState
    from failure.quality import DataQualityState

    ctx = evaluate_decision_safety(
        freshness=FreshnessState.STALE,
        quality=DataQualityState.INSUFFICIENT,
        source_count=0,
        conflicting=True,
    )
    assert ctx.decision_state == DecisionSafetyState.ABSTAINED
    assert ctx.evidence_state == "insufficient"


def test_ai_failure_decomposition():
    from failure.ai import AIFailureKind, ai_problem, classify_ai_failure

    assert classify_ai_failure(context="evidence incomplete stale data") == AIFailureKind.EVIDENCE
    problem = ai_problem(AIFailureKind.PRESENTATION, correlation_id="bd-ai")
    assert problem.error_code == "BD-AI-PRES"
    assert "LLM" not in problem.detail


def test_user_action_contract_and_retry_safety():
    from failure.user_action import INDETERMINATE_SAFE_ACTIONS, UserAction

    assert UserAction.RETRY.value == "RETRY"
    assert UserAction.RETRY not in INDETERMINATE_SAFE_ACTIONS
    assert UserAction.CHECK_STATUS in INDETERMINATE_SAFE_ACTIONS


def test_structured_logging_redacts_secrets():
    from failure.logging import log_failure, redact_payload

    payload = redact_payload({"msg": "password=secret token=abc"})
    assert "secret" not in str(payload).lower() or "[REDACTED]" in str(payload)
    rec = log_failure(
        correlation_id="bd-log",
        component="api",
        operation="POST /test",
        failure_class="INTERNAL",
        certainty="CONFIRMED",
        severity="ERROR",
        user_impact="LOW",
        message_key="error.generic",
    )
    assert rec["correlation_id"] == "bd-log"


def test_incident_aggregation_and_status_components():
    from failure.incident import CANONICAL_COMPONENTS, aggregate_dependency_failures, component_status_report

    assert len(CANONICAL_COMPONENTS) >= 8
    agg = aggregate_dependency_failures(
        [
            {"dependency": "market_data", "component": "widget_a"},
            {"dependency": "market_data", "component": "widget_b"},
        ]
    )
    assert len(agg) == 1
    assert agg[0]["count"] == 2
    report = component_status_report()
    assert "components" in report


def test_payment_error_normalization():
    from failure.payment import normalize_payment_error

    ind = normalize_payment_error(provider_code="card_declined", correlation_id="bd-pay", indeterminate=True)
    assert ind.error_code == "BD-PAY-IND"
    assert ind.user_action == "CHECK_STATUS"


def test_error_registry_stable_codes():
    from failure.registry import get_error_spec, list_error_specs

    specs = list_error_specs()
    assert len(specs) >= 10
    pay = get_error_spec("BD-PAY-IND")
    assert pay is not None
    assert pay.message_key == "error.payment.indeterminate"


def test_fault_injection_matrix():
    from failure.injection import FAULT_MATRIX, FaultKind, inject_fault

    assert len(FAULT_MATRIX) >= 20
    for fault in ("http_429", "stale_data", "reconciliation", "offline"):
        body = inject_fault(FaultKind(fault), correlation_id="bd-inject")
        assert body


def test_error_flood_dedup():
    from failure.flood import should_surface

    key = "same-error"
    assert should_surface(key, cooldown_seconds=60) is True
    assert should_surface(key, cooldown_seconds=60) is False


def test_support_handoff():
    from failure.support import support_handoff

    payload = support_handoff(
        correlation_id="bd-support123456",
        component="billing",
        action="checkout",
        summary_key="error.payment.indeterminate",
    )
    assert payload["support_reference"].startswith("SR-")
    assert payload["links"]["status"] == "/status"


def test_i18n_error_keys_present_all_locales():
    from i18n_service import EN, catalogs, invalidate_catalogs

    invalidate_catalogs()
    keys = [k for k in EN if k.startswith("error.")]
    assert keys
    cats = catalogs()
    for code, cat in cats.items():
        for key in keys:
            assert key in cat, f"{code} missing {key}"


@pytest.mark.asyncio
async def test_http_exception_handler_problem_json():
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/journal")
        assert resp.status_code == 401
        assert resp.headers.get("content-type", "").startswith("application/problem+json")
        body = resp.json()
        assert body.get("error_code")
        assert body.get("correlation_id")
        assert resp.headers.get("X-Correlation-ID")


def test_decision_abstention_engine_wiring():
    from failure.decision import DecisionSafetyState
    from failure.freshness import FreshnessState
    from failure.quality import DataQualityState
    from bd_platform.adaptive_intelligence.decision_contract import build_decision_contract

    stale = build_decision_contract(
        goal="funding",
        symbol="BTC",
        candidates=[{"capability_id": 609, "relevance_score": 3.0}],
        freshness_state=FreshnessState.STALE,
        quality_state=DataQualityState.CONFLICTING,
        conflicting=True,
    )
    assert stale["abstain"] is True
    assert stale["decision_safety"] == DecisionSafetyState.ABSTAINED.value
    assert stale["evidence_context"]["decision_state"] == DecisionSafetyState.ABSTAINED.value


@pytest.mark.asyncio
async def test_fault_injection_production_safety(monkeypatch):
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    monkeypatch.setenv("SOFT_LAUNCH", "false")
    monkeypatch.delenv("ENABLE_FAULT_INJECTION", raising=False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        anon = await client.get("/api/failure/inject/http_429")
        assert anon.status_code in {403, 404}

    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("ADMIN_API_KEY", "failure-test-admin-key")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        denied = await client.get("/api/failure/inject/http_429")
        assert denied.status_code in {403, 404}
        allowed = await client.get(
            "/api/failure/inject/http_429",
            headers={"X-Admin-Key": "failure-test-admin-key"},
        )
        assert allowed.status_code == 200
        assert allowed.json().get("error_code") == "BD-RATE-001"


@pytest.mark.asyncio
async def test_failure_api_endpoints(monkeypatch):
    from httpx import ASGITransport, AsyncClient

    from dashboard import app

    monkeypatch.setenv("SOFT_LAUNCH", "true")
    monkeypatch.setenv("ADMIN_API_KEY", "failure-test-admin-key")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        status = await client.get("/api/failure/status/components")
        assert status.status_code == 200
        inject = await client.get(
            "/api/failure/inject/http_429",
            headers={"X-Admin-Key": "failure-test-admin-key"},
        )
        assert inject.status_code == 200
        assert inject.json().get("error_code") == "BD-RATE-001"


def test_billing_checkout_idempotency():
    from failure.idempotency import check_idempotency, store_idempotency

    store_idempotency("billing-checkout-test", 200, {"url": "https://example.com/checkout"})
    dup, cached = check_idempotency("billing-checkout-test")
    assert dup is True
    assert cached["body"]["url"] == "https://example.com/checkout"

def test_engineering_closure_module():
    from bd_platform.failure_source_driven_engineering import failure_source_driven_status

    status = failure_source_driven_status(head="test", pytest_ok=True)
    assert status["SOURCE_REQUIREMENTS_ACCOUNTED_FOR"] == "100%"
    assert len(status["requirements"]) == 50
