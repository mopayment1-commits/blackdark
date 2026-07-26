"""Tests for health_sidecar."""

import json
import time
import urllib.request

from health_sidecar import start_health_sidecar, stop_health_sidecar


def test_sidecar_responds_fast():
    port = 18777
    start_health_sidecar(port)
    time.sleep(0.3)
    # Warmup
    urllib.request.urlopen(f"http://127.0.0.1:{port}/health/live", timeout=2)
    t0 = time.perf_counter()
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health/live", timeout=2) as resp:
        body = json.loads(resp.read())
    elapsed_ms = (time.perf_counter() - t0) * 1000
    assert resp.status == 200
    assert body["status"] == "ok"
    assert body["sidecar"] is True
    assert elapsed_ms < 200
    stop_health_sidecar()
