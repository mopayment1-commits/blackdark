"""
BLACKDARK — Acquirer Evidence Pack (Differentiator D6).

One-click institutional data-room payload for funds / M&A committees:
accuracy · audit chain · signal registry · net-edge rejects · half-life · moat.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


async def build_acquirer_evidence_pack() -> dict[str, Any]:
    pack: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product_thesis": (
            "Decision Intelligence + Proven Predictive Accuracy + "
            "Proprietary Labeled Market Corpus"
        ),
        "not_selling": "500-indicator dashboard / HFT theater",
        "sections": {},
        "committee_checklist": [],
    }

    # Public accuracy / track record
    try:
        from ml.public_accuracy import build_public_accuracy_payload

        pack["sections"]["public_accuracy"] = await build_public_accuracy_payload()
    except Exception as exc:
        pack["sections"]["public_accuracy"] = {"error": str(exc)}

    try:
        from oracle_track_record import public_track_record

        pack["sections"]["track_record"] = public_track_record()
    except Exception as exc:
        pack["sections"]["track_record"] = {"error": str(exc)}

    try:
        from oracle_audit_chain import chain_summary, verify_chain

        pack["sections"]["audit_chain"] = {
            "summary": chain_summary(limit=10),
            "verify": verify_chain(),
        }
    except Exception as exc:
        pack["sections"]["audit_chain"] = {"error": str(exc)}

    try:
        from signal_registry import registry_stats

        pack["sections"]["signal_registry"] = registry_stats()
    except Exception as exc:
        pack["sections"]["signal_registry"] = {"error": str(exc)}

    try:
        from net_edge_truth import net_edge_truth_status

        pack["sections"]["net_edge_truth"] = net_edge_truth_status()
    except Exception as exc:
        pack["sections"]["net_edge_truth"] = {"error": str(exc)}

    try:
        from opportunity_tracker import half_life_status

        pack["sections"]["opportunity_half_life"] = half_life_status()
    except Exception as exc:
        pack["sections"]["opportunity_half_life"] = {"error": str(exc)}

    try:
        from dimension_conflict_guard import dimension_conflict_status

        pack["sections"]["contradiction_veto"] = dimension_conflict_status()
    except Exception as exc:
        pack["sections"]["contradiction_veto"] = {"error": str(exc)}

    try:
        from data_moat_guard import build_moat_build_status

        pack["sections"]["data_moat"] = await build_moat_build_status()
    except Exception as exc:
        pack["sections"]["data_moat"] = {"error": str(exc)}

    try:
        from acquisition_assets_service import build_acquisition_asset_audit

        pack["sections"]["acquisition_assets"] = await build_acquisition_asset_audit()
    except Exception as exc:
        pack["sections"]["acquisition_assets"] = {"error": str(exc)}

    try:
        from flywheel_saturation_guard import flywheel_saturation_status

        pack["sections"]["flywheel_saturation"] = flywheel_saturation_status()
    except Exception as exc:
        pack["sections"]["flywheel_saturation"] = {"error": str(exc)}

    pack["differentiators"] = [
        {"id": "D1", "name": "Proof-Native Oracle", "status": "live"},
        {"id": "D2", "name": "Contradiction Veto", "status": "live"},
        {"id": "D3", "name": "Net-Edge Truth Score", "status": "live"},
        {"id": "D4", "name": "Opportunity Half-Life", "status": "live"},
        {"id": "D5", "name": "Regime-Conditional Models", "status": "pending"},
        {"id": "D6", "name": "Acquirer Evidence Pack", "status": "live"},
        {"id": "D7", "name": "Persona Clarity (English-first)", "status": "live"},
        {"id": "D8", "name": "Sovereign Signal Registry", "status": "live"},
    ]
    try:
        from ml.regime_models import regime_model_registry

        d5 = regime_model_registry()
        pack["differentiators"][4] = {
            "id": "D5",
            "name": "Regime-Conditional Models",
            "status": d5.get("status") or d5.get("evidence_status") or "weights_live",
            "evidence_status": d5.get("evidence_status"),
            "artifacts_ready": d5.get("artifacts_ready"),
            "artifacts_expected": d5.get("artifacts_expected"),
            "note": d5.get("note"),
        }
    except Exception:
        pack["differentiators"][4] = {
            "id": "D5",
            "name": "Regime-Conditional Models",
            "status": "weights_live",
            "note": "Regime weights + confidence router live; registry unavailable",
        }
    try:
        from signal_registry import registry_stats

        d8 = registry_stats()
        pack["differentiators"][7] = {
            "id": "D8",
            "name": "Sovereign Signal Registry",
            "status": d8.get("status") or ("live" if (d8.get("labeled") or 0) > 0 else "pending_labels"),
            "labeled": d8.get("labeled"),
            "unlabeled": d8.get("unlabeled"),
            "linked_prediction_ids": d8.get("linked_prediction_ids"),
            "total_in_memory": d8.get("total_in_memory"),
            "by_label": d8.get("by_label"),
            "by_type_performance": d8.get("by_type_performance"),
        }
    except Exception:
        pass
    pack["constitution"] = "docs/PRODUCT_CONSTITUTION_AR.md"

    pack["committee_checklist"] = [
        "Verify audit chain integrity",
        "Inspect public accuracy sample size and hit-rate",
        "Confirm Net-Edge reject rate (quality over quantity)",
        "Review labeled Signal Registry growth (moat)",
        "Confirm contradiction veto is fail-closed on severe conflict",
        "Confirm half-life stats exist (time-edge product)",
        "Review data moat / acquisition asset audit",
    ]

    pack["one_liner_for_ic"] = (
        "We sell audited market decisions with a labeled corpus and executable "
        "net-edge truth — not indicator spam."
    )
    return pack
