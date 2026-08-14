"""Live Telegram on-call drill: secret-free receipts; FAIL closed without secrets."""

from __future__ import annotations

import json

import pytest


def test_telegram_oncall_live_fail_closed_without_secrets(monkeypatch, tmp_path):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_SECRETS_FILE", raising=False)
    monkeypatch.setenv("TELEGRAM_ONCALL_EVIDENCE_PATH", str(tmp_path / "tg.json"))
    from launch_drills import drill_telegram_oncall_live

    row = drill_telegram_oncall_live()
    assert row["id"] == "telegram_oncall_live"
    assert row["verdict"] == "FAIL"
    assert row["reason"] == "secrets_missing"
    blob = json.dumps(row)
    assert "TELEGRAM_BOT_TOKEN" not in blob
    assert ":AA" not in blob
    assert row.get("bot_token_present") is False
    assert row.get("chat_id_present") is False
    assert row.get("message_id") is None
    stamped = json.loads((tmp_path / "tg.json").read_text(encoding="utf-8"))
    assert stamped["verdict"] == "FAIL"
    assert "token" not in json.dumps(stamped).lower() or stamped.get("bot_token_present") is False
    assert "chat_id" not in stamped or "chat_id_present" in stamped


def test_telegram_oncall_live_pass_requires_message_id(monkeypatch, tmp_path):
    monkeypatch.setenv("TELEGRAM_ONCALL_EVIDENCE_PATH", str(tmp_path / "tg.json"))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:AAAnotarealtokenvaluehere000000")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")

    async def _fake(*, text: str) -> dict:
        assert "BLACKDARK" in text
        return {
            "ok": True,
            "reason": "ok",
            "bot_token_present": True,
            "chat_id_present": True,
            "bot_username": "blackdark_oncall_bot",
            "message_id": 9001,
            "chat_type": "private",
            "http_status": 200,
            "telegram_ok": True,
            "error_code": None,
        }

    monkeypatch.setattr("telegram_monitor.prove_telegram_oncall_page", _fake)
    from launch_drills import drill_telegram_oncall_live, telegram_oncall_live_proved

    row = drill_telegram_oncall_live()
    assert row["verdict"] == "PASS", row
    assert row["message_id"] == 9001
    assert row["bot_username"] == "blackdark_oncall_bot"
    assert row["chat_type"] == "private"
    blob = json.dumps(row)
    assert "123:AAA" not in blob
    assert "TELEGRAM_BOT_TOKEN" not in blob
    assert telegram_oncall_live_proved() is True


def test_receipt_omits_secrets_on_mocked_send(monkeypatch):
    pytest.importorskip("aiohttp")
    import alert_service

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:AAAnotarealtokenvaluehere000000")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")

    class _Resp:
        status = 200

        async def json(self, content_type=None):
            return {
                "ok": True,
                "result": {
                    "message_id": 77,
                    "chat": {"id": 42, "type": "private"},
                    "text": "hi",
                },
            }

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

    class _Session:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        def post(self, url, json=None):
            assert "123:AAA" in url  # request uses token; receipt must not
            return _Resp()

        def get(self, url):
            return _Resp()

    import aiohttp

    monkeypatch.setattr(aiohttp, "ClientSession", _Session)

    async def _run():
        receipt = await alert_service.send_telegram_message_receipt("hi")
        assert receipt["ok"] is True
        assert receipt["message_id"] == 77
        assert receipt["chat_type"] == "private"
        dumped = json.dumps(receipt)
        assert "123:AAA" not in dumped
        assert "chat_id" not in receipt
        assert "token" not in receipt
        assert receipt.get("chat_id_present") is True

    import asyncio

    asyncio.run(_run())
