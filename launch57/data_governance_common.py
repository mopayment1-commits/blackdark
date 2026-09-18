"""
Launch-57 data intelligence & governance common layer.

Scope: LAUNCH57_IDS data-critical capabilities only (#21–#30, #38–#43, #53–#57).
Reuses data_governance reconciliation where applicable; does not activate legacy Phase II/III expansion.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from data_governance.reconciliation import reconcile_observations
from launch57.temporal_common import to_rfc3339, utc_now

LAUNCH57_DATA_CRITICAL_IDS: frozenset[int] = frozenset(
    {
        21,
        22,
        23,
        24,
        25,
        26,
        27,
        28,
        29,
        30,
        31,
        38,
        39,
        40,
        41,
        42,
        43,
        53,
        54,
        55,
        56,
        57,
    }
)

REGISTRY_VERSION = "launch57-data-governance-1.0.0"


class SourceRole(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    FALLBACK = "FALLBACK"
    VALIDATION = "VALIDATION"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"
    DERIVED_INTERNAL = "DERIVED_INTERNAL"


@dataclass(frozen=True)
class Launch57SourceEntry:
    source_id: str
    provider: str
    source_role: SourceRole
    source_type: str
    domain: str
    supported_launch_items: tuple[int, ...]
    endpoint_feed: str
    authentication_model: str
    public_private: str
    expected_cadence: str
    coverage: str
    rate_quota_limits: str
    historical_availability: str
    rights_licensing_status: str
    health_state: str
    fallback_eligible: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "provider": self.provider,
            "source_role": self.source_role.value,
            "source_type": self.source_type,
            "domain": self.domain,
            "supported_launch57_capabilities": list(self.supported_launch_items),
            "endpoint_feed": self.endpoint_feed,
            "authentication_model": self.authentication_model,
            "public_private": self.public_private,
            "expected_cadence": self.expected_cadence,
            "coverage": self.coverage,
            "rate_quota_limits": self.rate_quota_limits,
            "historical_availability": self.historical_availability,
            "rights_licensing_status": self.rights_licensing_status,
            "health_state": self.health_state,
            "fallback_eligible": self.fallback_eligible,
            "schema_version": REGISTRY_VERSION,
        }


_LAUNCH57_CONNECTOR_SOURCES: tuple[tuple[str, SourceRole, tuple[int, ...]], ...] = (
    ("binance", SourceRole.PRIMARY, (21, 22, 23, 24, 42, 43)),
    ("kraken", SourceRole.FALLBACK, (21, 22, 42)),
    ("okx", SourceRole.FALLBACK, (21, 22, 42)),
    ("bybit", SourceRole.FALLBACK, (21, 22, 42)),
    ("coingecko", SourceRole.VALIDATION, (21, 22, 24, 38, 42)),
    ("coinbase", SourceRole.FALLBACK, (21, 22, 42)),
)

_SOURCE_METADATA: dict[str, dict[str, str]] = {
    "binance": {
        "source_type": "cex_rest",
        "domain": "spot_prices",
        "endpoint_feed": "api.binance.com / data-api.binance.vision / api.binance.us",
        "authentication_model": "public_rest",
        "public_private": "public",
        "expected_cadence": "sub_second_to_seconds",
        "coverage": "major_usdt_pairs",
        "rate_quota_limits": "provider_default",
        "historical_availability": "rest_backfill",
        "rights_licensing_status": "public_feed_review_required",
    },
    "kraken": {
        "source_type": "cex_rest",
        "domain": "spot_prices",
        "endpoint_feed": "api.kraken.com",
        "authentication_model": "public_rest",
        "public_private": "public",
        "expected_cadence": "seconds",
        "coverage": "major_pairs",
        "rate_quota_limits": "provider_default",
        "historical_availability": "rest_backfill",
        "rights_licensing_status": "public_feed_review_required",
    },
    "okx": {
        "source_type": "cex_rest",
        "domain": "spot_prices",
        "endpoint_feed": "www.okx.com",
        "authentication_model": "public_rest",
        "public_private": "public",
        "expected_cadence": "seconds",
        "coverage": "major_pairs",
        "rate_quota_limits": "provider_default",
        "historical_availability": "rest_backfill",
        "rights_licensing_status": "public_feed_review_required",
    },
    "bybit": {
        "source_type": "cex_rest",
        "domain": "spot_prices",
        "endpoint_feed": "api.bybit.com",
        "authentication_model": "public_rest",
        "public_private": "public",
        "expected_cadence": "seconds",
        "coverage": "major_pairs",
        "rate_quota_limits": "provider_default",
        "historical_availability": "rest_backfill",
        "rights_licensing_status": "public_feed_review_required",
    },
    "coingecko": {
        "source_type": "aggregator_rest",
        "domain": "reference_prices",
        "endpoint_feed": "api.coingecko.com",
        "authentication_model": "public_rest",
        "public_private": "public",
        "expected_cadence": "minutes",
        "coverage": "broad_discovery",
        "rate_quota_limits": "free_tier_quota",
        "historical_availability": "limited_free_history",
        "rights_licensing_status": "validation_only_not_execution_grade",
    },
    "coinbase": {
        "source_type": "cex_rest",
        "domain": "spot_prices",
        "endpoint_feed": "api.coinbase.com",
        "authentication_model": "public_rest",
        "public_private": "public",
        "expected_cadence": "seconds",
        "coverage": "major_pairs",
        "rate_quota_limits": "provider_default",
        "historical_availability": "rest_backfill",
        "rights_licensing_status": "public_feed_review_required",
    },
}

_CAPABILITY_RUNTIME_OWNERS: dict[int, dict[str, str]] = {
    21: {"module": "launch57.data_batch1", "entrypoint": "spot_market_metrics_suite"},
    22: {"module": "launch57.data_batch1", "entrypoint": "real_time_prices"},
    23: {"module": "launch57.data_batch1", "entrypoint": "ohlcv"},
    24: {"module": "launch57.data_batch1", "entrypoint": "quote_data|symbol_metadata"},
    25: {"module": "launch57.derivatives_batch1", "entrypoint": "futures_open_interest_intelligence"},
    26: {"module": "launch57.derivatives_batch1", "entrypoint": "funding_rate_intelligence"},
    27: {"module": "launch57.derivatives_batch1", "entrypoint": "liquidation_intelligence"},
    28: {"module": "launch57.derivatives_batch1", "entrypoint": "taker_buy_sell_pressure"},
    29: {"module": "launch57.derivatives_batch1", "entrypoint": "derivatives_sentiment_composite"},
    30: {"module": "launch57.derivatives_batch2", "entrypoint": "order_book_intelligence"},
    38: {"module": "launch57.edge_ui_batch1", "entrypoint": "mvrv_zscore_btc_eth"},
    39: {"module": "launch57.data_batch2", "entrypoint": "point_in_time_immutable_metrics"},
    40: {"module": "launch57.data_batch2", "entrypoint": "data_quality_provenance_layer"},
    41: {"module": "launch57.data_batch2", "entrypoint": "freshness_update_assurance"},
    42: {"module": "launch57.data_batch1", "entrypoint": "unified_exchange_connector"},
    43: {"module": "launch57.edge_ui_batch1", "entrypoint": "spot_perp_net_edge"},
    53: {"module": "launch57.smart_money_batch2", "entrypoint": "instant_wallet_due_diligence"},
    54: {"module": "launch57.smart_money_batch2", "entrypoint": "instant_token_due_diligence"},
    55: {"module": "launch57.smart_money_batch3", "entrypoint": "manipulation_pattern_alerts"},
    56: {"module": "launch57.smart_money_batch3", "entrypoint": "suspicious_activity_flags"},
    57: {"module": "launch57.smart_money_batch3", "entrypoint": "exchange_transparency_risk_indicators"},
}


def build_launch57_source_registry() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for provider, role, launch_items in _LAUNCH57_CONNECTOR_SOURCES:
        meta = _SOURCE_METADATA[provider]
        entry = Launch57SourceEntry(
            source_id=f"launch57:{provider}",
            provider=provider,
            source_role=role,
            source_type=meta["source_type"],
            domain=meta["domain"],
            supported_launch_items=launch_items,
            endpoint_feed=meta["endpoint_feed"],
            authentication_model=meta["authentication_model"],
            public_private=meta["public_private"],
            expected_cadence=meta["expected_cadence"],
            coverage=meta["coverage"],
            rate_quota_limits=meta["rate_quota_limits"],
            historical_availability=meta["historical_availability"],
            rights_licensing_status=meta["rights_licensing_status"],
            health_state="runtime_probed",
            fallback_eligible=role in {SourceRole.FALLBACK, SourceRole.VALIDATION},
        )
        entries.append(entry.as_dict())
    return entries


def connector_fetchers_from_registry() -> tuple[tuple[str, str], ...]:
    return tuple((e.provider, e.source_role.value.lower()) for e in (
        Launch57SourceEntry(
            source_id=f"launch57:{p}",
            provider=p,
            source_role=r,
            source_type=_SOURCE_METADATA[p]["source_type"],
            domain=_SOURCE_METADATA[p]["domain"],
            supported_launch_items=items,
            endpoint_feed=_SOURCE_METADATA[p]["endpoint_feed"],
            authentication_model=_SOURCE_METADATA[p]["authentication_model"],
            public_private=_SOURCE_METADATA[p]["public_private"],
            expected_cadence=_SOURCE_METADATA[p]["expected_cadence"],
            coverage=_SOURCE_METADATA[p]["coverage"],
            rate_quota_limits=_SOURCE_METADATA[p]["rate_quota_limits"],
            historical_availability=_SOURCE_METADATA[p]["historical_availability"],
            rights_licensing_status=_SOURCE_METADATA[p]["rights_licensing_status"],
            health_state="runtime_probed",
            fallback_eligible=r in {SourceRole.FALLBACK, SourceRole.VALIDATION},
        )
        for p, r, items in _LAUNCH57_CONNECTOR_SOURCES
    ))


def validate_observation_contract(observation: dict[str, Any]) -> dict[str, Any]:
    """RESTORE-003 / spec §5 — material observation contract gate."""
    required_any = (
        ("source", ("source", "source_id", "provider")),
        ("event_time", ("event_time", "source_time", "event_timestamp", "timestamp")),
        ("received_time", ("received_time", "observed_at", "observed_time")),
        ("freshness", ("freshness", "freshness_state", "data_age_sec")),
        ("quality", ("quality_score", "quality_state", "quality")),
    )
    missing: list[str] = []
    present: list[str] = []
    for label, keys in required_any:
        if any(observation.get(k) is not None for k in keys):
            present.append(label)
        else:
            missing.append(label)
    ok = len(missing) == 0
    return {
        "contract": "RESTORE-003_LAUNCH57_OBSERVATION",
        "ok": ok,
        "present_fields": present,
        "missing_fields": missing,
        "schema_version": REGISTRY_VERSION,
    }


def build_observation_contract(
    *,
    source: str | None,
    asset_id: str | None = None,
    instrument_id: str | None = None,
    venue: str | None = None,
    data_type: str | None = None,
    event_time: Any = None,
    observed_at: str | None = None,
    ingested_at: str | None = None,
    raw_value: Any = None,
    normalized_value: Any = None,
    unit: str | None = None,
    precision: int | None = None,
    freshness_state: str | None = None,
    quality_state: str | None = None,
    provenance_ref: str | None = None,
) -> dict[str, Any]:
    now = to_rfc3339(utc_now())
    observed = observed_at or now
    event = event_time if event_time is not None else observed
    obs = {
        "source_id": source,
        "provider": source,
        "asset_id": asset_id,
        "instrument_id": instrument_id,
        "venue": venue,
        "data_type": data_type,
        "event_time": event,
        "observed_at": observed,
        "ingested_at": ingested_at or now,
        "raw_value": raw_value,
        "normalized_value": normalized_value,
        "unit": unit,
        "precision": precision,
        "freshness_state": freshness_state,
        "quality_state": quality_state,
        "provenance_reference": provenance_ref,
        "schema_version": REGISTRY_VERSION,
    }
    gate = validate_observation_contract(obs)
    return {"observation": obs, "contract_gate": gate}


def reconcile_price_observations(
    observations: list[dict[str, Any]],
    *,
    threshold_pct: float = 1.0,
) -> dict[str, Any]:
    result = reconcile_observations(observations, threshold_pct=threshold_pct)
    state_map = {
        "CONFLICT": "CONFLICT",
        "CONSENSUS": "AGREED",
        "SINGLE_SOURCE": "INSUFFICIENT",
        "INSUFFICIENT": "UNAVAILABLE",
    }
    return {
        **result,
        "launch57_reconciliation_state": state_map.get(result.get("state", ""), result.get("state")),
        "policy": "no_silent_average_on_conflict",
        "owner": "launch57.data_governance_common",
    }


def build_price_reconciliation_from_probe(
    *,
    primary_price: float | None,
    primary_source: str | None,
    probe: dict[str, Any] | None,
) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    if primary_price is not None and primary_source:
        observations.append(
            {"source_id": primary_source, "value": float(primary_price), "role": "PRIMARY"}
        )
    resolved_price = (probe or {}).get("resolved_price")
    resolved_source = (probe or {}).get("resolved_source")
    if resolved_price is not None and resolved_source:
        if not primary_source or resolved_source != primary_source:
            observations.append(
                {"source_id": str(resolved_source), "value": float(resolved_price), "role": "VALIDATION"}
            )
        elif primary_price is None:
            observations.append(
                {"source_id": str(resolved_source), "value": float(resolved_price), "role": "PRIMARY"}
            )
    if not observations:
        return {
            "state": "UNAVAILABLE",
            "launch57_reconciliation_state": "UNAVAILABLE",
            "method": "no_observations",
            "policy": "no_silent_average_on_conflict",
            "owner": "launch57.data_governance_common",
        }
    return reconcile_price_observations(observations)


def attach_data_governance_envelope(body: dict[str, Any]) -> dict[str, Any]:
    out = dict(body)
    out["launch57_data_governance"] = {
        "registry_version": REGISTRY_VERSION,
        "scope": "LAUNCH57_IDS",
        "source_registry_authority": "launch57.data_governance_common",
        "reconciliation_authority": "data_governance.reconciliation via launch57.data_governance_common",
        "legacy_data_governance_parallel_path": False,
        "parked_out_of_launch": True,
    }
    return out


def attach_material_observation(
    body: dict[str, Any],
    *,
    source: str | None,
    asset_id: str | None = None,
    data_type: str | None = None,
    event_time: Any = None,
    raw_value: Any = None,
    normalized_value: Any = None,
    unit: str | None = None,
    precision: int | None = None,
    freshness_state: str | None = None,
    quality_state: str | None = None,
) -> dict[str, Any]:
    out = attach_data_governance_envelope(body)
    contract = build_observation_contract(
        source=source,
        asset_id=asset_id or out.get("symbol") or out.get("canonical_symbol"),
        instrument_id=out.get("pair"),
        venue=source,
        data_type=data_type or out.get("surface"),
        event_time=event_time or out.get("event_timestamp"),
        observed_at=(out.get("temporal") or {}).get("observed_time") or out.get("observed_at"),
        ingested_at=(out.get("temporal") or {}).get("ingested_at"),
        raw_value=raw_value,
        normalized_value=normalized_value,
        unit=unit or out.get("unit"),
        precision=precision if precision is not None else out.get("precision"),
        freshness_state=freshness_state or out.get("freshness_state") or "UNKNOWN",
        quality_state=quality_state
        or (out.get("provenance") or {}).get("quality_state")
        or ("decision_grade" if out.get("success") else "unknown"),
        provenance_ref=(out.get("provenance") or {}).get("lineage", [None])[0] if isinstance(out.get("provenance"), dict) else None,
    )
    out["material_observation_contract"] = contract
    return out


def build_capability_source_matrix() -> list[dict[str, Any]]:
    registry = build_launch57_source_registry()
    by_cap_sources: dict[int, list[str]] = {}
    for entry in registry:
        for cap_id in entry["supported_launch57_capabilities"]:
            by_cap_sources.setdefault(cap_id, []).append(entry["source_id"])

    rows: list[dict[str, Any]] = []
    for cap_id in sorted(LAUNCH57_DATA_CRITICAL_IDS):
        owner = _CAPABILITY_RUNTIME_OWNERS.get(cap_id, {})
        rows.append(
            {
                "launch_item_id": cap_id,
                "runtime_owner": owner.get("module"),
                "entrypoint": owner.get("entrypoint"),
                "active_sources": by_cap_sources.get(cap_id, []),
                "source_roles_documented": cap_id in by_cap_sources or cap_id in {39, 40, 41, 53, 54, 55, 56, 57},
                "launch57_only": True,
            }
        )
    return rows


def build_rights_cost_matrix() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in build_launch57_source_registry():
        rows.append(
            {
                "source_id": entry["source_id"],
                "provider": entry["provider"],
                "rights_licensing_status": entry["rights_licensing_status"],
                "rate_quota_limits": entry["rate_quota_limits"],
                "cost_class": "free_public" if entry["public_private"] == "public" else "paid_or_keyed",
                "redistribution_rights": "internal_analysis_default",
                "provider_sla": "NONE",
                "internal_slo_class": entry["expected_cadence"],
            }
        )
    return rows


def build_quality_freshness_reconciliation_summary() -> dict[str, Any]:
    return {
        "freshness_owner": "launch57.freshness_common (#41)",
        "quality_owner": "launch57.provenance_common (#40)",
        "pit_owner": "launch57.point_in_time_common (#39)",
        "reconciliation_owner": "launch57.data_governance_common",
        "b1_to_41_bridge": "launch57.b1_freshness_bridge",
        "stale_as_live_blocked": True,
        "conflict_quarantine_policy": "no_silent_average",
        "cross_source_reconciliation_wired": True,
        "anti_lookahead_owner": "launch57.temporal_common + launch57.point_in_time_common",
    }
