"""BLACKDARK Canonical Data Layer — single semantic authority for critical datums.

Every critical intelligence path should ingest CanonicalDatum (or typed subtypes)
rather than ad-hoc provider dicts. Unknown/malformed input is rejected; missing
required provenance fails closed for LIVE classification.
"""

from __future__ import annotations

import re
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


SCHEMA_VERSION = "1.0.0"


class EntityType(str, Enum):
    ASSET = "asset"
    INSTRUMENT = "instrument"
    MARKET = "market"
    VENUE = "venue"
    CHAIN = "chain"
    CONTRACT = "contract"
    SYMBOL = "symbol"
    QUOTE = "quote"
    TRADE = "trade"
    ORDER_BOOK = "order_book"
    FUNDING = "funding"
    OPEN_INTEREST = "open_interest"
    LIQUIDATION = "liquidation"
    DERIVATIVE = "derivative"
    WALLET = "wallet"
    ENTITY = "entity"
    PROTOCOL = "protocol"
    NEWS_EVENT = "news_event"
    MACRO_EVENT = "macro_event"
    PORTFOLIO = "portfolio"
    POSITION = "position"
    OPPORTUNITY = "opportunity"
    DECISION = "decision"
    EVIDENCE = "evidence"
    RISK = "risk"
    EXECUTION = "execution"
    OUTCOME = "outcome"


class NormalizationStatus(str, Enum):
    RAW = "raw"
    NORMALIZED = "normalized"
    REJECTED = "rejected"
    CONFLICT = "conflict"


class FreshnessClass(str, Enum):
    LIVE = "LIVE"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


_VENUE_ALIASES = {
    "binanceusdm": "binance",
    "binance-futures": "binance",
    "okex": "okx",
    "okx-swap": "okx",
    "bybit-spot": "bybit",
    "bybit-linear": "bybit",
}

_CHAIN_ALIASES = {
    "eth": "ethereum",
    "ether": "ethereum",
    "arb": "arbitrum",
    "matic": "polygon",
    "bsc": "bnb",
    "binance-smart-chain": "bnb",
}


def _utcnow() -> datetime:
    return datetime.now(UTC)


def normalize_venue(name: str) -> str:
    raw = (name or "").strip().lower()
    if not raw:
        raise ValueError("venue_empty")
    return _VENUE_ALIASES.get(raw, raw)


def normalize_chain(name: str) -> str:
    raw = (name or "").strip().lower()
    if not raw:
        raise ValueError("chain_empty")
    return _CHAIN_ALIASES.get(raw, raw)


def normalize_symbol(symbol: str) -> str:
    raw = (symbol or "").strip().upper().replace("-", "/")
    if not raw:
        raise ValueError("symbol_empty")
    if "/" not in raw:
        for quote in ("USDT", "USD", "USDC", "BTC", "ETH"):
            if raw.endswith(quote) and len(raw) > len(quote):
                return f"{raw[: -len(quote)]}/{quote}"
        raise ValueError(f"symbol_unparseable:{symbol}")
    base, quote = raw.split("/", 1)
    if not base or not quote:
        raise ValueError(f"symbol_invalid:{symbol}")
    return f"{base}/{quote}"


def normalize_ts(value: Any) -> datetime:
    if value is None:
        raise ValueError("timestamp_missing")
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=UTC)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"timestamp_invalid:{value}") from exc
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


@dataclass
class Provenance:
    source: str
    provider_timestamp: datetime | None
    ingestion_timestamp: datetime
    freshness_class: FreshnessClass
    quality: float
    confidence: float
    confidence_type: str = "heuristic_score"
    normalization_status: NormalizationStatus = NormalizationStatus.NORMALIZED
    schema_version: str = SCHEMA_VERSION
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["provider_timestamp"] = (
            self.provider_timestamp.isoformat() if self.provider_timestamp else None
        )
        d["ingestion_timestamp"] = self.ingestion_timestamp.isoformat()
        d["freshness_class"] = self.freshness_class.value
        d["normalization_status"] = self.normalization_status.value
        return d


@dataclass
class CanonicalDatum:
    entity_type: EntityType
    id: str
    payload: dict[str, Any]
    provenance: Provenance
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type.value,
            "id": self.id,
            "payload": self.payload,
            "provenance": self.provenance.to_dict(),
            "tags": dict(self.tags),
        }


def classify_freshness(
    *,
    provider_ts: datetime | None,
    max_live_age_sec: float,
    max_degraded_age_sec: float,
    now: datetime | None = None,
) -> FreshnessClass:
    if provider_ts is None:
        return FreshnessClass.UNKNOWN
    now = now or _utcnow()
    age = (now - provider_ts).total_seconds()
    if age < 0:
        return FreshnessClass.UNKNOWN
    if age <= max_live_age_sec:
        return FreshnessClass.LIVE
    if age <= max_degraded_age_sec:
        return FreshnessClass.DEGRADED
    return FreshnessClass.STALE


def assert_not_stale_as_live(freshness: FreshnessClass) -> None:
    if freshness is FreshnessClass.LIVE:
        return
    raise ValueError(f"stale_as_live_forbidden:{freshness.value}")


def quality_score(
    *,
    has_provider_ts: bool,
    normalized_ok: bool,
    source_health: float = 1.0,
) -> float:
    score = 0.0
    if normalized_ok:
        score += 0.5
    if has_provider_ts:
        score += 0.3
    score += 0.2 * max(0.0, min(1.0, float(source_health)))
    return round(score, 4)


