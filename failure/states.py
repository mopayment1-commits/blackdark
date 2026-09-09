"""Canonical failure, mutation, and reconciliation state models (ERR-001, ERR-006, ERR-046)."""

from __future__ import annotations

from enum import StrEnum


class FailureState(StrEnum):
    LOADING = "LOADING"
    SUCCESS = "SUCCESS"
    DELAYED = "DELAYED"
    STALE = "STALE"
    PARTIAL = "PARTIAL"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"
    RATE_LIMITED = "RATE_LIMITED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    CONFIRMATION_PENDING = "CONFIRMATION_PENDING"
    INDETERMINATE = "INDETERMINATE"
    RETRYING = "RETRYING"
    MAINTENANCE = "MAINTENANCE"
    ABSTAINED = "ABSTAINED"


class MutationOutcome(StrEnum):
    CONFIRMED_SUCCESS = "CONFIRMED_SUCCESS"
    CONFIRMED_FAILURE = "CONFIRMED_FAILURE"
    INDETERMINATE = "INDETERMINATE"


class ReconciliationState(StrEnum):
    REQUESTED = "REQUESTED"
    PROCESSING = "PROCESSING"
    INDETERMINATE = "INDETERMINATE"
    RECONCILING = "RECONCILING"
    CONFIRMED_SUCCESS = "CONFIRMED_SUCCESS"
    CONFIRMED_FAILURE = "CONFIRMED_FAILURE"


class IncidentLifecycle(StrEnum):
    DETECTED = "DETECTED"
    MITIGATING = "MITIGATING"
    RECOVERING = "RECOVERING"
    RESOLVED = "RESOLVED"


class ComponentStatus(StrEnum):
    OPERATIONAL = "Operational"
    DEGRADED_PERFORMANCE = "Degraded Performance"
    PARTIAL_OUTAGE = "Partial Outage"
    MAJOR_OUTAGE = "Major Outage"
    MAINTENANCE = "Maintenance"


STATE_SEMANTICS: dict[FailureState, dict[str, str]] = {
    FailureState.LOADING: {
        "backend": "operation_in_progress",
        "frontend": "skeleton_or_spinner",
        "retry": "none",
        "user_action": "NONE",
        "observability": "trace_start",
    },
    FailureState.SUCCESS: {
        "backend": "completed_ok",
        "frontend": "render_full",
        "retry": "none",
        "user_action": "NONE",
        "observability": "success_metric",
    },
    FailureState.DELAYED: {
        "backend": "upstream_slow",
        "frontend": "delayed_badge",
        "retry": "SAFE_AUTO_RETRY",
        "user_action": "WAIT",
        "observability": "latency_sli",
    },
    FailureState.STALE: {
        "backend": "data_age_exceeded",
        "frontend": "stale_badge",
        "retry": "SAFE_USER_RETRY",
        "user_action": "REFRESH",
        "observability": "stale_rate",
    },
    FailureState.PARTIAL: {
        "backend": "incomplete_payload",
        "frontend": "partial_banner",
        "retry": "SAFE_USER_RETRY",
        "user_action": "REVIEW_DATA",
        "observability": "partial_rate",
    },
    FailureState.DEGRADED: {
        "backend": "fallback_active",
        "frontend": "degraded_scope",
        "retry": "SAFE_AUTO_RETRY",
        "user_action": "VIEW_STATUS",
        "observability": "fallback_rate",
    },
    FailureState.UNAVAILABLE: {
        "backend": "dependency_down",
        "frontend": "scoped_unavailable",
        "retry": "SAFE_USER_RETRY",
        "user_action": "VIEW_STATUS",
        "observability": "error_rate",
    },
    FailureState.FAILED: {
        "backend": "hard_failure",
        "frontend": "error_panel",
        "retry": "policy_from_registry",
        "user_action": "policy_from_registry",
        "observability": "error_rate",
    },
    FailureState.RATE_LIMITED: {
        "backend": "rate_limit_exceeded",
        "frontend": "rate_limit_message",
        "retry": "WAIT",
        "user_action": "WAIT",
        "observability": "429_rate",
    },
    FailureState.AUTH_REQUIRED: {
        "backend": "unauthenticated",
        "frontend": "sign_in_prompt",
        "retry": "DO_NOT_RETRY",
        "user_action": "SIGN_IN",
        "observability": "401_rate",
    },
    FailureState.PERMISSION_DENIED: {
        "backend": "authorization_denied",
        "frontend": "permission_message",
        "retry": "DO_NOT_RETRY",
        "user_action": "NONE",
        "observability": "403_rate",
    },
    FailureState.CONFIRMATION_PENDING: {
        "backend": "awaiting_confirmation",
        "frontend": "pending_state",
        "retry": "DO_NOT_RETRY",
        "user_action": "WAIT",
        "observability": "pending_count",
    },
    FailureState.INDETERMINATE: {
        "backend": "mutation_outcome_unknown",
        "frontend": "indeterminate_guidance",
        "retry": "RECONCILE_FIRST",
        "user_action": "VIEW_STATUS",
        "observability": "indeterminate_rate",
    },
    FailureState.RETRYING: {
        "backend": "auto_retry_scheduled",
        "frontend": "retry_progress",
        "retry": "SAFE_AUTO_RETRY",
        "user_action": "WAIT",
        "observability": "retry_rate",
    },
    FailureState.MAINTENANCE: {
        "backend": "planned_maintenance",
        "frontend": "maintenance_banner",
        "retry": "WAIT",
        "user_action": "VIEW_STATUS",
        "observability": "maintenance_active",
    },
    FailureState.ABSTAINED: {
        "backend": "decision_abstained",
        "frontend": "abstain_message",
        "retry": "DO_NOT_RETRY",
        "user_action": "REVIEW_DATA",
        "observability": "abstain_rate",
    },
}
