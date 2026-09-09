"""Payment provider error normalization (ERR-032)."""

from __future__ import annotations

from typing import Any

from failure.registry import build_problem_from_spec, get_error_spec


def normalize_payment_error(
    *,
    provider_code: str | None,
    correlation_id: str,
    indeterminate: bool = False,
) -> Any:
    if indeterminate:
        spec = get_error_spec("BD-PAY-IND")
    else:
        spec = get_error_spec("BD-PAY-DECL")
    assert spec is not None
    detail = None
    if provider_code:
        detail = spec.title
    return build_problem_from_spec(
        spec,
        correlation_id=correlation_id,
        detail=detail,
    )
