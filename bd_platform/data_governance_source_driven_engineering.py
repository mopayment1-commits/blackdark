"""Live verification register separation (DIG-056)."""

from __future__ import annotations

from typing import Any


def live_verification_register() -> dict[str, Any]:
    return {
        "engineering_register": "in_repo",
        "production_verified_register": "blocked_external",
        "separated": True,
    }
