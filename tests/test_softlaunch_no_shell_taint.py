"""DEC-0219 — Soft Launch env opener must not OS-command-taint admin email."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load_open_softlaunch():
    path = ROOT / "scripts" / "open_softlaunch_env.py"
    spec = importlib.util.spec_from_file_location("open_softlaunch_env", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_rejects_shell_metachar_email():
    mod = _load_open_softlaunch()
    with pytest.raises(ValueError):
        mod._validate_admin_email("evil;rm -rf /@x.com")
    with pytest.raises(ValueError):
        mod._validate_admin_email("bad|pipe@x.com")


def test_accepts_normal_email():
    mod = _load_open_softlaunch()
    assert mod._validate_admin_email("ops@example.com") == "ops@example.com"


def test_ensure_env_is_in_process_not_subprocess(monkeypatch, tmp_path):
    mod = _load_open_softlaunch()
    calls: list[list[str]] = []

    def _fake_call(cmd, *a, **k):
        calls.append(list(cmd))
        return 0

    monkeypatch.setattr(mod.subprocess, "call", _fake_call)
    monkeypatch.setattr(mod, "DEFAULT_ENV", tmp_path / "env.local")

    class _Boot:
        @staticmethod
        def write_softlaunch_env(*, admin_email, rotate):
            (tmp_path / "env.local").write_text("X" * 120, encoding="utf-8")
            return {"ok": True, "admin_email": admin_email, "rotate": rotate}

    monkeypatch.setattr(mod, "_load_bootstrap", lambda: _Boot)
    path = mod._ensure_env("ops@example.com", rotate=False)
    assert path.exists()
    assert path.stat().st_size >= 100
    # No subprocess during ensure/bootstrap — only editor open uses allowlisted binaries.
    assert calls == []
