"""
Launch-57 canonical public-accuracy ledger timing owner for B5 (#4).

Zero legacy/PARKED runtime dependencies on cap646 or decision_certificate.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from launch57.evidence_class_common import EvidenceClassAssessment, assess_user_evidence_class
from launch57.temporal_common import local_render_instant, parse_rfc3339, to_rfc3339

METHODOLOGY_VERSION = "launch57-public-accuracy-common-1.0"
DEFAULT_EVALUATION_WINDOW_HOURS = 24


@dataclass(frozen=True)
class LedgerEntryTiming:
    prediction_id: int
    decision_time: str
    outcome_time: str | None
    evaluation_window: dict[str, Any]
    evidence_class: str
    user_facing_evidence_label: str
    live_only_eligible: bool
    display_timezone: str
    local_render_decision_time: str | None = None
    local_render_outcome_time: str | None = None
    canonical_order_key: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "decision_time": self.decision_time,
            "outcome_time": self.outcome_time,
            "evaluation_window": self.evaluation_window,
            "canonical_evidence_class": self.evidence_class,
            "user_facing_evidence_label": self.user_facing_evidence_label,
            "live_only_eligible": self.live_only_eligible,
            "display_timezone": self.display_timezone,
            "local_render_decision_time": self.local_render_decision_time,
            "local_render_outcome_time": self.local_render_outcome_time,
            "canonical_order_key": self.canonical_order_key,
            "methodology_version": METHODOLOGY_VERSION,
        }


def _parse_instant(value: Any) -> str | None:
    if value is None or value == "":
        return None
    return to_rfc3339(parse_rfc3339(str(value)))


def _is_live_eligible(record: dict[str, Any]) -> bool:
    try:
        from oracle_integrity import is_synthetic_prediction

        if is_synthetic_prediction(record):
            return False
    except ImportError:
        if record.get("synthetic"):
            return False
    evidence = assess_user_evidence_class(record)
    return evidence.user_facing_label != "SIM"


def _build_evaluation_window(decision_time: str, outcome_time: str | None) -> dict[str, Any]:
    window = {
        "start": decision_time,
        "end": outcome_time,
        "duration_hours": DEFAULT_EVALUATION_WINDOW_HOURS,
        "status": "closed" if outcome_time else "open",
    }
    if outcome_time:
        start = parse_rfc3339(decision_time)
        end = parse_rfc3339(outcome_time)
        window["duration_seconds"] = max(0, int((end - start).total_seconds()))
    return window


def _merge_chain_records(records: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    merged: dict[int, dict[str, Any]] = {}
    for record in records:
        pid = record.get("prediction_id")
        if pid is None:
            continue
        slot = merged.setdefault(int(pid), {"prediction_id": int(pid), "source": record.get("source")})
        event = str(record.get("event") or "")
        if event == "prediction_created" or record.get("resolved") is False:
            slot["decision_time"] = _parse_instant(record.get("decision_time") or record.get("timestamp"))
            slot["created_chain_seq"] = record.get("seq")
            slot.update({k: record.get(k) for k in ("asset", "verdict", "source", "chain_hash") if record.get(k) is not None})
        if event == "prediction_resolved" or record.get("resolved") is True:
            slot["outcome_time"] = _parse_instant(record.get("outcome_time") or record.get("timestamp"))
            if not slot.get("decision_time"):
                slot["decision_time"] = _parse_instant(record.get("decision_time"))
            slot["resolved_chain_seq"] = record.get("seq")
            slot.update(
                {
                    k: record.get(k)
                    for k in ("label", "outcome", "accuracy_score", "price_after_24h", "chain_hash")
                    if record.get(k) is not None
                }
            )
        slot.setdefault("chain_seq", record.get("seq"))
    return merged


def _canonical_order_key(decision_time: str, prediction_id: int, chain_seq: int | None) -> str:
    return f"{decision_time}|{int(chain_seq or 0):010d}|{int(prediction_id):010d}"


def build_ledger_entry_timing(
    record: dict[str, Any],
    *,
    display_timezone: str = "UTC",
) -> LedgerEntryTiming | None:
    decision_time = _parse_instant(record.get("decision_time"))
    if decision_time is None:
        return None
    outcome_time = _parse_instant(record.get("outcome_time"))
    evidence = assess_user_evidence_class(record, display_timezone=display_timezone)
    live_eligible = _is_live_eligible(record)
    zone = str(display_timezone or "UTC")
    return LedgerEntryTiming(
        prediction_id=int(record["prediction_id"]),
        decision_time=decision_time,
        outcome_time=outcome_time,
        evaluation_window=_build_evaluation_window(decision_time, outcome_time),
        evidence_class=evidence.canonical_evidence_class,
        user_facing_evidence_label=evidence.user_facing_label,
        live_only_eligible=live_eligible,
        display_timezone=zone,
        local_render_decision_time=local_render_instant(parse_rfc3339(decision_time), zone),
        local_render_outcome_time=local_render_instant(parse_rfc3339(outcome_time), zone) if outcome_time else None,
        canonical_order_key=_canonical_order_key(decision_time, int(record["prediction_id"]), record.get("chain_seq")),
    )


def sort_canonical_ledger_order(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Canonical ledger order is UTC decision_time order; display timezone must not reorder."""
    return sorted(entries, key=lambda row: row.get("canonical_order_key") or row.get("decision_time") or "")


