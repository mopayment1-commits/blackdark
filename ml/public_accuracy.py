"""

BLACKDARK — Public Oracle Accuracy + AI model transparency API.



Live-only hit rate is the primary metric; synthetic seeded data is labeled separately.

"""



from __future__ import annotations

import asyncio
from typing import Any

import config
from oracle_integrity import is_synthetic_prediction


def _track_record_block() -> dict[str, Any]:
    try:
        from oracle_track_record import public_track_record

        return public_track_record()
    except Exception:
        return {"auto_accumulation": False}


def _chain_ref(pred_id: Any, chain_meta: dict[str, Any] | None) -> str | None:
    if chain_meta is not None:
        return (chain_meta.get("chain_hash") or "")[:16]
    if pred_id is not None:
        return f"oracle_pred:{pred_id}"
    return None


def _public_verdict_display(raw_verdict: Any) -> str:
    from supplemental_public_compliance import map_public_decision_action

    return map_public_decision_action(str(raw_verdict or ""))


def _public_recent_row(row: dict[str, Any], chain_meta: dict[str, Any] | None, label: str) -> dict[str, Any]:
    pred_id = row.get("id")
    raw_verdict = row.get("verdict")
    return {
        "prediction_id": pred_id,
        "timestamp": row.get("timestamp"),
        "asset": row.get("asset"),
        "verdict": _public_verdict_display(raw_verdict),
        "price_at_prediction": row.get("price_at_prediction"),
        "price_after_24h": row.get("price_after_24h"),
        "label": label,
        "direction_label": row.get("direction_label"),
        "accuracy_score": row.get("accuracy_score"),
        "opportunity_score": row.get("opportunity_score"),
        "synthetic": False,
        "source": row.get("source") or "oracle",
        "chain_hash": (chain_meta or {}).get("chain_hash"),
        "prev_hash": (chain_meta or {}).get("prev_hash"),
        "chain_seq": (chain_meta or {}).get("seq"),
        "chain_ref": _chain_ref(pred_id, chain_meta),
    }


def _public_recent_predictions(
    recent: list[dict[str, Any]],
    chain_lookup: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], int, int]:
    chain_lookup = chain_lookup if chain_lookup is not None else _chain_lookup()
    public_recent = []
    correct = 0
    resolved_rows = 0
    for row in recent:
        if not row.get("resolved") or is_synthetic_prediction(row):
            continue
        resolved_rows += 1
        label = str(row.get("label") or row.get("outcome") or "")
        if label == "correct":
            correct += 1
        pred_id = row.get("id")
        chain_meta = chain_lookup.get(str(pred_id) if pred_id is not None else "")
        public_recent.append(_public_recent_row(row, chain_meta, label))
    return public_recent, correct, resolved_rows


