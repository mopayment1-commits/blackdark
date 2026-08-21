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
    from cap646.data_spine import freshness_assurance_report, ingestion_architecture_report
    from data_provenance_score import compute_data_provenance_score
    from decision_certificate import build_decision_certificate
    from ml.experience_log import load_experience_summary
    from oracle_track_record import public_track_record
    from signal_registry import registry_stats

    links = [
        await verify_chain_link("source_ingestion", ingestion_architecture_report, required_keys=("architecture",)),
        await verify_chain_link("freshness_assurance", lambda: freshness_assurance_report(symbol=symbol), required_keys=("freshness_chip",)),
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
        await verify_chain_link("outcome_ledger", public_track_record, required_keys=("immutable_chain",)),
        await verify_chain_link("learning_memory", load_experience_summary),
    ]

    failed = [l for l in links if not l.get("ok")]
    verdict = "VERIFIED_COMPLETE" if not failed else "FUNCTIONALLY_INCOMPLETE"
    return {
        "chain": "Source→Normalize→Lake/Hot→Provenance→Signal→Decision→Outcome→Learning→Evidence",
        "links": links,
        "failed": failed,
        "verdict": verdict,
        "internal_closure": not failed,
    }
