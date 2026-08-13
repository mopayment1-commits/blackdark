"""
BLACKDARK — Acquirer Evidence Pack (Differentiator D6).

One-click institutional data-room payload for funds / M&A committees:
accuracy · audit chain · signal registry · net-edge rejects · half-life · moat.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# Sonar S1192: duplicated string literals
STR_REGIME_CONDITIONAL_MODELS = 'Regime-Conditional Models'


async def _public_accuracy_section() -> dict[str, Any]:
    try:
        from ml.public_accuracy import build_public_accuracy_payload

        return await build_public_accuracy_payload()
    except Exception as exc:
        return {"error": str(exc)}


def _track_record_section() -> dict[str, Any]:
    try:
        from oracle_track_record import public_track_record

        return public_track_record()
    except Exception as exc:
        return {"error": str(exc)}


def _audit_chain_section() -> dict[str, Any]:
    try:
        from oracle_audit_chain import chain_summary, verify_chain

        return {
            "summary": chain_summary(limit=10),
            "verify": verify_chain(),
        }
    except Exception as exc:
        return {"error": str(exc)}


def _registry_section() -> dict[str, Any]:
    try:
        from signal_registry import registry_stats

        return registry_stats()
    except Exception as exc:
        return {"error": str(exc)}


def _net_edge_section() -> dict[str, Any]:
    try:
        from net_edge_truth import net_edge_truth_status

        return net_edge_truth_status()
    except Exception as exc:
        return {"error": str(exc)}


def _half_life_section() -> dict[str, Any]:
    try:
        from opportunity_tracker import half_life_status

        return half_life_status()
    except Exception as exc:
        return {"error": str(exc)}


def _conflict_section() -> dict[str, Any]:
    try:
        from dimension_conflict_guard import dimension_conflict_status

        return dimension_conflict_status()
    except Exception as exc:
        return {"error": str(exc)}


async def _data_moat_section() -> dict[str, Any]:
    try:
        from data_moat_guard import build_moat_build_status

        return await build_moat_build_status()
    except Exception as exc:
        return {"error": str(exc)}


async def _acquisition_assets_section() -> dict[str, Any]:
    try:
        from acquisition_assets_service import build_acquisition_asset_audit

        return await build_acquisition_asset_audit()
    except Exception as exc:
        return {"error": str(exc)}


def _flywheel_section() -> dict[str, Any]:
    try:
        from flywheel_saturation_guard import flywheel_saturation_status

        return flywheel_saturation_status()
    except Exception as exc:
        return {"error": str(exc)}


async def _corpus_passport_section() -> dict[str, Any]:
    try:
        from corpus_passport import build_corpus_passport

        return await build_corpus_passport()
    except Exception as exc:
        return {"error": str(exc)}


def _base_differentiators() -> list[dict[str, Any]]:
    return [
        {"id": "D1", "name": "Proof-Native Oracle", "status": "live"},
        {"id": "D2", "name": "Contradiction Veto", "status": "live"},
        {"id": "D3", "name": "Net-Edge Truth Score", "status": "live"},
        {"id": "D4", "name": "Opportunity Half-Life", "status": "live"},
        {"id": "D5", "name": STR_REGIME_CONDITIONAL_MODELS, "status": "pending"},
        {"id": "D6", "name": "Acquirer Evidence Pack", "status": "live"},
        {"id": "D7", "name": "Persona Clarity (English-first)", "status": "live"},
        {"id": "D8", "name": "Sovereign Signal Registry", "status": "live"},
    ]


def _refresh_regime_differentiator(differentiators: list[dict[str, Any]]) -> None:
    try:
        from ml.regime_models import regime_model_registry

        d5 = regime_model_registry()
        differentiators[4] = {
            "id": "D5",
            "name": STR_REGIME_CONDITIONAL_MODELS,
            "status": d5.get("status") or d5.get("evidence_status") or "weights_live",
            "evidence_status": d5.get("evidence_status"),
            "artifacts_ready": d5.get("artifacts_ready"),
            "artifacts_expected": d5.get("artifacts_expected"),
            "note": d5.get("note"),
        }
    except Exception:
        differentiators[4] = {
            "id": "D5",
            "name": STR_REGIME_CONDITIONAL_MODELS,
            "status": "weights_live",
            "note": "Regime weights + confidence router live; registry unavailable",
        }


def _refresh_registry_differentiator(differentiators: list[dict[str, Any]]) -> None:
    try:
        from signal_registry import registry_stats

        d8 = registry_stats()
        differentiators[7] = {
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


def _four_blockers_section() -> dict[str, Any]:
    """Embed frozen four-blocker evidence — never invents PASS/COMPLETE."""
    from pathlib import Path
    import json

    path = Path("docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json")
    if not path.is_file():
        return {
            "ok": False,
            "product_complete": False,
            "reason": "four_blockers_evidence_missing",
            "external_evidence_required": True,
        }
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "product_complete": False, "error": str(exc)[:200]}
    return {
        "ok": True,
        "product_complete": False,
        "institutional_verdict": "NOT_COMPLETE",
        "source": str(path),
        "proved_at": raw.get("proved_at"),
        "blocker_1_live_venue_fill": raw.get("blocker_1_live_venue_fill"),
        "blocker_2_jupiter_live_signature": raw.get("blocker_2_jupiter_live_signature"),
        "blocker_3_full_mesh_100": raw.get("blocker_3_full_mesh_100"),
        "blocker_4_cloud_multi_az_ha": raw.get("blocker_4_cloud_multi_az_ha"),
        "operator_decisions": raw.get("operator_decisions"),
        "integrity": raw.get("integrity"),
        "note": (
            "Binding: green tests ≠ COMPLETE. live_fill / Jupiter VC / Full Mesh "
            "L2 100% / cloud multi-AZ must not be claimed without observed evidence."
        ),
    }


async def build_acquirer_evidence_pack() -> dict[str, Any]:
    pack: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "product_thesis": (
            "Decision Intelligence + Proven Predictive Accuracy + "
            "Proprietary Labeled Market Corpus"
        ),
        "not_selling": "500-indicator dashboard / HFT theater",
        "sections": {},
        "committee_checklist": [],
    }

    sections = pack["sections"]
    sections["public_accuracy"] = await _public_accuracy_section()
    sections["track_record"] = _track_record_section()
    sections["audit_chain"] = _audit_chain_section()
    sections["signal_registry"] = _registry_section()
    sections["net_edge_truth"] = _net_edge_section()
    sections["opportunity_half_life"] = _half_life_section()
    sections["contradiction_veto"] = _conflict_section()
    sections["data_moat"] = await _data_moat_section()
    sections["acquisition_assets"] = await _acquisition_assets_section()
    sections["flywheel_saturation"] = _flywheel_section()

    pack["differentiators"] = _base_differentiators()
    _refresh_regime_differentiator(pack["differentiators"])
    _refresh_registry_differentiator(pack["differentiators"])
    pack["constitution"] = "docs/PRODUCT_CONSTITUTION_AR.md"

    pack["sections"]["corpus_passport"] = await _corpus_passport_section()
    pack["sections"]["four_blockers"] = _four_blockers_section()

    pack["committee_checklist"] = [
        "Verify audit chain integrity",
        "Inspect public accuracy sample size and hit-rate",
        "Confirm Net-Edge reject rate (quality over quantity)",
        "Review labeled Signal Registry growth (moat)",
        "Open Corpus Passport (/corpus-passport)",
        "Confirm contradiction veto is fail-closed on severe conflict",
        "Confirm half-life stats exist (time-edge product)",
        "Review data moat / acquisition asset audit",
        "Read four-blockers evidence — do NOT treat as product COMPLETE",
        "Confirm live_fill / Jupiter VC / Full Mesh L2 100% / cloud multi-AZ are external-blocked or unpaid",
    ]

    pack["one_liner_for_ic"] = (
        "We sell audited market decisions with a labeled corpus and executable "
        "net-edge truth — not indicator spam. Institutional readiness is NOT COMPLETE "
        "while live_fill, Jupiter on-chain VC, Full Mesh L2 100%, or cloud multi-AZ remain open."
    )
    pack["product_complete"] = False
    pack["institutional_verdict"] = "NOT_COMPLETE"
    return pack
