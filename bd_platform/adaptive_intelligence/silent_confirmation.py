"""Silent Confirmation Network — dependence-aware (spec §27)."""

from __future__ import annotations

from typing import Any


def effective_evidence_count(signals: list[dict[str, Any]]) -> dict[str, Any]:
    clusters: dict[str, list[dict[str, Any]]] = {}
    for sig in signals:
        cluster = sig.get("source_cluster") or sig.get("source_id") or sig.get("capability_id") or "unknown"
        clusters.setdefault(str(cluster), []).append(sig)
    raw = len(signals)
    effective = len(clusters)
    contradictions = [s for s in signals if s.get("contradicts")]
    return {
        "raw_count": raw,
        "effective_independent_evidence": effective,
        "dependence_clusters": {k: len(v) for k, v in clusters.items()},
        "contradictions": contradictions,
        "display": f"{effective} effective independent / {raw} raw (dependence-clustered)",
    }
