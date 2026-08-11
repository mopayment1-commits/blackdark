"""Service bus extended tests."""


import pytest

from service_bus import (
    bus_stats,
    publish,
    redis_url,
    start_service_bus,
    stop_service_bus,
    subscribe,
)


def test_redis_url_empty(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    assert redis_url() == ""


@pytest.mark.asyncio
async def test_publish_local_queue():
    hits = []

    async def h(p):
        hits.append(p)

    subscribe("blackdark.test", h)
    ok = await publish("blackdark.test", {"x": 1})
    assert ok is True
    assert hits[0]["x"] == 1


@pytest.mark.asyncio
async def test_start_stop_bus():
    await start_service_bus()
    stats = bus_stats()
    assert stats["enabled"]
    await stop_service_bus()


@pytest.mark.asyncio
async def test_publish_no_redis_uses_local(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "")
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    received = []

    async def h(p):
        received.append(p)

    subscribe("local.only", h)
    ok = await publish("local.only", {"ok": True})
    assert ok
    assert received
