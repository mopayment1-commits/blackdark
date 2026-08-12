"""Distributed service bus must not silently fall back when Redis is required."""

from __future__ import annotations

import pytest

import service_bus


@pytest.mark.asyncio
async def test_publish_fails_closed_without_redis_in_distributed_mode(monkeypatch):
    monkeypatch.setenv("ENV", "production")
    monkeypatch.delenv("SOFT_LAUNCH", raising=False)
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "false")
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:6399/0")
    monkeypatch.setenv("WEB_REPLICAS", "2")

    async def _no_redis():
        return None

    monkeypatch.setattr(service_bus, "_get_redis", _no_redis)
    ok = await service_bus.publish("blackdark.test", {"x": 1})
    assert ok is False


@pytest.mark.asyncio
async def test_local_bus_allowed_in_dev(monkeypatch):
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("SERVICE_BUS_LOCAL", "true")
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.setenv("WEB_REPLICAS", "1")
    ok = await service_bus.publish("blackdark.test", {"x": 1})
    assert ok is True
