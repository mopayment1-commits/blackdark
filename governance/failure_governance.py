"""Failure / degraded mode governance — ERR spine runtime (BGS-008)."""

from __future__ import annotations

from typing import Any

from governance.rfc9457 import is_problem_detail, problem_response


def failure_governance_status() -> dict[str, Any]:
    from failure_corpus import corpus_stats

    stats = corpus_stats()
    sample = problem_response(status=503, title="Service Unavailable", detail="degraded mode")
    return {
        "corpus_rows": stats.get("total", 0),
        "rfc9457_problem_contract": is_problem_detail(sample),
        "correlation_id_present": bool(sample.get("correlation_id")),
        "five_layer_ux": {
            "detection": True,
            "classification": True,
            "user_message": True,
            "recovery_action": True,
            "observability": True,
        },
        "categories": stats.get("by_category", {}),
    }
