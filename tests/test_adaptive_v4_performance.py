"""Representative local performance and reliability workloads."""

from __future__ import annotations

import concurrent.futures
import statistics
import time

import pytest
from fastapi.testclient import TestClient


def _percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    return s[int(round((p / 100) * (len(s) - 1)))]


@pytest.fixture(scope="module")
def client():
    import dashboard

    return TestClient(dashboard.app)


def _bench(fn, iterations: int = 100, warmup: int = 10) -> dict:
    for _ in range(warmup):
        fn()
    lat: list[float] = []
    errors = 0
    for _ in range(iterations):
        t0 = time.perf_counter()
        try:
            fn()
        except Exception:
            errors += 1
        lat.append((time.perf_counter() - t0) * 1000)
    return {
        "iterations": iterations,
        "p50_ms": round(_percentile(lat, 50), 3),
        "p95_ms": round(_percentile(lat, 95), 3),
        "p99_ms": round(_percentile(lat, 99), 3),
        "max_ms": round(max(lat), 3),
        "errors": errors,
    }


def test_workload_minimal_intent_api(client):
    r = _bench(lambda: client.post("/api/adaptive/route", json={"intent_id": "decide"}))
    assert r["errors"] == 0
    assert r["p95_ms"] < 500


def test_workload_typical_command_path(client):
    r = _bench(lambda: client.post("/api/adaptive/command", json={"query": "decide BTC intraday"}))
    assert r["errors"] == 0


def test_workload_explorer_query(client):
    r = _bench(lambda: client.get("/api/adaptive/explorer?query=oracle&limit=24"))
    assert r["errors"] == 0


def test_workload_data_room(client):
    r = _bench(lambda: client.get("/api/adaptive/data-room/1"))
    assert r["errors"] == 0


def test_workload_full_path_route_to_contract(client):
    def _full():
        route = client.post("/api/adaptive/route", json={"intent_id": "verify"}).json()
        client.post("/api/adaptive/decision-contract", json={"opportunity": {"symbol": "BTC", "quote_age_ms": 100, "data_quality_score": 80}, "router_result": route})

    r = _bench(_full, iterations=50)
    assert r["errors"] == 0


def test_workload_entitlement_denied_abstain():
    from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request

    r = route_intelligence_request(intent_id="decide", force_entitlement_denied=True)
    assert r["stance"] == "ABSTAIN"


def test_workload_degraded_abstain():
    from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request

    r = route_intelligence_request(intent_id="decide", force_degraded=True)
    assert r["stance"] == "ABSTAIN"


def test_concurrent_routing_no_corruption():
    from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request

    def _run():
        return route_intelligence_request(intent_id="decide")["stance"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(lambda _: _run(), range(40)))
    assert all(s in {"NEUTRAL", "ABSTAIN"} for s in results)


def test_candidate_explosion_budget():
    from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request
    from bd_platform.adaptive_intelligence.performance_budgets import PerformanceBudget

    with pytest.raises(ValueError, match="budget_candidate"):
        route_intelligence_request(intent_id="decide", budget=PerformanceBudget(max_candidates=1))


def test_local_performance_evidence_export():
    from bd_platform.adaptive_intelligence.performance_benchmarks import run_local_benchmarks

    ev = run_local_benchmarks()
    assert ev["status"] == "LOCAL_PERFORMANCE_ENGINEERING_COMPLETE"
    assert ev["router"]["iterations"] >= 50
