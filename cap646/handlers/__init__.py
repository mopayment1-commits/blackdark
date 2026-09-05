"""Domain capability handlers — real backends only."""

from typing import Any

__all__ = [
    "handle_data_capability",
    "handle_market_capability",
    "handle_derivatives_capability",
    "handle_execution_capability",
    "handle_onchain_capability",
    "handle_ai_capability",
    "handle_alerts_capability",
    "handle_institutional_capability",
    "handle_verified_capability",
]

_EXPORTS = {
    "handle_data_capability": "cap646.handlers.data",
    "handle_market_capability": "cap646.handlers.market",
    "handle_derivatives_capability": "cap646.handlers.derivatives",
    "handle_execution_capability": "cap646.handlers.execution",
    "handle_onchain_capability": "cap646.handlers.onchain",
    "handle_ai_capability": "cap646.handlers.ai",
    "handle_alerts_capability": "cap646.handlers.alerts",
    "handle_institutional_capability": "cap646.handlers.institutional",
    "handle_verified_capability": "cap646.handlers.verified",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    mod = importlib.import_module(_EXPORTS[name])
    return getattr(mod, name)
