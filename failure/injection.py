"""Deterministic fault injection for engineering verification (ERR-050)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from failure.ai import AIFailureKind, ai_problem
from failure.decision import evaluate_decision_safety
from failure.freshness import FreshnessState, classify_freshness
from failure.payment import normalize_payment_error
from failure.problem import ProblemDetail
from failure.quality import DataQualityState
from failure.registry import build_problem_from_spec, get_error_spec
from failure.states import MutationOutcome
from failure.mutation import mark_indeterminate, resolve_reconciliation


class FaultKind(StrEnum):
    TIMEOUT = "timeout"
    CONNECTION_RESET = "connection_reset"
    MALFORMED_UPSTREAM = "malformed_upstream"
    HTTP_4XX = "http_4xx"
    HTTP_429 = "http_429"
    HTTP_500 = "http_500"
    HTTP_502 = "http_502"
    HTTP_503 = "http_503"
    HTTP_504 = "http_504"
    STALE_DATA = "stale_data"
    PARTIAL_DATA = "partial_data"
    CONFLICTING_DATA = "conflicting_data"
    DB_FAILURE = "db_failure"
    CACHE_FAILURE = "cache_failure"
    QUEUE_DELAY = "queue_delay"
    EMAIL_FAILURE = "email_failure"
    NOTIFICATION_FAILURE = "notification_failure"
    AI_FAILURE = "ai_failure"
    PROVIDER_FAILURE = "provider_failure"
    WEBHOOK_DELAY = "webhook_delay"
    DUPLICATE_RETRY = "duplicate_retry"
    LOST_RESPONSE = "lost_response"
    RECONCILIATION = "reconciliation"
    OFFLINE = "offline"


_FAULT_TO_CODE = {
    FaultKind.HTTP_429: "BD-RATE-001",
    FaultKind.HTTP_502: "BD-UP-502",
    FaultKind.HTTP_503: "BD-NET-001",
    FaultKind.HTTP_504: "BD-UP-504",
    FaultKind.HTTP_500: "BD-GEN-001",
    FaultKind.PROVIDER_FAILURE: "BD-PAY-DECL",
    FaultKind.LOST_RESPONSE: "BD-PAY-IND",
    FaultKind.RECONCILIATION: "BD-RECON-001",
    FaultKind.OFFLINE: "BD-OFFLINE-001",
}


def inject_fault(kind: FaultKind, *, correlation_id: str = "bd-test") -> dict[str, Any]:
    if kind == FaultKind.STALE_DATA:
        return classify_freshness(age_seconds=3600.0).to_dict()
    if kind == FaultKind.PARTIAL_DATA:
        return classify_freshness(partial=True, age_seconds=5.0).to_dict()
    if kind == FaultKind.CONFLICTING_DATA:
        ctx = evaluate_decision_safety(
            freshness=FreshnessState.LIVE,
            quality=DataQualityState.CONFLICTING,
            source_count=2,
            conflicting=True,
        )
        return ctx.to_dict()
    if kind == FaultKind.AI_FAILURE:
        return ai_problem(AIFailureKind.EVIDENCE, correlation_id=correlation_id).to_dict()
    if kind in {FaultKind.LOST_RESPONSE, FaultKind.PROVIDER_FAILURE}:
        problem = normalize_payment_error(
            provider_code="card_declined",
            correlation_id=correlation_id,
            indeterminate=kind == FaultKind.LOST_RESPONSE,
        )
        return problem.to_dict()
    if kind == FaultKind.RECONCILIATION:
        mark_indeterminate(operation_id="op-test", correlation_id=correlation_id, component="billing")
        resolved = resolve_reconciliation(
            operation_id="op-test",
            correlation_id=correlation_id,
            component="billing",
            final_outcome=MutationOutcome.CONFIRMED_SUCCESS,
        )
        return resolved
    code = _FAULT_TO_CODE.get(kind, "BD-GEN-001")
    spec = get_error_spec(code)
    assert spec is not None
    problem = build_problem_from_spec(spec, correlation_id=correlation_id, detail=f"injected:{kind.value}")
    return problem.to_dict()


FAULT_MATRIX = [k.value for k in FaultKind]
