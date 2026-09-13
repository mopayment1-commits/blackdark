"""AI failure decomposition — user impact, not stack traces (ERR-014)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from failure.registry import build_problem_from_spec, get_error_spec


class AIFailureKind(StrEnum):
    PRESENTATION = "presentation"
    REASONING = "reasoning"
    EVIDENCE = "evidence"


def classify_ai_failure(exc: BaseException | None = None, *, context: str | None = None) -> AIFailureKind:
    msg = (str(exc) if exc else context or "").lower()
    if any(k in msg for k in ("evidence", "data", "source", "quality", "stale", "partial")):
        return AIFailureKind.EVIDENCE
    if any(k in msg for k in ("orchestr", "reason", "plan", "chain")):
        return AIFailureKind.REASONING
    return AIFailureKind.PRESENTATION


def ai_problem(
    kind: AIFailureKind,
    *,
    correlation_id: str,
    detail: str | None = None,
) -> Any:
    code = {
        AIFailureKind.PRESENTATION: "BD-AI-PRES",
        AIFailureKind.REASONING: "BD-AI-PRES",
        AIFailureKind.EVIDENCE: "BD-AI-EVID",
    }[kind]
    spec = get_error_spec(code)
    assert spec is not None
    return build_problem_from_spec(spec, correlation_id=correlation_id, detail=detail)
