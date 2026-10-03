"""Monitoring & alerting module tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_monitoring_status_shape():
    from ops.monitoring_alerting import monitoring_status

    status = await monitoring_status()
    assert "uptime_24h" in status
    assert "enabled" in status
    assert "health_signals" in status


@pytest.mark.asyncio
async def test_probe_endpoints_records_probes(monkeypatch):
    from ops.monitoring_alerting import probe_endpoints

    class _Resp:
        status_code = 200

    class _Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, url):
            return _Resp()

    async def _neutral_health_signals():
        return {"signals": {}, "error_rate": {}, "uptime_24h": {}, "vendor_rate_limits": {}}

    monkeypatch.setattr("ops.monitoring_alerting.httpx.AsyncClient", lambda **k: _Client())
    monkeypatch.setattr("ops.monitoring_alerting.check_health_signals", _neutral_health_signals)
    monkeypatch.setenv("MONITORING_BASE_URL", "http://test")
    result = await probe_endpoints()
    assert result["overall_ok"] is True
    assert len(result["probes"]) == 2
    assert all(p.get("ok") for p in result["probes"])
    assert "health_signals" in result


@pytest.mark.asyncio
async def test_check_health_signals_shape():
    from ops.monitoring_alerting import check_health_signals

    signals = await check_health_signals()
    assert "error_rate" in signals
    assert "uptime_24h" in signals
    assert "vendor_rate_limits" in signals


def test_vendor_rate_limit_watchdog_status():
    from ops.vendor_rate_limit_watchdog import vendor_rate_limit_status

    status = vendor_rate_limit_status()
    assert "signals" in status
    assert "overall_ok" in status


def test_setup_monitoring_script():
    import subprocess
    import sys

    proc = subprocess.run([sys.executable, "scripts/setup_monitoring.py"], capture_output=True, text=True)
    assert proc.returncode in (0, 1)
    assert "monitoring_setup_ok" in proc.stdout


def test_free_api_rate_limit_audit():
    import subprocess
    import sys

    proc = subprocess.run([sys.executable, "scripts/free_api_rate_limit_audit.py"], capture_output=True, text=True)
    assert proc.returncode in (0, 1)
    assert "PASS_RATE_LIMIT_REVIEW" in proc.stdout