async def build_public_accuracy_payload(*, recent_limit: int = 20) -> dict[str, Any]:

    from database import fetch_labeled_oracle_predictions, fetch_oracle_audit_stats
    from ml.experience_log import public_experience_block
    from ml.train_baseline import model_status
    from ml.training_utils import LEAKAGE_GUARD_NOTE



    stats = await fetch_oracle_audit_stats(limit=recent_limit, include_synthetic=False)

    from oracle_audit_chain import chain_summary, read_recent_chain_records

    chain_ctx = await asyncio.to_thread(lambda: chain_summary(limit=8))
    chain_verify = chain_ctx.get("integrity") or {}
    chain_recent_tail = await asyncio.to_thread(lambda: read_recent_chain_records(200))
    chain_lookup = _chain_lookup_from_recent(chain_recent_tail)

    ml_status = await model_status()

    labeled = await fetch_labeled_oracle_predictions(limit=1000, include_synthetic=False)

    experience = public_experience_block()



    recent_raw = stats.get("recent") or []
    public_recent, correct, resolved_rows = _public_recent_predictions(recent_raw, chain_lookup)

    hit_rate = round(correct / resolved_rows * 100, 2) if resolved_rows else 0.0

    live_block = stats.get("live") or {}
    live_resolved = int(
        live_block.get("resolved_predictions", stats.get("resolved_predictions", 0)) or 0
    )
    live_total = int(live_block.get("total_predictions", stats.get("total_predictions", 0)) or 0)
    live_pending = int(
        live_block.get("pending_predictions", stats.get("pending_predictions", 0)) or 0
    )
    metrics_footnote = (
        f"Average accuracy is the cumulative mean over {live_resolved} resolved live prediction(s). "
        f"Logged total ({live_total}) includes {live_pending} still pending 24h resolution."
    )
    if public_recent:
        recent_table_footnote = (
            f"Showing {min(len(public_recent), recent_limit)} most recent resolved rows "
            f"from the last {len(recent_raw)} logged prediction(s) in this window."
        )
    else:
        recent_table_footnote = (
            f"No resolved rows in the last {len(recent_raw)} logged prediction(s) "
            f"(window limit {recent_limit}). Cumulative stats above still use all {live_resolved} resolved live rows."
        )



    track_record_block = _track_record_block()



    from ml.drift_monitor import load_feature_envelope



    envelope = load_feature_envelope()

    production_engine = "ml_model" if ml_status.get("latest_model_loaded") else "rules_engine"

    synthetic_block = stats.get("synthetic") or {}



    return {

        "product": "BLACKDARK Oracle AI",

        "mission": "Proprietary crypto intelligence — every live prediction tracked publicly",

        "transparency": {

            "production_engine": production_engine,

            "engine_note": (

                "Live verdicts use deterministic rules engine until ML model is trained and OOD-validated."

                if production_engine == "rules_engine"

                else "ML model active with OOD gate and temporal hold-out validation."

            ),

            "confidence_type": "calibrated" if envelope else "heuristic_formula",

            "drift_monitoring": envelope is not None,

            "ood_protection": True,

            "min_training_samples": ml_status.get("min_samples_required"),

            "validation_method": "temporal_holdout",

            "synthetic_data_excluded": True,

            "integrity_note": LEAKAGE_GUARD_NOTE,

        },

        "oracle": {

            "total_predictions": stats.get("live", {}).get("total_predictions", stats.get("total_predictions", 0)),

            "resolved_predictions": stats.get("live", {}).get(

                "resolved_predictions", stats.get("resolved_predictions", 0)

            ),

            "pending_predictions": stats.get("live", {}).get(

                "pending_predictions", stats.get("pending_predictions", 0)

            ),

            "average_accuracy_percent": stats.get("live", {}).get(

                "average_accuracy_percent", stats.get("average_accuracy_percent", 0)

            ),

            "recent_hit_rate_percent": hit_rate,

            "recent_predictions": public_recent[:recent_limit],

            "metrics_scope": "live_only",

            "recent_resolved_shown": len(public_recent[:recent_limit]),

            "recent_window_scanned": len(recent_raw),

            "metrics_footnote": metrics_footnote,

            "recent_table_footnote": recent_table_footnote,

        },

        "synthetic_demo_data": {

            "excluded_from_hit_rate": True,

            "total_predictions": synthetic_block.get("total_predictions", 0),

            "resolved_predictions": synthetic_block.get("resolved_predictions", 0),

            "average_accuracy_percent": synthetic_block.get("average_accuracy_percent", 0),

            "note": synthetic_block.get(

                "note",

                "Demo backfill for chain integrity — not counted as live performance.",

            ),

        },

        "model": {

            "production_engine": production_engine,

            "labeled_samples": len(labeled),

            "min_samples_required": ml_status.get("min_samples_required"),

            "latest_model_loaded": ml_status.get("latest_model_loaded"),

            "latest_model_version": ml_status.get("latest_model_version"),

            "auto_train_enabled": ml_status.get("auto_train_enabled"),

            "latest_run": ml_status.get("latest_run"),

            "drift_envelope_ready": envelope is not None,

            "synthetic_excluded": True,

            "validation_method": "temporal_holdout",

        },

        "learning_experience": experience,

        "immutable_track_record": track_record_block,

        "data_moat": {

            "exchanges": len(config.INGESTION_READY_EXCHANGES),

            "assets": len(config.UNIVERSE_ASSETS),

        },

        "proof_chain": _proof_chain_block_from_summary(chain_ctx, chain_verify),

        "regime_models": _regime_models_block(),

        "signal_registry": _signal_registry_block(),

        "drift": _drift_status_block(),

        "constitution": "docs/PRODUCT_CONSTITUTION_AR.md",

        "heroes_binding": "docs/HEROES_STRATEGY_BINDING.md",

    }


