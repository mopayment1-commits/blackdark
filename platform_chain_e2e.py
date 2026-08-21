"""
BLACKDARK — Platform compounding E2E chain.

Executes the full dependency chain with real modules and returns acceptance evidence:
Raw → Derived → Entity/Event → Feature → Signal → Prediction/Decision → Confidence
→ User Exposure → Outcome → Evidence/Error → Learning → Model Version
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _hot_stats_dict() -> dict[str, Any]:
    from hot_storage import get_hot_storage_stats

    stats = get_hot_storage_stats()
    if hasattr(stats, "__dict__"):
        return dict(stats.__dict__)
    return {"stats": str(stats)}


async def run_platform_compounding_e2e(
    *,
    symbol: str = "BTC",
    user_id: str = "platform-chain-verify",
    tier: str = "pro",
) -> dict[str, Any]:
    """Run one full compounding chain cycle; used for closure verification."""
    from cap646.evidence_class import infer_evidence_class

    chain_id = f"chain_{uuid4().hex[:12]}"
    evidence_class = infer_evidence_class(source="oracle")
    stages: dict[str, Any] = {}
    errors: list[str] = []

    # 1 Raw Data
    try:
        from data_lake import lake_status

        lake = await lake_status()
        hot = _hot_stats_dict()
        stages["raw_data"] = {
            "ok": lake.get("sources_tracked") is not None,
            "lake_keys": list(lake.keys())[:8],
            "hot_backend": hot.get("backend") or hot.get("stats"),
        }
    except Exception as exc:
        stages["raw_data"] = {"ok": False, "error": str(exc)}
        errors.append(f"raw_data:{exc}")

    # 2 Derived / Normalize
    try:
        from cap646.data_spine import normalization_report

        derived = await normalization_report(symbol=symbol)
        stages["derived_data"] = {
            "ok": bool(derived.get("success")) and bool(derived.get("normalized_context") or derived.get("provenance")),
            "schema_version": derived.get("schema_version"),
        }
    except Exception as exc:
        stages["derived_data"] = {"ok": False, "error": str(exc)}
        errors.append(f"derived_data:{exc}")

    # 3 Entity / Event
    try:
        from market_event_library import record_market_event

        event = record_market_event(
            event_name=f"platform_chain_{chain_id}",
            category="platform_verification",
            symbol=symbol,
            severity="info",
            description="Platform compounding E2E verification event",
            metadata={"chain_id": chain_id},
            evidence_class=evidence_class,
            source="platform_chain_e2e",
        )
        stages["entity_event"] = {"ok": bool(event.get("event_id")), "event_id": event.get("event_id")}
    except Exception as exc:
        stages["entity_event"] = {"ok": False, "error": str(exc)}
        errors.append(f"entity_event:{exc}")

    # 4 Feature
    features: dict[str, Any] = {}
    try:
        from ml.feature_store import build_feature_vector

        features = await build_feature_vector(symbol)
        stages["feature"] = {
            "ok": "asset" in features and isinstance(features.get("ret_1h"), (int, float)),
            "asset": features.get("asset"),
            "feature_count": len(features),
        }
    except Exception as exc:
        stages["feature"] = {"ok": False, "error": str(exc)}
        errors.append(f"feature:{exc}")

    prediction_id = f"pred_{chain_id}"
    signal: dict[str, Any] = {}

    # 5 Signal
    try:
        from signal_registry import register_signal

        signal = register_signal(
            signal_type="oracle_direction",
            asset=symbol,
            prediction_id=prediction_id,
            features=features,
            verdict="WAIT",
            score=55.0,
            provenance={"chain_id": chain_id, "source": "platform_chain_e2e"},
            label="pending",
        )
        stages["signal"] = {"ok": bool(signal.get("signal_id")), "signal_id": signal.get("signal_id")}
    except Exception as exc:
        stages["signal"] = {"ok": False, "error": str(exc)}
        errors.append(f"signal:{exc}")

    # 6 Prediction / Decision
    decision: dict[str, Any] = {}
    cert: dict[str, Any] = {}
    try:
        from decision_certificate import build_decision_certificate
        from decision_ledger import record_decision

        cert = build_decision_certificate(
            {
                "symbol": symbol,
                "prediction_id": prediction_id,
                "decision_action": "WAIT",
                "decision_sentence": "Platform chain verification — evidence-first posture.",
                "tier": tier,
                "opportunity_score": 55.0,
            }
        )
        decision = record_decision(
            prediction_id=prediction_id,
            decision_action=str(cert.get("decision_action") or "WAIT"),
            symbol=symbol,
            certificate_hash=cert.get("certificate_hash"),
            evidence_class=evidence_class,
            source="platform_chain_e2e",
            meta={"chain_id": chain_id, "signal_id": signal.get("signal_id")},
        )
        stages["prediction_decision"] = {
            "ok": bool(decision.get("decision_id")) and bool(cert.get("certificate_hash")),
            "decision_id": decision.get("decision_id"),
        }
    except Exception as exc:
        stages["prediction_decision"] = {"ok": False, "error": str(exc)}
        errors.append(f"prediction_decision:{exc}")

    # 7 Confidence
    try:
        from data_provenance_score import compute_data_provenance_score

        prov = compute_data_provenance_score(symbol=symbol)
        confidence_ok = prov.get("band") in {"decision_grade", "caution", "insufficient"}
        stages["confidence"] = {"ok": confidence_ok, "band": prov.get("band"), "score": prov.get("score")}
    except Exception as exc:
        stages["confidence"] = {"ok": False, "error": str(exc)}
        errors.append(f"confidence:{exc}")

    # 8 User Exposure
    exposure: dict[str, Any] = {}
    try:
        from decision_ledger import link_exposure
        from user_exposure_log import record_user_exposure

        exposure = record_user_exposure(
            user_id=user_id,
            tier=tier,
            surface="platform_chain_e2e",
            decision_id=decision.get("decision_id"),
            prediction_id=prediction_id,
            symbol=symbol,
            evidence_class=evidence_class,
            source="platform_chain_e2e",
            meta={"chain_id": chain_id},
        )
        if decision.get("decision_id") and exposure.get("exposure_id"):
            link_exposure(str(decision["decision_id"]), str(exposure["exposure_id"]))
        stages["user_exposure"] = {"ok": bool(exposure.get("exposure_id")), "exposure_id": exposure.get("exposure_id")}
    except Exception as exc:
        stages["user_exposure"] = {"ok": False, "error": str(exc)}
        errors.append(f"user_exposure:{exc}")

    # 9 Outcome
    outcome_id = f"out_{chain_id}"
    try:
        from decision_ledger import link_outcome
        from oracle_track_record import public_track_record

        ledger = public_track_record()
        outcome_ok = bool(ledger.get("immutable_chain") or ledger.get("total_predictions") is not None)
        if decision.get("decision_id"):
            link_outcome(str(decision["decision_id"]), outcome_id)
        stages["outcome"] = {
            "ok": outcome_ok,
            "outcome_id": outcome_id,
            "ledger_total": ledger.get("total_predictions"),
        }
    except Exception as exc:
        stages["outcome"] = {"ok": False, "error": str(exc)}
        errors.append(f"outcome:{exc}")

    # 10 Evidence / Error
    try:
        from acquirer_evidence_pack import build_acquirer_evidence_pack
        from failure_corpus import record_failure

        pack = await build_acquirer_evidence_pack()
        failure = record_failure(
            source="platform_chain_e2e",
            reason="boundary_verification",
            category="verification",
            evidence_class="SIMULATED",
            meta={"chain_id": chain_id, "note": "E2E boundary path — not a live kill"},
        )
        stages["evidence_error"] = {
            "ok": bool(pack.get("generated_at")) and bool(failure.get("failure_id")),
            "evidence_pack_sections": len(pack.get("sections") or {}),
            "failure_id": failure.get("failure_id"),
        }
    except Exception as exc:
        stages["evidence_error"] = {"ok": False, "error": str(exc)}
        errors.append(f"evidence_error:{exc}")

    # 11 Learning
    try:
        from ml.experience_log import append_experience, load_experience_summary

        entry = append_experience(
            "prediction_logged",
            {
                "chain_id": chain_id,
                "prediction_id": prediction_id,
                "decision_id": decision.get("decision_id"),
                "symbol": symbol,
            },
            notes="platform_compounding_e2e",
        )
        summary = load_experience_summary()
        stages["learning"] = {
            "ok": bool(entry.get("timestamp")) and isinstance(summary, dict),
            "total_events": summary.get("total_events"),
        }
    except Exception as exc:
        stages["learning"] = {"ok": False, "error": str(exc)}
        errors.append(f"learning:{exc}")

    # 12 Model Version
    try:
        from database import fetch_latest_ml_model_run

        model = await fetch_latest_ml_model_run()
        stages["model_version"] = {
            "ok": model is None or bool(model.get("model_version")),
            "model_version": (model or {}).get("model_version"),
            "model_name": (model or {}).get("model_name"),
        }
    except Exception as exc:
        stages["model_version"] = {"ok": False, "error": str(exc)}
        errors.append(f"model_version:{exc}")

    all_ok = all(stage.get("ok") for stage in stages.values())
    return {
        "chain_id": chain_id,
        "generated_at": _utcnow(),
        "symbol": symbol.upper(),
        "evidence_class": evidence_class,
        "verdict": "VERIFIED_COMPLETE" if all_ok and not errors else "FUNCTIONALLY_INCOMPLETE",
        "stages": stages,
        "errors": errors,
        "acceptance_evidence": {
            "prediction_id": prediction_id,
            "decision_id": decision.get("decision_id"),
            "exposure_id": exposure.get("exposure_id"),
            "certificate_hash": cert.get("certificate_hash"),
            "signal_id": signal.get("signal_id"),
            "outcome_id": outcome_id,
        },
        "internal_closure": all_ok and not errors,
    }
