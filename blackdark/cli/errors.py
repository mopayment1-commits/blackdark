"""CLI exit codes — Feature #167."""

from __future__ import annotations

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_AUTH = 2
EXIT_NOT_FOUND = 3
EXIT_USAGE = 4
EXIT_RATE_LIMIT = 5


def exit_code_for_http(status: int) -> int:
    if status == 401 or status == 403:
        return EXIT_AUTH
    if status == 404:
        return EXIT_NOT_FOUND
    if status == 429:
        return EXIT_RATE_LIMIT
    if 400 <= status < 500:
        return EXIT_USAGE
    return EXIT_ERROR
