"""Data platform compounding chain — governing reference verification."""

from __future__ import annotations

import inspect
from typing import Any, Callable


async def verify_chain_link(name: str, fn: Callable[..., Any], *, required_keys: tuple[str, ...] = ()) -> dict[str, Any]:
    try:
        result = fn()
        if inspect.isawaitable(result):
            result = await result
        if isinstance(result, dict):
            ok = all(k in result for k in required_keys) if required_keys else bool(result)
        else:
            ok = result is not None
        return {"link": name, "ok": ok, "result_keys": list(result.keys()) if isinstance(result, dict) else type(result).__name__}
    except Exception as exc:
        return {"link": name, "ok": False, "error": str(exc)}


async def verify_data_platform_chain(*, symbol: str = "BTC") -> dict[str, Any]:
    from cap646.data_spine import freshness_assurance_report, ingestion_architecture_report, normalization_report
    from data_lake import lake_status
    from data_provenance_score import compute_data_provenance_score
    from decision_certificate import build_decision_certificate
    from decision_ledger import ledger_stats
    from failure_corpus import corpus_stats
    from hot_storage import get_hot_storage_stats
    from market_event_library import event_library_stats
    from ml.experience_log import load_experience_summary
    from ml.feature_store import build_feature_vector
    from oracle_track_record import public_track_record
    from platform_chain_e2e import run_platform_compounding_e2e
    from signal_registry import registry_stats
    from user_exposure_log import exposure_stats

    hot = get_hot_storage_stats()
    hot_dict = hot.__dict__ if hasattr(hot, "__dict__") else {"stats": str(hot)}

    links = [
        await verify_chain_link("raw_lake", lake_status, required_keys=("sources_tracked",)),
        await verify_chain_link("raw_hot", lambda: hot_dict, required_keys=()),
        await verify_chain_link("source_ingestion", ingestion_architecture_report, required_keys=("architecture",)),
        await verify_chain_link("derived_normalize", lambda: normalization_report(symbol=symbol), required_keys=("schema_version",)),
        await verify_chain_link("freshness_assurance", lambda: freshness_assurance_report(symbol=symbol), required_keys=("freshness_chip",)),
        await verify_chain_link("entity_event_library", event_library_stats, required_keys=("status",)),
        await verify_chain_link("feature_store", lambda: build_feature_vector(symbol), required_keys=("asset",)),
        await verify_chain_link("provenance_score", lambda: compute_data_provenance_score(symbol=symbol), required_keys=("band",)),
        await verify_chain_link("signal_registry", registry_stats, required_keys=("status",)),
        await verify_chain_link(
            "decision_certificate",
            lambda: build_decision_certificate(
                {
                    "symbol": symbol,
                    "prediction_id": "chain-verify",
                    "decision_action": "WAIT",
                    "decision_sentence": "Platform chain verification",
                    "tier": "pro",
                }
            ),
            required_keys=("asset", "decision_action"),
        ),
        await verify_chain_link("decision_ledger", ledger_stats, required_keys=("status",)),
        await verify_chain_link("user_exposure", exposure_stats, required_keys=("status",)),
        await verify_chain_link("outcome_ledger", public_track_record, required_keys=("immutable_chain",)),
        await verify_chain_link("failure_corpus", corpus_stats, required_keys=("status",)),
        await verify_chain_link("learning_memory", load_experience_summary),
        await verify_chain_link("platform_e2e", lambda: run_platform_compounding_e2e(symbol=symbol), required_keys=("acceptance_evidence",)),
    ]

    e2e = await run_platform_compounding_e2e(symbol=symbol)
    failed = [l for l in links if not l.get("ok")]
    e2e_ok = e2e.get("verdict") == "VERIFIED_COMPLETE" and e2e.get("internal_closure") is True
    verdict = "VERIFIED_COMPLETE" if not failed and e2e_ok else "FUNCTIONALLY_INCOMPLETE"
    return {
        "chain": (
            "Raw→Derived→Entity/Event→Feature→Signal→Prediction/Decision→Confidence"
            "→User Exposure→Outcome→Evidence/Error→Learning→Model Version"
        ),
        "links": links,
        "failed": failed,
        "e2e": {
            "verdict": e2e.get("verdict"),
            "chain_id": e2e.get("chain_id"),
            "acceptance_evidence": e2e.get("acceptance_evidence"),
            "stage_count": len(e2e.get("stages") or {}),
            "failed_stages": [k for k, v in (e2e.get("stages") or {}).items() if not v.get("ok")],
        },
        "verdict": verdict,
        "internal_closure": not failed and e2e_ok,
    }
