"""
BLACKDARK — Central guard for strict WS-only price ingestion policy.

When PRICE_FEED_WS_ONLY=true, any REST/HTTP price fetch must go through this guard.
"""

from __future__ import annotations

import logging

import config

logger = logging.getLogger("BLACKDARK.PriceFeedGuard")


class RestPriceIngestionBlocked(RuntimeError):
    """Raised when code attempts REST price ingestion in WS-only mode."""


def ws_only_mode() -> bool:
    return getattr(config, "PRICE_FEED_WS_ONLY", True)


def rest_price_ingestion_allowed() -> bool:
    return not ws_only_mode()


def assert_rest_price_allowed(context: str) -> None:
    if ws_only_mode():
        raise RestPriceIngestionBlocked(
            f"REST price ingestion forbidden in WS-only mode | context={context}"
        )


def is_ws_price_venue(exchange: str) -> bool:
    return exchange.strip().lower() in getattr(config, "WS_PRICE_VENUES", frozenset())


def should_skip_ingestion_category(category: str) -> bool:
    """Skip REST price lake pulls when live prices come from WebSocket streams."""
    return ws_only_mode() and category == "prices"
