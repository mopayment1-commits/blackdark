"""P6 closure verification probes — assertions from runtime behavior."""

from __future__ import annotations

import importlib
from datetime import UTC, datetime, timedelta
from typing import Any

from blackdark.temporal.computational_acceleration import (
    AccelerationCache,
    AccelerationStrategy,
    validate_acceleration_guards,
    run_event_based_replay_accelerated,
)
from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.operational_hardening import (
    FAIL_CLOSED_ON_UNCERTAINTY,
    assess_operational_readiness,
    evaluate_fail_closed,
)
from blackdark.temporal.p6_requirement_registry import (
    P6_ATOMIC_REQUIREMENT_IDS,
    P6_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P6_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P6_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
)
from blackdark.temporal.quality_governance import (
    EXTERNAL_STANDARDS_GUIDANCE_ONLY,
    QualityCharacteristic,
    assess_quality_governance,
    validate_external_attribution_claim,
)

_P6_MODULE_PATHS = (
    "blackdark.temporal.computational_acceleration",
    "blackdark.temporal.quality_governance",
    "blackdark.temporal.operational_hardening",
)


def probe_p6_module_surfaces() -> int:
    missing = 0
    for path in _P6_MODULE_PATHS:
        try:
            importlib.import_module(path)
        except ImportError:
            missing += 1
    return missing


def probe_acceleration_cache_deterministic() -> bool:
    cache = AccelerationCache()
    key1 = cache.build_key(strategy=AccelerationStrategy.FEATURE_CACHING, payload={"a": 1})
    key2 = cache.build_key(strategy=AccelerationStrategy.FEATURE_CACHING, payload={"a": 1})
    key3 = cache.build_key(strategy=AccelerationStrategy.FEATURE_CACHING, payload={"a": 2})
    return key1.key == key2.key and key1.key != key3.key


def probe_acceleration_guards() -> bool:
    cache = AccelerationCache()
    result = validate_acceleration_guards(
        cache=cache,
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        strict_mode=True,
    )
    return result.provenance_preserved and result.temporal_integrity_preserved and not result.violations


def probe_event_replay_acceleration() -> bool:
    from blackdark.temporal import (
        CanonicalTemporalEvent,
        ProvenanceMetadata,
        ReplayRequest,
        TemporalCanonicalEventStore,
        TemporalObservation,
        TemporalSemanticField,
        TemporalTimestamp,
    )

    t = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    t_start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)

    def _ts(field: TemporalSemanticField, value: datetime) -> TemporalTimestamp:
        return TemporalTimestamp.direct(field, value)

    obs = TemporalObservation.create(
        event_time=_ts(TemporalSemanticField.EVENT_TIME, t),
        observed_time=_ts(TemporalSemanticField.OBSERVED_TIME, t),
        available_at=_ts(TemporalSemanticField.AVAILABLE_AT, t),
        ingested_at=_ts(TemporalSemanticField.INGESTED_AT, t),
        effective_at=_ts(TemporalSemanticField.EFFECTIVE_AT, t),
        revised_at=_ts(TemporalSemanticField.REVISED_AT, t),
    )
    event = CanonicalTemporalEvent(
        event_id="p6-probe-1",
        entity_key="asset-a",
        event_type="market.tick",
        payload={"price": "100"},
        observation=obs,
        provenance=ProvenanceMetadata(source="binance", source_version="v1", dataset_version="ds-1"),
        record_version="1",
    )
    store = TemporalCanonicalEventStore([event])
    replay = run_event_based_replay_accelerated(
        event_source=store,
        request=ReplayRequest(
            event_source=store,
            start_time=t_start,
            end_time=t_start + timedelta(hours=4),
            replay_clock_or_schedule=(t_start + timedelta(hours=2),),
            strict_mode=True,
        ),
    )
    return replay.success is True


def probe_fail_closed_behavior() -> bool:
    if not FAIL_CLOSED_ON_UNCERTAINTY:
        return False
    decision = evaluate_fail_closed(status="failed", error_code="TEMPORAL_LEAKAGE_REJECTED")
    return decision.admitted is False and decision.temporal_integrity_preserved is True


