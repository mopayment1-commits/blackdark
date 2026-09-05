"""826 RTM classification — isolated from cap978 gate verdict namespace."""

from __future__ import annotations

from typing import Any


def runtime_classification(result: dict[str, Any]) -> str:
    """826 RTM classification — VERIFIED_COMPLETE is banned for inventory reporting."""
    return "PRODUCTION-ALIGNED" if result.get("success") else "NOT_COMPLETE"
