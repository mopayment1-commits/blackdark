"""RFC 9457 problem details with BLACKDARK extensions (ERR-003, ERR-042)."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from failure.dimensions import CertaintyState, RetryPolicy
from failure.user_action import UserAction


def opaque_instance_id() -> str:
    return f"bd-{uuid.uuid4().hex[:16]}"


@dataclass(slots=True)
class ProblemDetail:
    type: str
    title: str
    status: int
    detail: str
    instance: str = field(default_factory=opaque_instance_id)
    error_code: str = "BD-GEN-001"
    correlation_id: str = ""
    retryable: bool = False
    retry_after: int | None = None
    certainty: str = CertaintyState.CONFIRMED.value
    data_freshness: str | None = None
    affected_component: str | None = None
    user_action: str = UserAction.NONE.value
    support_reference: str | None = None
    message_key: str | None = None
    failure_class: str | None = None
    user_impact: str | None = None
    retry_policy: str | None = None
    fields: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": self.instance,
            "error_code": self.error_code,
            "correlation_id": self.correlation_id,
            "retryable": self.retryable,
            "certainty": self.certainty,
            "user_action": self.user_action,
        }
        if self.retry_after is not None:
            out["retry_after"] = self.retry_after
        if self.data_freshness:
            out["data_freshness"] = self.data_freshness
        if self.affected_component:
            out["affected_component"] = self.affected_component
        if self.support_reference:
            out["support_reference"] = self.support_reference
        if self.message_key:
            out["message_key"] = self.message_key
        if self.failure_class:
            out["failure_class"] = self.failure_class
        if self.user_impact:
            out["user_impact"] = self.user_impact
        if self.retry_policy:
            out["retry_policy"] = self.retry_policy
        if self.fields:
            out["fields"] = self.fields
        return out

    def localized_detail(self, lang: str | None = None) -> str:
        if not self.message_key:
            return self.detail
        try:
            from i18n_service import t

            return t(self.message_key, lang, **self._format_kwargs())
        except Exception:
            return self.detail

    def _format_kwargs(self) -> dict[str, Any]:
        kw: dict[str, Any] = {}
        if self.retry_after is not None:
            kw["seconds"] = self.retry_after
        if self.support_reference:
            kw["reference"] = self.support_reference
        return kw


def problem_response(problem: ProblemDetail, *, lang: str | None = None):
    from fastapi.responses import JSONResponse

    body = problem.to_dict()
    if lang and problem.message_key:
        body["detail"] = problem.localized_detail(lang)
    return JSONResponse(
        status_code=problem.status,
        content=body,
        media_type="application/problem+json",
        headers=_problem_headers(problem),
    )


def _problem_headers(problem: ProblemDetail) -> dict[str, str]:
    headers: dict[str, str] = {}
    if problem.correlation_id:
        headers["X-Correlation-ID"] = problem.correlation_id
    if problem.retry_after is not None:
        headers["Retry-After"] = str(problem.retry_after)
    return headers


def retryable_from_policy(policy: RetryPolicy | str) -> bool:
    val = policy.value if isinstance(policy, RetryPolicy) else str(policy)
    return val in {RetryPolicy.SAFE_AUTO_RETRY.value, RetryPolicy.SAFE_USER_RETRY.value}
