"""Evidence provenance integration (DTS-051)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from decision_truth.methodology_versions import DTS_METHODOLOGY_VERSIONS


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_provenance_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Reuse canonical Data Governance provenance where available."""
    dg = payload.get("data_governance") or {}
    prov = dg.get("provenance") or {}
    fresh = dg.get("freshness") or {}
    quality = dg.get("quality") or {}
    lineage = prov.get("lineage") or {}

    material_inputs: list[dict[str, Any]] = []
    for key in ("symbol", "quote_age_ms", "net_profit_usdt", "total_slippage_bps", "depth_usd", "evidence_class"):
        if key in payload and payload.get(key) is not None:
            material_inputs.append(
                {
                    "field": key,
                    "source": payload.get("source") or prov.get("source") or "decision_payload",
                    "source_timestamp": fresh.get("as_of") or payload.get("timestamp"),
                    "ingestion_timestamp": _utc_now(),
                    "methodology_version": DTS_METHODOLOGY_VERSIONS["provenance"],
                    "freshness_state": fresh.get("freshness_state") or payload.get("freshness_state"),
                    "quality_state": quality.get("quality_state") or payload.get("data_quality_state"),
                    "transformation": "decision_truth.lifecycle",
                }
            )

    return {
        "state": "AVAILABLE" if material_inputs else "UNAVAILABLE",
        "material_inputs": material_inputs,
        "lineage": lineage,
        "methodology_version": DTS_METHODOLOGY_VERSIONS["provenance"],
        "timestamp_utc": _utc_now(),
    }
