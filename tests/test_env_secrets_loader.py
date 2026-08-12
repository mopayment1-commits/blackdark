"""Coverage for env_secrets_loader (RC2 telegram private-file pointer)."""

from __future__ import annotations

import os

import pytest

import env_secrets_loader as esl

_TELEGRAM_ENV_KEYS = (
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "TELEGRAM_SECRETS_FILE",
)


@pytest.fixture(autouse=True)
def _isolate_telegram_env(monkeypatch):
    """Prevent os.environ writes in the loader from leaking into later tests."""
    for key in _TELEGRAM_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    esl._LOADED.clear()
    yield
    for key in _TELEGRAM_ENV_KEYS:
        os.environ.pop(key, None)
    esl._LOADED.clear()


def test_parse_and_load_secrets_file(tmp_path, monkeypatch):
    secret = tmp_path / "telegram.secrets.env"
    secret.write_text(
        "# comment\nTELEGRAM_BOT_TOKEN=123:AAAtesttokenvaluehere000\nTELEGRAM_CHAT_ID=42\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TELEGRAM_SECRETS_FILE", str(secret))
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    esl._LOADED.clear()

    assert esl.load_secrets_file("TELEGRAM_SECRETS_FILE") is True
    assert esl.load_secrets_file("TELEGRAM_SECRETS_FILE") is True  # idempotent
    assert os.environ["TELEGRAM_BOT_TOKEN"].startswith("123:")
    assert os.environ["TELEGRAM_CHAT_ID"] == "42"


def test_load_missing_pointer_and_missing_file(monkeypatch, tmp_path):
    monkeypatch.delenv("TELEGRAM_SECRETS_FILE", raising=False)
    esl._LOADED.clear()
    assert esl.load_secrets_file("TELEGRAM_SECRETS_FILE") is False

    monkeypatch.setenv("TELEGRAM_SECRETS_FILE", str(tmp_path / "nope.env"))
    assert esl.load_secrets_file("TELEGRAM_SECRETS_FILE") is False


def test_ensure_telegram_env_relative_pointer(monkeypatch, tmp_path):
    secret = tmp_path / "t.env"
    secret.write_text("TELEGRAM_BOT_TOKEN=9:ABCDEFGHIJKLMNOPQRSTUV\n", encoding="utf-8")
    monkeypatch.setenv("TELEGRAM_SECRETS_FILE", str(secret))
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    esl._LOADED.clear()
    esl.ensure_telegram_env()
    assert os.getenv("TELEGRAM_BOT_TOKEN", "").startswith("9:")


def test_override_false_preserves_existing(monkeypatch, tmp_path):
    secret = tmp_path / "t.env"
    secret.write_text("TELEGRAM_BOT_TOKEN=fromfile:xxxxxxxxxxxxxxxxxxxx\n", encoding="utf-8")
    monkeypatch.setenv("TELEGRAM_SECRETS_FILE", str(secret))
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "already:setxxxxxxxxxxxxxxxxx")
    esl._LOADED.clear()
    assert esl.load_secrets_file("TELEGRAM_SECRETS_FILE", override=False) is True
    assert os.environ["TELEGRAM_BOT_TOKEN"].startswith("already:")
    esl._LOADED.clear()
    assert esl.load_secrets_file("TELEGRAM_SECRETS_FILE", override=True) is True
    assert os.environ["TELEGRAM_BOT_TOKEN"].startswith("fromfile:")


def test_parse_env_file_skips_junk(tmp_path):
    p = tmp_path / "x.env"
    p.write_text("\n#c\n=noval\nOK=1\n", encoding="utf-8")
    assert esl._parse_env_file(p) == {"OK": "1"}
    assert esl._parse_env_file(tmp_path / "missing.env") == {}


@pytest.mark.asyncio
async def test_alert_service_loads_telegram_secrets(monkeypatch, tmp_path):
    import alert_service

    secret = tmp_path / "t.env"
    secret.write_text(
        "TELEGRAM_BOT_TOKEN=1:AAAAAAAAAAAAAAAAAAAA\nTELEGRAM_CHAT_ID=9\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("TELEGRAM_SECRETS_FILE", str(secret))
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    esl._LOADED.clear()

    class _Resp:
        status = 200

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

        def post(self, *a, **k):
            return _Resp()

    import aiohttp

    monkeypatch.setattr(aiohttp, "ClientSession", _Session)
    ok = await alert_service.send_telegram_message("hi")
    assert ok is True
    assert os.getenv("TELEGRAM_BOT_TOKEN", "").startswith("1:")


def test_telegram_poller_ensure_import(monkeypatch, tmp_path):
    import telegram_bot_poller as tbp

    secret = tmp_path / "t.env"
    secret.write_text("TELEGRAM_BOT_TOKEN=2:BBBBBBBBBBBBBBBBBBBB\n", encoding="utf-8")
    monkeypatch.setenv("TELEGRAM_SECRETS_FILE", str(secret))
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    esl._LOADED.clear()
    esl.ensure_telegram_env()
    assert os.getenv("TELEGRAM_BOT_TOKEN", "").startswith("2:")
    assert hasattr(tbp, "_poll_loop")


@pytest.mark.asyncio
async def test_telegram_poll_loop_returns_without_token(monkeypatch):
    import telegram_bot_poller as tbp

    monkeypatch.delenv("TELEGRAM_SECRETS_FILE", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    esl._LOADED.clear()
    await tbp._poll_loop()