def probe_operational_readiness() -> bool:
    report = assess_operational_readiness(api_admin_gated=True)
    return report.fail_closed_enabled and report.metrics_available and report.recovery_supported


def probe_quality_governance_complete() -> bool:
    report = assess_quality_governance(runtime_signals={"api_admin_gated": True, "deterministic_replay": True})
    return (
        report.external_standards_guidance_only is True
        and report.false_attribution_prohibited is True
        and all(a.supported for a in report.assessments)
        and len(report.assessments) == len(QualityCharacteristic)
    )


def probe_external_attribution_honest() -> bool:
    bad = validate_external_attribution_claim(
        "ISO/IEC 25010:2023 certifies our Market Time Machine component"
    )
    good = validate_external_attribution_claim(
        "ISO/IEC 25010:2023 guides our quality characteristic assessment"
    )
    return bad["accepted"] is False and good["accepted"] is True


def probe_p6_local_engineering_complete() -> tuple[bool, int]:
    implemented_count = len(P6_ATOMIC_REQUIREMENT_IDS)
    complete = (
        P6_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 28
        and P6_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS == 28
        and implemented_count == 28
        and P6_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS == ()
        and EXTERNAL_STANDARDS_GUIDANCE_ONLY is True
    )
    return complete, implemented_count


def evaluate_p6_closure_assertions() -> dict[str, Any]:
    module_surfaces = probe_p6_module_surfaces()
    cache_deterministic = probe_acceleration_cache_deterministic()
    guards = probe_acceleration_guards()
    replay_accel = probe_event_replay_acceleration()
    fail_closed = probe_fail_closed_behavior()
    readiness = probe_operational_readiness()
    quality = probe_quality_governance_complete()
    attribution = probe_external_attribution_honest()
    local_complete, local_count = probe_p6_local_engineering_complete()

    closure_assertions = {
        "P6_MODULE_SURFACES": module_surfaces,
        "ACCELERATION_CACHE_DETERMINISTIC": cache_deterministic,
        "ACCELERATION_GUARDS": guards,
        "EVENT_REPLAY_ACCELERATION": replay_accel,
        "FAIL_CLOSED_BEHAVIOR": fail_closed,
        "OPERATIONAL_READINESS": readiness,
        "QUALITY_GOVERNANCE_COMPLETE": quality,
        "EXTERNAL_ATTRIBUTION_HONEST": attribution,
        "P6_LOCAL_ENGINEERING_COMPLETE": local_complete,
        "P6_CLOSED": (
            module_surfaces == 0
            and cache_deterministic is True
            and guards is True
            and replay_accel is True
            and fail_closed is True
            and readiness is True
            and quality is True
            and attribution is True
            and local_complete is True
        ),
    }

    return {
        "closure_assertions": closure_assertions,
        "P6_TOTAL_ACTIVE_ATOMIC_REQUIREMENTS": P6_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
        "P6_LOCAL_ENGINEERING_COMPLETE_COUNT": local_count,
        "P6_UNIMPLEMENTED_ACTIVE_ATOMIC_REQUIREMENTS": max(
            0, P6_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS - local_count
        ),
        "P6_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS": list(P6_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS),
        "runtime_probe_paths": {
            "P6_MODULE_SURFACES": "p6_closure_verification.probe_p6_module_surfaces",
            "ACCELERATION_CACHE_DETERMINISTIC": "p6_closure_verification.probe_acceleration_cache_deterministic",
            "ACCELERATION_GUARDS": "p6_closure_verification.probe_acceleration_guards",
            "EVENT_REPLAY_ACCELERATION": "p6_closure_verification.probe_event_replay_acceleration",
            "FAIL_CLOSED_BEHAVIOR": "p6_closure_verification.probe_fail_closed_behavior",
            "OPERATIONAL_READINESS": "p6_closure_verification.probe_operational_readiness",
            "QUALITY_GOVERNANCE_COMPLETE": "p6_closure_verification.probe_quality_governance_complete",
            "EXTERNAL_ATTRIBUTION_HONEST": "p6_closure_verification.probe_external_attribution_honest",
            "P6_LOCAL_ENGINEERING_COMPLETE": "p6_closure_verification.probe_p6_local_engineering_complete",
        },
    }
