"""
Unified Connector Layer (#194) — shared fetch/normalize/fallback for external APIs.

Tronscan (#103) and future chain connectors use this instead of bespoke HTTP logic.
"""

from __future__ import annotations

import logging
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.UnifiedConnector")

_DEFAULT_CACHE = IngestionCache(default_ttl_sec=300, max_ttl_sec=86400)


class UnifiedConnector:
    """Thin wrapper over connector_cache with per-source slug + fail-closed semantics."""

    def __init__(self, *, source_slug: str, cache: IngestionCache | None = None) -> None:
        self.source_slug = source_slug
        self.cache = cache or _DEFAULT_CACHE

    def ttl(self, env_key: str, default: int) -> int:
        return self.cache.ttl(env_key, default)

    async def get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_sec: float = 3.0,
        cache_parts: tuple[Any, ...],
        ttl: int,
    ) -> dict[str, Any]:
        ck = cache_key(self.source_slug, *cache_parts)
        return await self.cache.http_get_json(
            url,
            params=params,
            headers=headers,
            timeout_sec=timeout_sec,
            cache_key=ck,
            ttl=ttl,
            source_slug=self.source_slug,
        )

    async def get_text(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_sec: float = 3.0,
        cache_parts: tuple[Any, ...],
        ttl: int,
    ) -> dict[str, Any]:
        ck = cache_key(self.source_slug, *cache_parts)
        return await self.cache.http_get(
            url,
            params=params,
            headers=headers,
            timeout_sec=timeout_sec,
            cache_key=ck,
            ttl=ttl,
            source_slug=self.source_slug,
        )
