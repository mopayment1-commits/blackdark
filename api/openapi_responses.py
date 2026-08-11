"""Shared OpenAPI error response docs for FastAPI (Sonar python:S8415)."""

from __future__ import annotations

from typing import Any

# Status codes observed across HTTPException raises in this codebase.
COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"description": "Bad request"},
    401: {"description": "Unauthorized"},
    403: {"description": "Forbidden"},
    404: {"description": "Not found"},
    409: {"description": "Conflict"},
    422: {"description": "Validation error"},
    429: {"description": "Too many requests"},
    500: {"description": "Internal server error"},
    502: {"description": "Bad gateway"},
    503: {"description": "Service unavailable"},
}
