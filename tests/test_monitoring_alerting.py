"""Monitoring & alerting module tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_monitoring_status_shape():
    from ops.monitoring_alerting import monitoring_status

    status = await monitoring_status()
    assert "uptime_24h" in status
    assert "enabled" in status


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

    monkeypatch.setattr("httpx.AsyncClient", lambda **k: _Client())
    monkeypatch.setenv("MONITORING_BASE_URL", "http://test")
    result = await probe_endpoints()
    assert result["overall_ok"] is True
    assert len(result["probes"]) == 2
