"""Canonical source registry SSOT — wraps data_sources_registry with governance metadata."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from data_sources_registry import DATA_SOURCES, DataSourceSpec, source_by_id, sources_by_category


class SourceTier(StrEnum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    FALLBACK = "FALLBACK"
    VALIDATION_ONLY = "VALIDATION_ONLY"
    EXPERIMENTAL = "EXPERIMENTAL"
    DISALLOWED_FOR_CRITICAL = "DISALLOWED_FOR_CRITICAL_DECISIONS"


class SourceClass(StrEnum):
    CEX_SPOT = "CEX_SPOT"
    CEX_DERIVATIVES = "CEX_DERIVATIVES"
    ORDER_BOOK = "ORDER_BOOK"
    ONCHAIN_RPC = "ONCHAIN_RPC"
    DEFI = "DEFI"
    STABLECOIN = "STABLECOIN"
    ORACLE = "ORACLE"
    WALLET_ENTITY = "WALLET_ENTITY"
    MACRO = "MACRO"
    REGULATORY = "REGULATORY"
    NEWS_EVENT = "NEWS_EVENT"
    SOCIAL_SENTIMENT = "SOCIAL_SENTIMENT"
    SECURITY_INCIDENT = "SECURITY_INCIDENT"
    USER_PORTFOLIO = "USER_PORTFOLIO"


_CATEGORY_TO_CLASS: dict[str, SourceClass] = {
    "prices": SourceClass.CEX_SPOT,
    "onchain": SourceClass.ONCHAIN_RPC,
    "defi": SourceClass.DEFI,
    "news": SourceClass.NEWS_EVENT,
    "sentiment": SourceClass.SOCIAL_SENTIMENT,
    "events": SourceClass.NEWS_EVENT,
    "whale": SourceClass.WALLET_ENTITY,
    "research": SourceClass.NEWS_EVENT,
    "macro": SourceClass.MACRO,
    "regulatory": SourceClass.REGULATORY,
}

_WS_SOURCES = frozenset({"binance_ws"})
_L2_CAPABLE = frozenset({"binance_ws", "binance_spot", "okx_spot", "bybit_spot", "coinbase_spot", "kraken_spot"})
_L3_CAPABLE = frozenset({"coinbase_spot"})


@dataclass(frozen=True)
class SourceRegistryEntry:
    source_id: str
    provider_name: str
    endpoint: str
    data_domain: str
    source_class: SourceClass
    auth_model: str
    credential_owner: str
    account_requirement: str
    env_key: str | None
    transport: str
    update_cadence_seconds: int
    expected_latency_ms: int | None
    internal_slo_class: str
    rate_limit_notes: str
    historical_depth: str
    l1: bool
    l2: bool
    l3: bool
    tier: SourceTier
    fallback_sources: tuple[str, ...]
    commercial_use_status: str
    redistribution_status: str
    data_owner: str
    schema_version: str
    parser_version: str
    status: str


def _auth_model(spec: DataSourceSpec) -> str:
    if spec.env_key:
        return "api_key"
    if spec.fetch_kind == "websocket":
        return "public_ws"
    return "public_rest"


def _tier_for(spec: DataSourceSpec) -> SourceTier:
    if spec.source_id in _WS_SOURCES or spec.fetch_kind == "websocket":
        return SourceTier.PRIMARY
    if spec.env_key and "COINMARKETCAP" in (spec.env_key or "").upper():
        return SourceTier.SECONDARY
    if spec.category in {"sentiment", "research"}:
        return SourceTier.VALIDATION_ONLY
    if spec.fetch_kind == "internal":
        return SourceTier.PRIMARY
    return SourceTier.SECONDARY


def _fallbacks(spec: DataSourceSpec) -> tuple[str, ...]:
    fb: list[str] = []
    if spec.category == "prices" and spec.source_id != "coingecko_prices":
        fb.append("coingecko_prices")
    if spec.fetch_kind == "websocket":
        fb.append("binance_spot")
    return tuple(fb)


def enrich_source_spec(spec: DataSourceSpec) -> SourceRegistryEntry:
    sc = _CATEGORY_TO_CLASS.get(spec.category, SourceClass.CEX_SPOT)
    if "futures" in spec.source_id or "swap" in spec.source_id or "linear" in spec.source_id:
        sc = SourceClass.CEX_DERIVATIVES
    if spec.fetch_kind == "websocket" or "ws" in spec.source_id:
        sc = SourceClass.ORDER_BOOK
    return SourceRegistryEntry(
        source_id=spec.source_id,
        provider_name=spec.name,
        endpoint=spec.url,
        data_domain=spec.category,
        source_class=sc,
        auth_model=_auth_model(spec),
        credential_owner="platform_ops",
        account_requirement="none" if not spec.env_key else "api_key_required",
        env_key=spec.env_key,
        transport=spec.fetch_kind,
        update_cadence_seconds=spec.interval_seconds or 0,
        expected_latency_ms=500 if spec.fetch_kind == "websocket" else 5000,
        internal_slo_class="T0" if spec.fetch_kind == "websocket" else "T1",
        rate_limit_notes=spec.notes or "provider_default",
        historical_depth="live_only" if spec.fetch_kind == "websocket" else "rest_backfill",
        l1=True,
        l2=spec.source_id in _L2_CAPABLE,
        l3=spec.source_id in _L3_CAPABLE,
        tier=_tier_for(spec),
        fallback_sources=_fallbacks(spec),
        commercial_use_status="review_required" if spec.env_key else "public_feed_review_required",
        redistribution_status="internal_analysis_default",
        data_owner="platform_ops",
        schema_version="1.0.0",
        parser_version="1.0.0",
        status="active",
    )


def get_registry_entry(source_id: str) -> SourceRegistryEntry | None:
    spec = source_by_id(source_id)
    if spec is None:
        return None
    return enrich_source_spec(spec)


def canonical_source_registry() -> list[SourceRegistryEntry]:
    return [enrich_source_spec(s) for s in DATA_SOURCES]


def registry_summary() -> dict[str, Any]:
    entries = canonical_source_registry()
    by_class: dict[str, int] = {}
    by_tier: dict[str, int] = {}
    keyed = 0
    for e in entries:
        by_class[e.source_class.value] = by_class.get(e.source_class.value, 0) + 1
        by_tier[e.tier.value] = by_tier.get(e.tier.value, 0) + 1
        if e.env_key:
            keyed += 1
    return {
        "total_sources": len(entries),
        "by_source_class": by_class,
        "by_tier": by_tier,
        "credential_required_count": keyed,
        "registry_authority": "data_governance/registry.py",
        "catalog_authority": "data_sources_registry.py",
    }


def critical_sources() -> list[SourceRegistryEntry]:
    critical_ids = {
        "binance_ws", "binance_spot", "coingecko_prices", "kraken_spot",
        "okx_spot", "bybit_spot", "coinbase_spot", "defillama_tvl", "fred",
    }
    return [e for e in canonical_source_registry() if e.source_id in critical_ids]


def sources_for_class(source_class: SourceClass) -> list[SourceRegistryEntry]:
    return [e for e in canonical_source_registry() if e.source_class == source_class]


def lookup_by_category(category: str) -> list[SourceRegistryEntry]:
    return [enrich_source_spec(s) for s in sources_by_category(category)]  # type: ignore[arg-type]
