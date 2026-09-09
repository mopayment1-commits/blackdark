"""Central error contract registry (ERR-040, ERR-041)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from failure.dimensions import (
    CertaintyState,
    FailureClass,
    RetryPolicy,
    Severity,
    UserImpact,
)
from failure.user_action import UserAction

PROBLEM_TYPE_BASE = "https://blackdark.io/problems"


@dataclass(frozen=True, slots=True)
class ErrorSpec:
    error_code: str
    category: str
    certainty: CertaintyState
    severity: Severity
    user_impact: UserImpact
    retry_policy: RetryPolicy
    http_status: int
    message_key: str
    user_action: UserAction
    support_reference_policy: str
    log_level: str
    alert_policy: str
    failure_class: FailureClass
    title: str
    affected_component: str | None = None


_REGISTRY: dict[str, ErrorSpec] = {}


def _register(spec: ErrorSpec) -> None:
    _REGISTRY[spec.error_code] = spec


def get_error_spec(code: str) -> ErrorSpec | None:
    return _REGISTRY.get(code)


def list_error_specs() -> list[ErrorSpec]:
    return list(_REGISTRY.values())


def spec_for_http_status(status: int, *, failure_class: FailureClass | None = None) -> ErrorSpec:
    for spec in _REGISTRY.values():
        if spec.http_status == status:
            if failure_class is None or spec.failure_class == failure_class:
                return spec
    return _REGISTRY["BD-GEN-001"]


def bootstrap_registry() -> None:
    if _REGISTRY:
        return
    entries: list[ErrorSpec] = [
        ErrorSpec(
            "BD-GEN-001",
            "generic",
            CertaintyState.CONFIRMED,
            Severity.ERROR,
            UserImpact.MEDIUM,
            RetryPolicy.SAFE_USER_RETRY,
            500,
            "error.generic",
            UserAction.CONTACT_SUPPORT,
            "high_impact",
            "error",
            "page",
            FailureClass.INTERNAL,
            "Request failed",
        ),
        ErrorSpec(
            "BD-VAL-001",
            "validation",
            CertaintyState.CONFIRMED,
            Severity.INFO,
            UserImpact.LOW,
            RetryPolicy.DO_NOT_RETRY,
            422,
            "error.validation",
            UserAction.CHANGE_INPUT,
            "none",
            "info",
            "none",
            FailureClass.VALIDATION,
            "Validation failed",
        ),
        ErrorSpec(
            "BD-AUTH-001",
            "authentication",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.MEDIUM,
            RetryPolicy.DO_NOT_RETRY,
            401,
            "error.auth.generic_failure",
            UserAction.SIGN_IN,
            "none",
            "warning",
            "none",
            FailureClass.AUTHENTICATION,
            "Authentication required",
        ),
        ErrorSpec(
            "BD-AUTHZ-001",
            "authorization",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.MEDIUM,
            RetryPolicy.DO_NOT_RETRY,
            403,
            "error.authz.denied",
            UserAction.NONE,
            "none",
            "warning",
            "none",
            FailureClass.AUTHORIZATION,
            "Permission denied",
        ),
        ErrorSpec(
            "BD-SEC-001",
            "security",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.HIGH,
            RetryPolicy.DO_NOT_RETRY,
            403,
            "error.security.blocked",
            UserAction.VERIFY,
            "high_impact",
            "warning",
            "security",
            FailureClass.SECURITY,
            "Security block",
        ),
        ErrorSpec(
            "BD-RATE-001",
            "rate_limit",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.LOW,
            RetryPolicy.SAFE_AUTO_RETRY,
            429,
            "error.rate_limit",
            UserAction.WAIT,
            "none",
            "warning",
            "rate",
            FailureClass.RATE_LIMIT,
            "Too many requests",
        ),
        ErrorSpec(
            "BD-NET-001",
            "network",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.MEDIUM,
            RetryPolicy.SAFE_AUTO_RETRY,
            503,
            "error.network.unavailable",
            UserAction.WAIT,
            "none",
            "warning",
            "dependency",
            FailureClass.NETWORK,
            "Service unavailable",
        ),
        ErrorSpec(
            "BD-DATA-STALE",
            "data_freshness",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.MEDIUM,
            RetryPolicy.SAFE_USER_RETRY,
            200,
            "error.market_data.delayed",
            UserAction.REFRESH,
            "none",
            "warning",
            "data",
            FailureClass.MARKET_DATA,
            "Data delayed",
            "Market Data",
        ),
        ErrorSpec(
            "BD-DATA-PARTIAL",
            "data_quality",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.MEDIUM,
            RetryPolicy.SAFE_USER_RETRY,
            200,
            "error.data.partial",
            UserAction.REVIEW_DATA,
            "none",
            "warning",
            "data",
            FailureClass.MARKET_DATA,
            "Partial data",
            "Market Data",
        ),
        ErrorSpec(
            "BD-PAY-IND",
            "billing",
            CertaintyState.INDETERMINATE,
            Severity.ERROR,
            UserImpact.HIGH,
            RetryPolicy.RECONCILE_FIRST,
            409,
            "error.payment.indeterminate",
            UserAction.CHECK_STATUS,
            "always",
            "error",
            "billing",
            FailureClass.PAYMENT_PROVIDER,
            "Payment outcome unknown",
            "Billing",
        ),
        ErrorSpec(
            "BD-PAY-DECL",
            "billing",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.HIGH,
            RetryPolicy.DO_NOT_RETRY,
            402,
            "error.payment.declined",
            UserAction.UPDATE_PAYMENT,
            "high_impact",
            "warning",
            "billing",
            FailureClass.PAYMENT_PROVIDER,
            "Payment declined",
            "Billing",
        ),
        ErrorSpec(
            "BD-AI-PRES",
            "ai",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.LOW,
            RetryPolicy.SAFE_USER_RETRY,
            503,
            "error.ai.presentation",
            UserAction.RETRY,
            "none",
            "warning",
            "ai",
            FailureClass.AI_PRESENTATION,
            "Presentation unavailable",
            "AI Intelligence",
        ),
        ErrorSpec(
            "BD-AI-EVID",
            "ai",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.MEDIUM,
            RetryPolicy.DO_NOT_RETRY,
            503,
            "error.ai.evidence",
            UserAction.REVIEW_DATA,
            "none",
            "warning",
            "ai",
            FailureClass.AI_EVIDENCE,
            "Insufficient evidence",
            "AI Intelligence",
        ),
        ErrorSpec(
            "BD-DEC-ABST",
            "decision",
            CertaintyState.CONFIRMED,
            Severity.INFO,
            UserImpact.MEDIUM,
            RetryPolicy.DO_NOT_RETRY,
            200,
            "error.decision.abstain",
            UserAction.REVIEW_DATA,
            "none",
            "info",
            "decision",
            FailureClass.AI_EVIDENCE,
            "Decision abstained",
            "Analytics",
        ),
        ErrorSpec(
            "BD-MAINT-001",
            "maintenance",
            CertaintyState.CONFIRMED,
            Severity.INFO,
            UserImpact.MEDIUM,
            RetryPolicy.SAFE_AUTO_RETRY,
            503,
            "error.maintenance",
            UserAction.VIEW_STATUS,
            "none",
            "info",
            "maintenance",
            FailureClass.MAINTENANCE,
            "Maintenance",
            "API",
        ),
        ErrorSpec(
            "BD-OFFLINE-001",
            "offline",
            CertaintyState.CONFIRMED,
            Severity.WARNING,
            UserImpact.MEDIUM,
            RetryPolicy.SAFE_AUTO_RETRY,
            503,
            "error.offline",
            UserAction.WAIT,
            "none",
            "warning",
            "client",
            FailureClass.OFFLINE,
            "Offline",
        ),
        ErrorSpec(
            "BD-UP-502",
            "upstream",
            CertaintyState.CONFIRMED,
            Severity.ERROR,
            UserImpact.MEDIUM,
            RetryPolicy.SAFE_AUTO_RETRY,
            502,
            "error.upstream.bad_gateway",
            UserAction.RETRY,
            "high_impact",
            "error",
            "dependency",
            FailureClass.UPSTREAM,
            "Upstream error",
        ),
        ErrorSpec(
            "BD-UP-504",
            "upstream",
            CertaintyState.CONFIRMED,
            Severity.ERROR,
            UserImpact.MEDIUM,
            RetryPolicy.SAFE_AUTO_RETRY,
            504,
            "error.upstream.timeout",
            UserAction.RETRY,
            "high_impact",
            "error",
            "dependency",
            FailureClass.TIMEOUT,
            "Upstream timeout",
        ),
        ErrorSpec(
            "BD-RECON-001",
            "reconciliation",
            CertaintyState.INDETERMINATE,
            Severity.WARNING,
            UserImpact.HIGH,
            RetryPolicy.RECONCILE_FIRST,
            409,
            "error.reconciliation.pending",
            UserAction.CHECK_STATUS,
            "always",
            "warning",
            "billing",
            FailureClass.RECONCILIATION,
            "Reconciliation pending",
            "Billing",
        ),
    ]
    for spec in entries:
        _register(spec)


bootstrap_registry()


def build_problem_from_spec(
    spec: ErrorSpec,
    *,
    correlation_id: str,
    detail: str | None = None,
    retry_after: int | None = None,
    instance: str | None = None,
    support_reference: str | None = None,
    extra: dict[str, Any] | None = None,
) -> "ProblemDetail":
    from failure.problem import ProblemDetail, opaque_instance_id, retryable_from_policy

    support = support_reference
    if support is None and spec.support_reference_policy == "always":
        support = correlation_id[:8].upper() if correlation_id else None
    elif support is None and spec.support_reference_policy == "high_impact" and spec.user_impact in {
        UserImpact.HIGH,
        UserImpact.CRITICAL,
    }:
        support = correlation_id[:8].upper() if correlation_id else None

    return ProblemDetail(
        type=f"{PROBLEM_TYPE_BASE}/{spec.error_code.lower()}",
        title=spec.title,
        status=spec.http_status or 500,
        detail=detail or spec.title,
        instance=instance or opaque_instance_id(),
        error_code=spec.error_code,
        correlation_id=correlation_id,
        retryable=retryable_from_policy(spec.retry_policy),
        retry_after=retry_after,
        certainty=spec.certainty.value,
        affected_component=spec.affected_component,
        user_action=spec.user_action.value,
        support_reference=support,
        message_key=spec.message_key,
        failure_class=spec.failure_class.value,
        user_impact=spec.user_impact.value,
        retry_policy=spec.retry_policy.value,
    )
