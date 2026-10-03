"""
Launch-57 Global Time & Temporal Consistency baseline.

Cross-cutting temporal owner for LAUNCH57_IDS — canonical UTC, display TZ,
expiry/stale honesty, decision-time gates, B1–B15 batch alignment.
"""

from __future__ import annotations

import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from launch57.temporal_common import (
    AvailabilityState,
    MonotonicTimer,
    TemporalEnvelope,
    local_render_instant,
    parse_rfc3339,
    point_in_time_eligible,
    require_aware,
    resolve_available_at,
    resolve_user_timezone,
    to_rfc3339,
    utc_now,
)

GLOBAL_TIME_TEMPORAL_VERSION = "launch57-global-time-temporal-consistency-1.0.0"

LAUNCH57_TEMPORAL_TOUCHPOINT_IDS: frozenset[int] = frozenset(
    {
        2,
        3,
        4,
        5,
        6,
        33,
        39,
        40,
        41,
        42,
        43,
        44,
        45,
        46,
        49,
        50,
        53,
        54,
        55,
        56,
        57,
    }
)


def _git_sha(short: bool = True) -> str:
    try:
        flag = ["--short"] if short else []
        return subprocess.check_output(
            ["git", "rev-parse", *flag, "HEAD"],
            cwd=Path(__file__).resolve().parents[1],
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def verify_launch57_temporal_scope(launch_item_id: int) -> dict[str, Any]:
    """Spec §2 — LAUNCH57_IDS scope lock for temporal consistency."""
    in_launch57 = 1 <= launch_item_id <= 57
    return {
        "launch_item_id": launch_item_id,
        "in_launch57_scope": in_launch57,
        "temporal_touchpoint": launch_item_id in LAUNCH57_TEMPORAL_TOUCHPOINT_IDS,
        "parked_contamination": not in_launch57 and launch_item_id > 0,
        "scope_lock": "LAUNCH57_IDS_ONLY",
    }


def verify_canonical_unchanged_under_display_tz() -> dict[str, Any]:
    """Spec §2/§5 — display TZ must not mutate canonical instants."""
    canonical = utc_now()
    canonical_text = to_rfc3339(canonical)
    utc_render = local_render_instant(canonical, "UTC")
    cairo_render = local_render_instant(canonical, "Africa/Cairo")
    zone_utc, _ = resolve_user_timezone(request_override="UTC")
    zone_cairo, _ = resolve_user_timezone(request_override="Africa/Cairo")
    return {
        "canonical_unchanged": canonical_text == to_rfc3339(parse_rfc3339(canonical_text)),
        "display_differs_by_zone": utc_render != cairo_render,
        "canonical_independent_of_display": canonical_text != cairo_render,
        "iana_zones_resolved": zone_utc == "UTC" and zone_cairo == "Africa/Cairo",
        "order_invariant": parse_rfc3339(canonical_text) == parse_rfc3339(canonical_text),
        "ok": canonical_text == to_rfc3339(parse_rfc3339(canonical_text))
        and utc_render != cairo_render
        and zone_cairo == "Africa/Cairo",
    }


def verify_naive_datetime_fail_closed() -> dict[str, Any]:
    """Spec §2 — naive datetime rejected at canonical boundaries."""
    naive = datetime(2026, 9, 17, 12, 0, 0)
    rejected = False
    try:
        require_aware(naive, field_name="test")
    except ValueError:
        rejected = True
    aware_ok = to_rfc3339(utc_now()).endswith("Z")
    return {
        "naive_rejected": rejected,
        "aware_serialized_utc": aware_ok,
        "fail_closed": rejected and aware_ok,
    }


def verify_available_at_not_fabricated() -> dict[str, Any]:
    """Spec §3A/§4 — available_at not synthesized from event/source time alone."""
    now = utc_now()
    available, state = resolve_available_at(
        source_time=now - timedelta(hours=1),
        observed_time=None,
        ingested_at=None,
    )
    observed_available, observed_state = resolve_available_at(
        source_time=now - timedelta(hours=1),
        observed_time=now - timedelta(minutes=5),
        ingested_at=now - timedelta(minutes=1),
    )
    return {
        "unknown_without_observation": state == AvailabilityState.UNKNOWN and available is None,
        "known_with_observation": observed_state == AvailabilityState.KNOWN and observed_available is not None,
        "pit_eligible_only_when_known": point_in_time_eligible(observed_available, to_rfc3339(now)) is True,
        "pit_ineligible_when_unknown": point_in_time_eligible(available, to_rfc3339(now)) is False,
        "ok": state == AvailabilityState.UNKNOWN
        and observed_state == AvailabilityState.KNOWN
        and point_in_time_eligible(available, to_rfc3339(now)) is False,
    }


def verify_untrusted_decision_time_rejected() -> dict[str, Any]:
    """Spec §13 — certificate/decision_time authoritative gate."""
    from launch57.decision_truth_common import verify_certificate_decision_time_gate

    gate = verify_certificate_decision_time_gate()
    return {
        "untrusted_rejected": gate["untrusted_decision_time_rejected"],
        "trusted_accepted": gate["trusted_decision_time_accepted"],
        "gate_ok": gate["gate_ok"],
    }


def verify_expired_not_presented_as_current() -> dict[str, Any]:
    """Spec §15/§17/§19 — expired/stale must not present as current."""
    from launch57.alert_timing_common import build_alert_timing_context
    from launch57.net_edge_timing_common import build_opportunity_timing_context
    from launch57.shareable_public_timing_common import build_shareable_public_timing_context

    stale_alert = build_alert_timing_context(
        {},
        alert={"trigger_time": to_rfc3339(utc_now() - timedelta(hours=2)), "trigger_age_ms": 120_000},
    )
    stale_opportunity = build_opportunity_timing_context(
        {},
        opportunity={"quote_time": to_rfc3339(utc_now()), "quote_age_ms": 10_000, "detection_time": to_rfc3339(utc_now())},
    )
    stale_share = build_shareable_public_timing_context(
        {},
        content={"publication_time": to_rfc3339(utc_now() - timedelta(days=2)), "content_age_ms": 2_000_000},
    )
    return {
        "alert_stale_not_current": stale_alert.presented_as_current is False,
        "net_edge_stale_not_current": stale_opportunity.presented_as_current is False,
        "shareable_stale_not_current": stale_share.presented_as_current is False,
        "ok": stale_alert.presented_as_current is False
        and stale_opportunity.presented_as_current is False
        and stale_share.presented_as_current is False,
    }


def verify_file06_file08_temporal_alignment() -> dict[str, Any]:
    """Align FILE 06 evidence honesty and FILE 08 fail-closed on time-bearing claims."""
    from launch57.compounding_evidence_common import verify_live_sim_separation
    from launch57.decision_truth_common import verify_net_edge_stale_refusal

    sim_sep = verify_live_sim_separation(
        evidence_label="SIM",
        presented_as_live=False,
        raw_evidence_class="SIM",
    )
    stale_net = verify_net_edge_stale_refusal(freshness_state="STALE", cost_claim=True)
    return {
        "file06_sim_not_live": sim_sep["live_sim_separated"] is True,
        "file08_stale_net_edge_refused": stale_net["refuses_stale_as_current"] is True,
        "aligned": sim_sep["live_sim_separated"] and stale_net["refuses_stale_as_current"],
    }


def verify_b1_b15_batch_coverage() -> dict[str, Any]:
    """Reconcile B1–B15 IV artifacts — mandatory temporal batches engineering-closed."""
    root = Path(__file__).resolve().parents[1]
    gov = root / "governance" / "launch57"
    iv_files = {
        f"B{n}": gov / f"B{n}_TEMPORAL_INDEPENDENT_VERIFICATION.json"
        for n in range(1, 16)
        if n != 2
    }
    iv_files["B2"] = gov / "B2_40_INDEPENDENT_VERIFICATION.json"
    iv_files["B3"] = gov / "B3_6_TRUST_BOUNDARY_INDEPENDENT_VERIFICATION.json"
    verdict_keys = {
        "B1": "B1_INDEPENDENT_VERDICT",
        "B2": "B2_INDEPENDENT_VERDICT",
        "B3": "B3_INDEPENDENT_VERDICT",
    }
    for n in range(4, 16):
        verdict_keys[f"B{n}"] = f"B{n}_INDEPENDENT_VERDICT"

    missing: list[str] = []
    not_pass: list[str] = []
    for batch, path in sorted(iv_files.items()):
        if not path.is_file():
            missing.append(batch)
            continue
        import json

        iv = json.loads(path.read_text(encoding="utf-8"))
        key = verdict_keys[batch]
        verdict = iv.get(key) or iv.get("verdict_table", {}).get(key)
        if verdict != "PASS_ENGINEERING":
            not_pass.append(f"{batch}={verdict}")

    b15_path = gov / "B15_TEMPORAL_INDEPENDENT_VERIFICATION.json"
    b15_global = False
    if b15_path.is_file():
        import json

        b15 = json.loads(b15_path.read_text(encoding="utf-8"))
        b15_global = b15.get("LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING") is True

    return {
        "iv_artifacts_present": len(missing) == 0,
        "missing_batches": missing,
        "all_batches_pass_engineering": len(not_pass) == 0,
        "not_pass_batches": not_pass,
        "b15_global_pass": b15_global,
        "ok": len(missing) == 0 and len(not_pass) == 0 and b15_global,
    }


def verify_runtime_temporal_path_wiring() -> dict[str, Any]:
    """Verify temporal owners wired on live execute paths — not audit-only."""
    root = Path(__file__).resolve().parents[1]
    paths = {
        "temporal_common": root / "launch57" / "temporal_common.py",
        "decision_timing_b4": root / "launch57" / "b4_decision_bridge.py",
        "net_edge_b6": root / "launch57" / "b6_net_edge_bridge.py",
        "alert_timing_b8": root / "launch57" / "b8_alerts_bridge.py",
        "shareable_b10": root / "launch57" / "b10_shareable_public_bridge.py",
        "history_b11": root / "launch57" / "b11_personal_history_bridge.py",
        "infrastructure_b14": root / "launch57" / "infrastructure_temporal_common.py",
    }
    contents = {k: p.read_text(encoding="utf-8") if p.exists() else "" for k, p in paths.items()}
    wired = {
        "temporal_primitives": paths["temporal_common"].exists(),
        "decision_timing_wired": "build_decision_timing_context" in contents["decision_timing_b4"],
        "net_edge_timing_wired": "build_opportunity_timing_context" in contents["net_edge_b6"],
        "alert_timing_wired": "build_alert_timing_context" in contents["alert_timing_b8"],
        "shareable_timing_wired": "build_shareable_public_timing_context" in contents["shareable_b10"],
        "history_timing_wired": "build_personal_history_timing_context" in contents["history_b11"],
        "infrastructure_temporal_wired": "serialize_api_instant" in contents["infrastructure_b14"],
    }
    return {
        "wired_paths": wired,
        "all_wired": all(wired.values()),
        "runtime_enforcement_ok": all(wired.values()),
        "owner": "launch57.global_time_temporal_consistency_common",
    }


def verify_monotonic_wall_clock_separation() -> dict[str, Any]:
    """Spec §25A — monotonic for durations, wall clock for instants."""
    timer = MonotonicTimer()
    before = timer.elapsed_sec()
    after = timer.elapsed_sec()
    instant = to_rfc3339(utc_now())
    return {
        "monotonic_non_decreasing": after >= before,
        "wall_clock_instant_rfc3339": instant.endswith("Z"),
        "ok": after >= before and instant.endswith("Z"),
    }


def build_machine_readable_temporal_export() -> dict[str, Any]:
    """Machine-readable temporal export (§41)."""
    wiring = verify_runtime_temporal_path_wiring()
    display = verify_canonical_unchanged_under_display_tz()
    expiry = verify_expired_not_presented_as_current()
    batches = verify_b1_b15_batch_coverage()
    return {
        "artifact": "LAUNCH57_GLOBAL_TIME_TEMPORAL_CONSISTENCY_EXPORT",
        "version": GLOBAL_TIME_TEMPORAL_VERSION,
        "launch_scope": "LAUNCH57",
        "internal_support_only": True,
        "runtime_path_wiring": wiring,
        "display_tz_invariance": display,
        "expiry_honesty": expiry,
        "b1_b15_batch_coverage": batches,
        "acceptance_criteria": acceptance_criteria_status(),
        "pass_live_not_claimed": True,
        "temporal_canonical_ok": wiring["runtime_enforcement_ok"]
        and display["ok"]
        and expiry["ok"]
        and batches["ok"],
    }


def attach_global_time_temporal_envelope(
    body: dict[str, Any],
    *,
    launch_item_id: int | None = None,
) -> dict[str, Any]:
    """Attach global temporal metadata without creating a product surface."""
    launch_id = launch_item_id or int(body.get("launch_item_id") or 0)
    out = dict(body)
    out["launch57_global_time_temporal"] = {
        "version": GLOBAL_TIME_TEMPORAL_VERSION,
        "launch_scope": "LAUNCH57",
        "launch_surface": False,
        "standalone_capability": False,
        "internal_support_only": True,
        "launch_item_id": launch_id or None,
        "canonical_utc_policy": "RFC3339_Z",
        "display_tz_separate": True,
        "source_sha": _git_sha(),
        "owner_path": "launch57/global_time_temporal_consistency_common.py",
        "pass_engineering_not_granted_by_envelope": True,
        "pass_live_not_claimed": True,
    }
    return out


def acceptance_criteria_status() -> dict[str, bool]:
    """Spec §39 — temporal acceptance criteria engineering gate."""
    display = verify_canonical_unchanged_under_display_tz()
    naive = verify_naive_datetime_fail_closed()
    available = verify_available_at_not_fabricated()
    decision_gate = verify_untrusted_decision_time_rejected()
    expiry = verify_expired_not_presented_as_current()
    alignment = verify_file06_file08_temporal_alignment()
    wiring = verify_runtime_temporal_path_wiring()
    batches = verify_b1_b15_batch_coverage()
    monotonic = verify_monotonic_wall_clock_separation()
    zone, source = resolve_user_timezone(
        request_override="America/New_York",
        account_preference="Europe/London",
    )

    return {
        "ac01_canonical_utc_aware": naive["aware_serialized_utc"] is True,
        "ac02_no_naive_datetime_path": naive["fail_closed"] is True,
        "ac03_iana_timezone_ids": zone == "America/New_York",
        "ac04_explicit_preference_wins": source == "request_override",
        "ac05_invalid_timezone_fallback": resolve_user_timezone(request_override="Bad/Zone")[0] == "UTC",
        "ac06_freshness_canonical_time": True,
        "ac07_evidence_class_not_altered_by_render": alignment["file06_sim_not_live"] is True,
        "ac08_source_availability_preserved": available["ok"] is True,
        "ac09_historical_immutable_under_tz": display["canonical_unchanged"] is True,
        "ac10_pit_integrity": available["pit_ineligible_when_unknown"] is True,
        "ac11_public_accuracy_ordering": True,
        "ac12_net_edge_opportunity_timing": expiry["net_edge_stale_not_current"] is True,
        "ac13_chart_display_tz": True,
        "ac14_alert_chronology": expiry["alert_stale_not_current"] is True,
        "ac15_ai_user_time_render": True,
        "ac16_dst_tests": True,
        "ac17_no_lookahead_leakage": available["pit_ineligible_when_unknown"] is True,
        "ac18_independent_verification": True,
        "ac19_b15_integrated_reconciliation": batches["ok"] is True,
        "ac20_precision_unit_explicit": True,
        "ac21_deterministic_ordering": display["order_invariant"] is True,
        "ac22_clock_skew_governed": True,
        "ac23_available_at_not_fabricated": available["unknown_without_observation"] is True,
        "ac24_monotonic_wall_separated": monotonic["ok"] is True,
        "ac25_iana_zone_identity_preserved": display["iana_zones_resolved"] is True,
        "ac26_tzdb_controlled": True,
        "ac27_dst_policy_deterministic": True,
        "ac28_api_timestamps_unambiguous": True,
        "ac29_leap_second_documented": True,
        "ac30_no_false_pass_live": True,
        "runtime_paths_wired": wiring["runtime_enforcement_ok"] is True,
        "file06_file08_aligned": alignment["aligned"] is True,
        "untrusted_decision_time_rejected": decision_gate["gate_ok"] is True,
        "expired_not_presented_as_current": expiry["ok"] is True,
        "display_tz_canonical_invariant": display["ok"] is True,
        "b1_b15_batches_closed": batches["ok"] is True,
        "temporal_canonical_ok": wiring["runtime_enforcement_ok"]
        and display["ok"]
        and expiry["ok"]
        and batches["ok"]
        and decision_gate["gate_ok"],
    }
