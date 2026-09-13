"""Field-level validation error contract (ERR-028)."""

from __future__ import annotations

from typing import Any

from failure.problem import ProblemDetail, opaque_instance_id
from failure.registry import get_error_spec, build_problem_from_spec
from failure.correlation import require_correlation_id


def validation_problem(errors: list[dict[str, Any]], *, correlation_id: str | None = None) -> ProblemDetail:
    cid = correlation_id or require_correlation_id()
    spec = get_error_spec("BD-VAL-001")
    assert spec is not None
    fields = []
    for err in errors:
        loc = err.get("loc") or ()
        field = ".".join(str(x) for x in loc if x not in {"body", "query"})
        fields.append(
            {
                "field": field or "form",
                "message_key": "error.validation.field",
                "detail": err.get("msg") or "Invalid value",
            }
        )
    problem = build_problem_from_spec(spec, correlation_id=cid, detail="Validation failed")
    problem.fields = fields
    return problem
