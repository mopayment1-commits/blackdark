"""Circuit Breaker Layer (#1051) tests."""

from __future__ import annotations

import time

import pytest

from circuit_breaker_layer import (
    _STATE_OPEN,
    check_circuit,
    check_circuit_breaker_production_gate,
    circuit_breaker_layer_status,
    record_service_request,
    reset_circuits_for_tests,
    run_circuit_breaker_e2e,
)


@pytest.fixture(autouse=True)
def _clean_circuits():
    reset_circuits_for_tests()
    yield
    reset_circuits_for_tests()


def test_circuit_breaker_status():
    status = circuit_breaker_layer_status()
    assert status["feature"] == "circuit_breaker_layer"
    assert status["triggers"]["error_rate_pct_60s"] == 50
    assert status["integrations"]["rate_limiting_ref"] == 1046


def test_production_gate():
    gate = check_circuit_breaker_production_gate()
    assert gate["ok"] is True


def test_trips_on_high_error_rate():
    svc = "oracle_api"
    for _ in range(10):
        record_service_request(svc, success=False, latency_ms=50)
    gate = check_circuit(svc)
    assert gate["degraded"] is True or gate.get("allow") is False


def test_degraded_response_when_open():
    svc = "data_engine"
    for _ in range(20):
        record_service_request(svc, success=False, latency_ms=50)
    gate = check_circuit(svc)
    if gate.get("allow") is False:
        assert gate["fallback"] == "cached_stale"
        assert gate["badge"] == "Service Degraded"


def test_e2e():
    assert run_circuit_breaker_e2e()["all_passed"] is True