_DEDUP: dict[str, CanonicalDatum] = {}
_CONFLICTS: list[dict[str, Any]] = []


def _dedup_key(entity_type: EntityType, id_: str) -> str:
    return f"{entity_type.value}:{id_}"


def ingest(
    *,
    entity_type: EntityType,
    id: str,
    payload: dict[str, Any],
    source: str,
    provider_timestamp: Any = None,
    max_live_age_sec: float = 2.0,
    max_degraded_age_sec: float = 15.0,
    source_health: float = 1.0,
    tags: dict[str, str] | None = None,
    require_provider_ts: bool = True,
) -> CanonicalDatum:
    if not source or not str(source).strip():
        raise ValueError("source_required")
    if not id or not str(id).strip():
        raise ValueError("id_required")
    if not isinstance(payload, dict):
        raise ValueError("payload_must_be_dict")

    ingestion_ts = _utcnow()
    provider_ts: datetime | None = None
    if provider_timestamp is not None:
        provider_ts = normalize_ts(provider_timestamp)
    elif require_provider_ts:
        raise ValueError("provider_timestamp_required")

    norm_payload = dict(payload)
    if "venue" in norm_payload:
        norm_payload["venue"] = normalize_venue(str(norm_payload["venue"]))
    if "exchange" in norm_payload:
        norm_payload["exchange"] = normalize_venue(str(norm_payload["exchange"]))
    if "chain" in norm_payload:
        norm_payload["chain"] = normalize_chain(str(norm_payload["chain"]))
    if "symbol" in norm_payload:
        norm_payload["symbol"] = normalize_symbol(str(norm_payload["symbol"]))

    freshness = classify_freshness(
        provider_ts=provider_ts,
        max_live_age_sec=max_live_age_sec,
        max_degraded_age_sec=max_degraded_age_sec,
        now=ingestion_ts,
    )
    q = quality_score(
        has_provider_ts=provider_ts is not None,
        normalized_ok=True,
        source_health=source_health,
    )
    prov = Provenance(
        source=str(source).strip(),
        provider_timestamp=provider_ts,
        ingestion_timestamp=ingestion_ts,
        freshness_class=freshness,
        quality=q,
        confidence=q,
        confidence_type="heuristic_score",
        normalization_status=NormalizationStatus.NORMALIZED,
    )
    datum = CanonicalDatum(
        entity_type=entity_type,
        id=str(id).strip(),
        payload=norm_payload,
        provenance=prov,
        tags=dict(tags or {}),
    )

    key = _dedup_key(entity_type, datum.id)
    prior = _DEDUP.get(key)
    if prior is not None:
        if prior.provenance.source != datum.provenance.source and prior.payload != datum.payload:
            _CONFLICTS.append(
                {
                    "id": datum.id,
                    "entity_type": entity_type.value,
                    "prior_source": prior.provenance.source,
                    "new_source": datum.provenance.source,
                    "at": ingestion_ts.isoformat(),
                }
            )
            prior_ts = prior.provenance.provider_timestamp or datetime.min.replace(tzinfo=UTC)
            new_ts = provider_ts or datetime.min.replace(tzinfo=UTC)
            if new_ts < prior_ts:
                return prior
    _DEDUP[key] = datum
    return datum


def get_datum(entity_type: EntityType, id: str) -> CanonicalDatum | None:
    return _DEDUP.get(_dedup_key(entity_type, id))


def conflicts() -> list[dict[str, Any]]:
    return list(_CONFLICTS)


def reset_store_for_tests() -> None:
    _DEDUP.clear()
    _CONFLICTS.clear()


def ingest_quote(
    *,
    venue: str,
    symbol: str,
    bid: float,
    ask: float,
    source: str,
    provider_timestamp: Any,
    bid_qty: float | None = None,
    ask_qty: float | None = None,
) -> CanonicalDatum:
    if bid <= 0 or ask <= 0 or ask < bid:
        raise ValueError("quote_malformed")
    v = normalize_venue(venue)
    s = normalize_symbol(symbol)
    return ingest(
        entity_type=EntityType.QUOTE,
        id=f"{v}:{s}",
        payload={
            "venue": v,
            "symbol": s,
            "bid": float(bid),
            "ask": float(ask),
            "bid_qty": float(bid_qty) if bid_qty is not None else None,
            "ask_qty": float(ask_qty) if ask_qty is not None else None,
            "mid": (float(bid) + float(ask)) / 2.0,
        },
        source=source,
        provider_timestamp=provider_timestamp,
        max_live_age_sec=2.0,
        max_degraded_age_sec=10.0,
    )


def live_payload_or_raise(datum: CanonicalDatum) -> dict[str, Any]:
    assert_not_stale_as_live(datum.provenance.freshness_class)
    return dict(datum.payload)


_SAFE_ID = re.compile(r"^[A-Za-z0-9_.:/=+\-]{1,128}$")


def validate_id(id_: str) -> str:
    if not _SAFE_ID.match(id_ or ""):
        raise ValueError("id_charset_invalid")
    return id_


def layer_status() -> dict[str, Any]:
    return {
        "surface": "canonical_data_layer",
        "schema_version": SCHEMA_VERSION,
        "entities_cached": len(_DEDUP),
        "conflicts": len(_CONFLICTS),
        "product_complete": True,
        "note": "Canonical authority for normalized+provenance datums. "
        "Confidence fields are heuristic_score unless calibration says otherwise.",
        "monotonic_ms": int(time.time() * 1000),
    }
