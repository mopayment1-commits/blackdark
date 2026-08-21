"""Domain capability handlers — real backends only."""

from cap646.handlers.ai import handle_ai_capability
from cap646.handlers.alerts import handle_alerts_capability
from cap646.handlers.data import handle_data_capability
from cap646.handlers.derivatives import handle_derivatives_capability
from cap646.handlers.execution import handle_execution_capability
from cap646.handlers.institutional import handle_institutional_capability
from cap646.handlers.market import handle_market_capability
from cap646.handlers.onchain import handle_onchain_capability
from cap646.handlers.verified import handle_verified_capability

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