"""Shared OpenAPI error response docs for FastAPI (RFC 9457 problem details)."""

from __future__ import annotations

from typing import Any

PROBLEM_JSON_SCHEMA = {
    "application/problem+json": {
        "schema": {
            "type": "object",
            "required": ["type", "title", "status", "detail", "instance", "error_code", "correlation_id"],
            "properties": {
                "type": {"type": "string"},
                "title": {"type": "string"},
                "status": {"type": "integer"},
                "detail": {"type": "string"},
                "instance": {"type": "string"},
                "error_code": {"type": "string"},
                "correlation_id": {"type": "string"},
                "retryable": {"type": "boolean"},
                "retry_after": {"type": "integer"},
                "certainty": {"type": "string"},
                "data_freshness": {"type": "string"},
                "affected_component": {"type": "string"},
                "user_action": {"type": "string"},
                "support_reference": {"type": "string"},
                "message_key": {"type": "string"},
            },
        }
    }
}

COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"description": "Bad request", "content": PROBLEM_JSON_SCHEMA},
    401: {"description": "Unauthorized", "content": PROBLEM_JSON_SCHEMA},
    403: {"description": "Forbidden", "content": PROBLEM_JSON_SCHEMA},
    404: {"description": "Not found", "content": PROBLEM_JSON_SCHEMA},
    409: {"description": "Conflict / indeterminate", "content": PROBLEM_JSON_SCHEMA},
    422: {"description": "Validation error", "content": PROBLEM_JSON_SCHEMA},
    429: {"description": "Too many requests", "content": PROBLEM_JSON_SCHEMA},
    500: {"description": "Internal server error", "content": PROBLEM_JSON_SCHEMA},
    502: {"description": "Bad gateway", "content": PROBLEM_JSON_SCHEMA},
    503: {"description": "Service unavailable", "content": PROBLEM_JSON_SCHEMA},
    504: {"description": "Gateway timeout", "content": PROBLEM_JSON_SCHEMA},
}
