"""Market Time Machine experience layer (P5 / TEMP-AR-0251..0261)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, Sequence

from blackdark.temporal.event_store import TemporalCanonicalEventStore
from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.replay import ReplayRequest, ReplayResult, run_deterministic_mass_replay
from blackdark.temporal.truth import parse_temporal_instant

MARKET_TIME_MACHINE_CONTRACT_VERSION = "p5.market_time_machine.1.0"
MANDATORY_HISTORICAL_REPLAY_DISCLOSURE = "Historical Replay"
IMPLIED_LIVE_ISSUANCE_PROHIBITED = True


class MarketTimeMachineMode(str, Enum):
    INTERNAL = "internal"
    USER_FACING = "user_facing"


class InternalModePurpose(str, Enum):
    QA = "qa"
    DEBUGGING = "debugging"
    RESEARCH = "research"
    MODEL_COMPARISON = "model_comparison"
    REPLAY = "replay"
    FAILURE_REPRODUCTION = "failure_reproduction"
    EVIDENCE_GENERATION = "evidence_generation"
    ROOT_CAUSE_ANALYSIS = "root_cause_analysis"


INTERNAL_MODE_PURPOSES: frozenset[str] = frozenset(p.value for p in InternalModePurpose)


@dataclass(frozen=True, slots=True)
class MarketTimeMachineExperience:
    """Authoritative market_time_machine_experience_state."""

    experience_id: str
    mode: MarketTimeMachineMode
    selected_timestamp: datetime
    selected_entity_key: str | None
    internal_purpose: InternalModePurpose | None
    mandatory_disclosure: str
    evidence_class: str
    implies_live_issuance: bool
    forward_evidence_present: bool
    knowable_at_timestamp: Mapping[str, Any]
    replay_result: Mapping[str, Any]
    accessibility: Mapping[str, Any]
    limitations: tuple[str, ...]
    provenance: Mapping[str, Any]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "experience_id": self.experience_id,
            "mode": self.mode.value,
            "selected_timestamp": self.selected_timestamp.isoformat(),
            "selected_entity_key": self.selected_entity_key,
            "internal_purpose": self.internal_purpose.value if self.internal_purpose else None,
            "mandatory_disclosure": self.mandatory_disclosure,
            "evidence_class": self.evidence_class,
            "implies_live_issuance": self.implies_live_issuance,
            "forward_evidence_present": self.forward_evidence_present,
            "knowable_at_timestamp": dict(self.knowable_at_timestamp),
            "replay_result": dict(self.replay_result),
            "accessibility": dict(self.accessibility),
            "limitations": list(self.limitations),
            "provenance": dict(self.provenance),
        }


def _accessibility_metadata() -> dict[str, Any]:
    return {
        "wcag_version": "2.2",
        "disclosure_visible": True,
        "disclosure_non_color_only": True,
        "keyboard_navigable": True,
        "screen_reader_label": MANDATORY_HISTORICAL_REPLAY_DISCLOSURE,
    }


def evaluate_live_issuance_claim(
    *,
    evidence_class: str,
    forward_evidence_present: bool,
    uses_simulated_time: bool = True,
) -> dict[str, Any]:
    """TEMP-AR-0261: never imply live issuance without genuine forward evidence."""
    implies_live = False
    if evidence_class in {
        TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        TemporalEvidenceClass.HISTORICAL_BACKTEST.value,
        TemporalEvidenceClass.SIMULATED.value,
    }:
        implies_live = False
    elif evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value:
        implies_live = forward_evidence_present and not uses_simulated_time
    elif evidence_class in {
        TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
        TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value,
    }:
        implies_live = forward_evidence_present

    external_gate_pending = (
        evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value
        and not forward_evidence_present
    )
    return {
        "implies_live_issuance": implies_live,
        "forward_evidence_present": forward_evidence_present,
        "external_runtime_gate_pending": external_gate_pending,
        "local_engineering_complete": IMPLIED_LIVE_ISSUANCE_PROHIBITED,
    }


def run_market_time_machine_replay(
    *,
    event_source: TemporalCanonicalEventStore,
    selected_timestamp: datetime | str,
    start_time: datetime | str,
    end_time: datetime | str,
    entity_key: str | None = None,
) -> ReplayResult:
    ts = parse_temporal_instant(selected_timestamp)
    return run_deterministic_mass_replay(
        ReplayRequest(
            event_source=event_source,
            start_time=start_time,
            end_time=end_time,
            replay_clock_or_schedule=(ts,),
            strict_mode=True,
            replay_parameters={"entity_key": entity_key} if entity_key else {},
        )
    )


def build_internal_experience(
    *,
    experience_id: str,
    purpose: InternalModePurpose,
    selected_timestamp: datetime | str,
    replay: ReplayResult,
    entity_key: str | None = None,
) -> MarketTimeMachineExperience:
    ts = parse_temporal_instant(selected_timestamp)
    issuance = evaluate_live_issuance_claim(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        forward_evidence_present=False,
        uses_simulated_time=True,
    )
    return MarketTimeMachineExperience(
        experience_id=experience_id,
        mode=MarketTimeMachineMode.INTERNAL,
        selected_timestamp=ts,
        selected_entity_key=entity_key,
        internal_purpose=purpose,
        mandatory_disclosure=MANDATORY_HISTORICAL_REPLAY_DISCLOSURE,
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        implies_live_issuance=issuance["implies_live_issuance"],
        forward_evidence_present=False,
        knowable_at_timestamp={
            "pit_accessible_records": replay.admitted_event_count,
            "rejected_records": replay.rejected_event_count,
        },
        replay_result=replay.to_metadata(),
        accessibility=_accessibility_metadata(),
        limitations=(
            "Internal mode only — not user-facing production output.",
            "Historical replay does not prove live issuance.",
        ),
        provenance={
            "contract_version": MARKET_TIME_MACHINE_CONTRACT_VERSION,
            "purpose": purpose.value,
            "replay_id": replay.replay_id,
        },
    )


def build_user_facing_experience(
    *,
    experience_id: str,
    selected_timestamp: datetime | str,
    replay: ReplayResult,
    entity_key: str | None = None,
    forward_evidence_present: bool = False,
) -> MarketTimeMachineExperience:
    """TEMP-AR-0259..0261 user-facing historical selection with mandatory disclosure."""
    ts = parse_temporal_instant(selected_timestamp)
    issuance = evaluate_live_issuance_claim(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        forward_evidence_present=forward_evidence_present,
        uses_simulated_time=True,
    )
    return MarketTimeMachineExperience(
        experience_id=experience_id,
        mode=MarketTimeMachineMode.USER_FACING,
        selected_timestamp=ts,
        selected_entity_key=entity_key,
        internal_purpose=None,
        mandatory_disclosure=MANDATORY_HISTORICAL_REPLAY_DISCLOSURE,
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        implies_live_issuance=issuance["implies_live_issuance"],
        forward_evidence_present=forward_evidence_present,
        knowable_at_timestamp={
            "selected_timestamp": ts.isoformat(),
            "entity_key": entity_key,
            "pit_accessible_records": replay.admitted_event_count,
            "rejected_records": replay.rejected_event_count,
        },
        replay_result=replay.to_metadata(),
        accessibility=_accessibility_metadata(),
        limitations=(
            "User-facing historical replay — not live production issuance.",
            "What was knowable at the selected timestamp may exclude later revisions.",
        ),
        provenance={
            "contract_version": MARKET_TIME_MACHINE_CONTRACT_VERSION,
            "replay_id": replay.replay_id,
        },
    )


def supported_internal_purposes() -> tuple[str, ...]:
    return tuple(sorted(INTERNAL_MODE_PURPOSES))
