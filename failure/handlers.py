"""FastAPI exception handlers and compatibility layer (ERR-003, ERR-005, ERR-029–031)."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError

from failure.correlation import require_correlation_id
from failure.logging import log_failure
from failure.observability import record_failure_sli
from failure.problem import ProblemDetail, problem_response
from failure.registry import build_problem_from_spec, get_error_spec, spec_for_http_status
from failure.validation import validation_problem
from safe_errors import public_error


def _status_to_code(status: int) -> str:
    mapping = {
        401: "BD-AUTH-001",
        403: "BD-AUTHZ-001",
        404: "BD-GEN-001",
        409: "BD-RECON-001",
        422: "BD-VAL-001",
        429: "BD-RATE-001",
        502: "BD-UP-502",
        503: "BD-NET-001",
        504: "BD-UP-504",
    }
    return mapping.get(status, "BD-GEN-001")


async def http_exception_handler(request: Request, exc: HTTPException):
    cid = require_correlation_id()
    lang = _request_lang(request)
    code = _status_to_code(exc.status_code)
    if isinstance(exc.detail, dict) and exc.detail.get("error_code"):
        code = str(exc.detail["error_code"])
    spec = get_error_spec(code) or spec_for_http_status(exc.status_code)
    detail = public_error(None, fallback=str(exc.detail))
    if isinstance(exc.detail, dict):
        detail = str(exc.detail.get("detail") or exc.detail.get("message") or detail)
    elif isinstance(exc.detail, str):
        detail = public_error(None, fallback=exc.detail)
    retry_after = None
    if exc.status_code == 429 and exc.headers:
        try:
            retry_after = int(exc.headers.get("Retry-After", 0))
        except Exception:
            retry_after = None
    problem = build_problem_from_spec(
        spec,
        correlation_id=cid,
        detail=detail,
        retry_after=retry_after,
    )
    _emit_failure_log(request, problem, exc)
    return problem_response(problem, lang=lang)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    cid = require_correlation_id()
    lang = _request_lang(request)
    errors = exc.errors()
    problem = validation_problem(errors, correlation_id=cid)
    _emit_failure_log(request, problem, exc)
    return problem_response(problem, lang=lang)


async def unhandled_exception_handler(request: Request, exc: Exception):
    cid = require_correlation_id()
    lang = _request_lang(request)
    spec = get_error_spec("BD-GEN-001")
    assert spec is not None
    problem = build_problem_from_spec(
        spec,
        correlation_id=cid,
        detail=public_error(exc, fallback="Request failed"),
    )
    _emit_failure_log(request, problem, exc)
    return problem_response(problem, lang=lang)


def register_exception_handlers(app) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)


def _request_lang(request: Request) -> str | None:
    try:
        from i18n_service import resolve_request_lang

        return resolve_request_lang(request)
    except Exception:
        return None


def _emit_failure_log(request: Request, problem: ProblemDetail, exc: BaseException | None) -> None:
    record_failure_sli(
        failure_class=problem.failure_class or "INTERNAL",
        indeterminate=problem.certainty == "INDETERMINATE",
    )
    log_failure(
        correlation_id=problem.correlation_id,
        component=problem.affected_component or "api",
        operation=f"{request.method} {request.url.path}",
        failure_class=problem.failure_class or "INTERNAL",
        certainty=problem.certainty,
        severity="ERROR",
        user_impact=problem.user_impact or "MEDIUM",
        message_key=problem.message_key,
        exc=exc,
    )