def _regime_models_block() -> dict[str, Any]:
    try:
        from ml.regime_models import regime_model_registry

        return regime_model_registry()
    except Exception as exc:
        return {"error": str(exc), "evidence_status": "unavailable"}


def _signal_registry_block() -> dict[str, Any]:
    """Public-safe D8 moat summary (no persist paths / raw feature dumps)."""
    try:
        from signal_registry import registry_stats

        stats = registry_stats()
        return {
            "differentiator": "D8",
            "total": stats.get("total_in_memory", 0),
            "labeled": stats.get("labeled", 0),
            "unlabeled": stats.get("unlabeled", 0),
            "by_type": stats.get("by_type") or {},
            "by_label": stats.get("by_label") or {},
            "public_lexicon_note": (
                "Public analytical feature lexicon — entry counts by type; "
                "labels grow as Oracle decisions resolve."
            ),
            "generated_at": stats.get("generated_at"),
            "api": "/api/oracle/signals",
        }
    except Exception as exc:
        return {"error": str(exc), "differentiator": "D8"}


def _drift_status_block() -> dict[str, Any]:
    """Core Canon §1.3 — product-facing drift / freeze state (fail-closed visibility)."""
    envelope_ready = False
    try:
        from ml.drift_monitor import load_feature_envelope

        envelope_ready = load_feature_envelope() is not None
    except Exception:
        envelope_ready = False
    try:
        from risk_manager import risk_status

        risk = risk_status()
    except Exception:
        risk = {}
    freeze_reason = str(risk.get("freeze_reason") or "")
    drift_freeze = freeze_reason.startswith("ml_drift_high")
    return {
        "drift_envelope_ready": envelope_ready,
        "trading_frozen": bool(risk.get("trading_frozen")),
        "freeze_reason": freeze_reason,
        "drift_freeze_active": drift_freeze,
        "fail_closed": drift_freeze or bool(risk.get("trading_frozen")),
        "note": "High PSI drift freezes trading; public surface shows freeze state honestly.",
    }


def _chain_lookup_from_recent(recent: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for entry in recent:
        pid = entry.get("prediction_id")
        if pid is None:
            continue
        index[str(pid)] = {
            "chain_hash": entry.get("chain_hash"),
            "prev_hash": entry.get("prev_hash"),
            "seq": entry.get("seq"),
        }
    return index


def _chain_lookup() -> dict[str, dict[str, Any]]:
    """Map prediction_id -> latest audit-chain entry (best-effort)."""
    try:
        from oracle_audit_chain import read_recent_chain_records

        return _chain_lookup_from_recent(read_recent_chain_records(200))
    except Exception:
        return {}


def _proof_chain_block_from_summary(summary: dict[str, Any], verify: dict[str, Any]) -> dict[str, Any]:
    try:
        from supplemental_public_compliance import sanitize_public_decision_records

        if summary.get("recent_records"):
            summary = {
                **summary,
                "recent_records": sanitize_public_decision_records(list(summary["recent_records"])),
            }
        recent = summary.get("recent_records") or []
        tip = recent[-1] if recent else {}
        block: dict[str, Any] = {
            "summary": summary,
            "verify": verify,
            "public_page": "/oracle-accuracy",
            "tip_hash": tip.get("chain_hash") if verify.get("valid") else None,
            "total_records": summary.get("total_records"),
        }
        if not verify.get("valid"):
            block["integrity_status"] = "failed"
            block["integrity_message"] = verify.get("integrity_failure_reason") or (
                "Audit chain integrity check failed — tip linkage cannot be used as proof."
            )
        else:
            block["integrity_status"] = "verified"
        return block
    except Exception as exc:
        return {"error": str(exc)}


def _proof_chain_block() -> dict[str, Any]:
    try:
        from oracle_audit_chain import chain_summary

        summary = chain_summary(limit=8)
        verify = summary.get("integrity") or {}
        return _proof_chain_block_from_summary(summary, verify)
    except Exception as exc:
        return {"error": str(exc)}

