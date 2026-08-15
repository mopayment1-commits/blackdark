"""B2B WebSocket hub must be awaitable on the web microservice startup path."""

from __future__ import annotations

import inspect

import pytest


def test_hub_start_is_async():
    from b2b_websocket_hub import B2BWebSocketHub

    assert inspect.iscoroutinefunction(B2BWebSocketHub.start)
    assert inspect.iscoroutinefunction(B2BWebSocketHub.stop)


@pytest.mark.asyncio
async def test_start_b2b_websocket_hub_is_awaitable(monkeypatch):
    import b2b_websocket_hub as hubmod
    import config

    monkeypatch.setattr(config, "B2B_WS_ENABLED", True)
    hubmod._hub = None
    await hubmod.start_b2b_websocket_hub()
    hub = hubmod.get_b2b_ws_hub()
    assert hub.stats()["running"] is True
    assert hub._heartbeat_task is not None
    await hubmod.stop_b2b_websocket_hub()
    assert hub.stats()["running"] is False


@pytest.mark.asyncio
async def test_start_b2b_websocket_hub_disabled_is_noop(monkeypatch):
    import b2b_websocket_hub as hubmod
    import config

    monkeypatch.setattr(config, "B2B_WS_ENABLED", False)
    hubmod._hub = None
    await hubmod.start_b2b_websocket_hub()
    assert hubmod._hub is None


@pytest.mark.asyncio
async def test_web_microservice_startup_path_sets_b2b_flag(monkeypatch, tmp_path):
    import b2b_websocket_hub as hubmod
    import config
    from microservices.lifecycle import ServiceContext, shutdown, startup

    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setattr(config, "SERVICE_MODE", "web")
    monkeypatch.setattr(config, "B2B_WS_ENABLED", True)
    monkeypatch.setattr(config, "ML_FLYWHEEL_ENABLED", False)
    monkeypatch.setattr("telegram_monitor.start_telegram_monitor", lambda: None)
    monkeypatch.setattr("telegram_bot_poller.start_telegram_poller", lambda: None)
    hubmod._hub = None

    ctx = await startup("web", ServiceContext())
    try:
        assert ctx.mode == "web"
        assert ctx.flags.get("b2b_ws") is True
        assert hubmod.get_b2b_ws_hub().stats()["running"] is True
    finally:
        await shutdown(ctx)
    assert hubmod.get_b2b_ws_hub().stats()["running"] is False


@pytest.mark.asyncio
async def test_dashboard_web_boot_does_not_log_await_none(monkeypatch):
    import logging

    import b2b_websocket_hub as hubmod
    import config
    from dashboard import _start_web_microservice

    class _App:
        def __init__(self):
            self.state = type("S", (), {})()

    records: list[str] = []

    class _Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record.getMessage())
            if record.exc_info and record.exc_info[1] is not None:
                records.append(str(record.exc_info[1]))

    monkeypatch.setenv("SERVICE_MODE", "web")
    monkeypatch.setattr(config, "SERVICE_MODE", "web")
    monkeypatch.setattr(config, "B2B_WS_ENABLED", True)
    monkeypatch.setattr(config, "ML_FLYWHEEL_ENABLED", False)
    monkeypatch.setattr("telegram_monitor.start_telegram_monitor", lambda: None)
    monkeypatch.setattr("telegram_bot_poller.start_telegram_poller", lambda: None)
    hubmod._hub = None

    handler = _Handler()
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        await _start_web_microservice(_App())
    finally:
        root.removeHandler(handler)
        if hubmod._hub is not None:
            await hubmod.stop_b2b_websocket_hub()

    blob = "\n".join(records)
    assert "can't be used in 'await' expression" not in blob
    assert "object NoneType" not in blob
