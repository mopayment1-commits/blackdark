"""
B5 → #4 targeted reconciliation bridge.

Binds trust_batch1 public_accuracy_ledger to launch57.public_accuracy_common.
"""

from __future__ import annotations

from typing import Any

from launch57.batch5_isolation import finalize_b5_response
from launch57.evidence_class_common import attach_evidence_class_metadata
from launch57.public_accuracy_common import enrich_public_track_record, snapshot_ledger_evidence_state
from launch57.trust_adaptive_common import attach_adaptive_disclosure, build_ledger_interpretation_context

B5_PUBLIC_ACCURACY_ACTIVATED: bool = True


def b5_public_accuracy_state() -> dict[str, Any]:
    return {
        "contract": "B5_PUBLIC_ACCURACY_RECONCILIATION",
        "activated": B5_PUBLIC_ACCURACY_ACTIVATED,
        "affected_launch_items": [4],
        "status": "PENDING_VERIFICATION" if B5_PUBLIC_ACCURACY_ACTIVATED else "PREPARED_NOT_ACTIVATED",
        "owner_module": "launch57/public_accuracy_common.py",
        "reopen_reason": "NONE",
    }


def apply_b5_trust_envelope(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    out = attach_evidence_class_metadata(dict(body), display_timezone=display_timezone)
    cls = out.get("evidence_class", "SHADOW_LIVE_FORWARD")
    out["compliance_footer"] = {
        "evidence_class": cls,
        "unknown_is_not_zero": True,
        "legal": (
            "Public accuracy ledger only. Not financial advice. "
            f"Evidence class={cls}. Synthetic rows excluded from live-primary metrics."
        ),
    }
    out["b5_public_accuracy"] = b5_public_accuracy_state()
    return finalize_b5_response(out)


def finalize_b5_ledger_surface(
    body: dict[str, Any],
    *,
    display_timezone: str | None = None,
) -> dict[str, Any]:
    """Enrich ledger with SPEC §14 timing; preserve canonical order under display TZ."""
    if not B5_PUBLIC_ACCURACY_ACTIVATED:
        return apply_b5_trust_envelope(body, display_timezone=display_timezone)

    zone = str(display_timezone or body.get("display_timezone") or "UTC")
    ledger = body.get("ledger") or body.get("public_accuracy_ledger") or {}
    enriched = enrich_public_track_record(ledger, display_timezone=zone)
    evidence = snapshot_ledger_evidence_state(body, display_timezone=zone)

    out = apply_b5_trust_envelope(body, display_timezone=zone)
    out["ledger"] = enriched
    out["public_accuracy_ledger"] = enriched
    out["metrics_scope"] = enriched.get("metrics_scope") or "live_only"
    out["live_only_primary"] = enriched.get("live_only_primary", True)
    out["synthetic_excluded_from_primary"] = bool(
        (enriched.get("synthetic_demo_data") or {}).get("excluded_from_primary_metrics", True)
    )
    out["ledger_evidence_state"] = evidence.to_payload()
    interpretation = build_ledger_interpretation_context(enriched)
    out["ledger_interpretation_context"] = interpretation
    out = attach_adaptive_disclosure(
        out,
        {
            "layer": "level_1_decision",
            "launch_item_id": 4,
            "surface": "public_accuracy_ledger",
            "answer_state": "LIVE_PRIMARY_LEDGER",
            "evidence_class": evidence.user_facing_label,
            "critical_limitation": {
                "summary": "Public ledger excludes replay/simulation from primary live metrics.",
            },
            "safety_floor_visible": True,
            "methodology_version": interpretation["methodology_version"],
        },
        extra={"ledger_interpretation_context": interpretation},
    )
    from launch57.compounding_evidence_common import attach_compounding_evidence_envelope

    out["b5_public_accuracy"] = b5_public_accuracy_state()
    out = attach_compounding_evidence_envelope(out, launch_item_id=4)
    return finalize_b5_response(out)
