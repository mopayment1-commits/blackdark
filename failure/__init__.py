"""BLACKDARK institutional failure, degraded mode, and recovery architecture (ERR-001 → ERR-050)."""

from failure.dimensions import CertaintyState, FailureClass, Severity, UserImpact
from failure.problem import ProblemDetail, problem_response
from failure.registry import ErrorSpec, get_error_spec, list_error_specs
from failure.states import FailureState, MutationOutcome, ReconciliationState
from failure.user_action import UserAction

__all__ = [
    "CertaintyState",
    "ErrorSpec",
    "FailureClass",
    "FailureState",
    "MutationOutcome",
    "ProblemDetail",
    "ReconciliationState",
    "Severity",
    "UserAction",
    "UserImpact",
    "get_error_spec",
    "list_error_specs",
    "problem_response",
]
