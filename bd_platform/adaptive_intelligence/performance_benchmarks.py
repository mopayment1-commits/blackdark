"""Local performance/replay benchmarks — spec §30."""

from __future__ import annotations

import statistics
import time
from typing import Any


def _percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((pct / 100.0) * (len(ordered) - 1)))
    return ordered[min(idx, len(ordered) - 1)]


def benchmark_router(iterations: int = 50) -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request

    latencies: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        route_intelligence_request(intent_id="decide")
        latencies.append((time.perf_counter() - t0) * 1000)
    return {
        "operation": "route_intelligence_request",
        "iterations": iterations,
        "p50_ms": round(_percentile(latencies, 50), 3),
        "p95_ms": round(_percentile(latencies, 95), 3),
        "p99_ms": round(_percentile(latencies, 99), 3),
        "mean_ms": round(statistics.mean(latencies), 3),
        "local_measurement": True,
        "production_slo_gated": True,
    }


def benchmark_decision_contract(iterations: int = 30) -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.decision_contract import build_adaptive_decision_contract
    from net_edge_truth import FIN_004_DEMO_OPPORTUNITY

    opp = dict(FIN_004_DEMO_OPPORTUNITY)
    opp.update({"symbol": "BTC", "quote_age_ms": 120, "data_quality_score": 80, "evidence_class": "forward_shadow"})
    latencies: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        build_adaptive_decision_contract(opp)
        latencies.append((time.perf_counter() - t0) * 1000)
    return {
        "operation": "build_adaptive_decision_contract",
        "iterations": iterations,
        "p50_ms": round(_percentile(latencies, 50), 3),
        "p95_ms": round(_percentile(latencies, 95), 3),
        "mean_ms": round(statistics.mean(latencies), 3),
        "local_measurement": True,
    }


def run_local_benchmarks() -> dict[str, Any]:
    router = benchmark_router()
    contract = benchmark_decision_contract()
    return {
        "status": "LOCAL_PERFORMANCE_ENGINEERING_COMPLETE",
        "router": router,
        "decision_contract": contract,
        "production_slo_evidence_gated": True,
    }