def enrich_ledger_records(
    records: list[dict[str, Any]],
    *,
    display_timezone: str = "UTC",
    live_primary_only: bool = False,
) -> list[dict[str, Any]]:
    merged = _merge_chain_records(records)
    enriched: list[dict[str, Any]] = []
    for slot in merged.values():
        timing = build_ledger_entry_timing(slot, display_timezone=display_timezone)
        if timing is None:
            continue
        if live_primary_only and not timing.live_only_eligible:
            continue
        row = dict(slot)
        row["ledger_timing"] = timing.as_dict()
        row["decision_time"] = timing.decision_time
        row["outcome_time"] = timing.outcome_time
        row["evaluation_window"] = timing.evaluation_window
        row["canonical_evidence_class"] = timing.evidence_class
        row["user_facing_evidence_label"] = timing.user_facing_evidence_label
        row["live_only_eligible"] = timing.live_only_eligible
        row["canonical_order_key"] = timing.canonical_order_key
        enriched.append(row)
    return sort_canonical_ledger_order(enriched)


def enrich_public_track_record(
    ledger: dict[str, Any],
    *,
    display_timezone: str = "UTC",
) -> dict[str, Any]:
    """Attach SPEC §14 temporal fields to public accuracy ledger without mutating canonical order."""
    recent_raw = list(ledger.get("recent") or [])
    all_records = list(recent_raw)
    live_recent = enrich_ledger_records(all_records, display_timezone=display_timezone, live_primary_only=True)
    full_recent = enrich_ledger_records(all_records, display_timezone=display_timezone, live_primary_only=False)

    out = dict(ledger)
    out["recent"] = live_recent
    out["recent_all"] = full_recent
    out["ledger_timing"] = {
        "methodology_version": METHODOLOGY_VERSION,
        "display_timezone": display_timezone,
        "canonical_order_invariant": True,
        "live_primary_count": len(live_recent),
        "total_recent_count": len(full_recent),
        "evaluation_window_hours_default": DEFAULT_EVALUATION_WINDOW_HOURS,
    }
    out["live_only_primary"] = True
    out["metrics_scope"] = (ledger.get("cumulative") or {}).get("metrics_scope") or "live_only"
    return out


def snapshot_ledger_evidence_state(payload: dict[str, Any], *, display_timezone: str | None = None) -> EvidenceClassAssessment:
    return assess_user_evidence_class(payload, display_timezone=display_timezone)
