"""Field availability markers for Decision Contract (P1)."""

from __future__ import annotations

from typing import Any, Literal

FieldAvailability = Literal["AVAILABLE", "UNAVAILABLE", "NOT_APPLICABLE"]


def field_value(
    value: Any,
    *,
    available: bool,
    not_applicable: bool = False,
    reason: str | None = None,
) -> dict[str, Any]:
    if not_applicable:
        state: FieldAvailability = "NOT_APPLICABLE"
    elif available:
        state = "AVAILABLE"
    else:
        state = "UNAVAILABLE"
    return {"state": state, "value": value, "reason": reason}
