"""Platform API key status + live verification (LunarCrush, CoinMarketCal, DeBank)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import aiohttp
from pathlib import Path

_PLATFORM_KEYS: tuple[dict[str, str], ...] = (
    {
        "id": "lunarcrush",
        "env": "LUNARCRUSH_API_KEY",
        "label": "LunarCrush",
        "signup": "https://lunarcrush.com/pricing",
        "docs": "https://lunarcrush.com/developers",
        "tier": "Hobby FREE — market data API 100/day",
    },
    {
        "id": "coinmarketcal",
        "env": "COINMARKETCAL_API_KEY",
        "label": "CoinMarketCal",
        "signup": "https://coinmarketcal.com/en/api",
        "docs": "https://developers.coinmarketcal.com",
        "tier": "Personal FREE — register for x-api-key",
    },
    {
        "id": "debank",
        "env": "DEBANK_API_KEY",
        "label": "DeBank Cloud",
        "signup": "https://cloud.debank.com/",
        "docs": "https://docs.cloud.debank.com/en/readme/open-api",
        "tier": "Paid — 200 USDC / 1M compute units (no free tier)",
    },
)

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}…{value[-4:]}"


def keys_status() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    configured = 0
    for spec in _PLATFORM_KEYS:
        raw = os.getenv(spec["env"], "").strip()
        ok = bool(raw)
        if ok:
            configured += 1
        rows.append({
            **spec,
            "configured": ok,
            "masked": _mask(raw) if ok else None,
        })
    return {
        "timestamp": _utcnow(),
        "total": len(_PLATFORM_KEYS),
        "configured_count": configured,
        "keys": rows,
        "setup_script": "python scripts/connect_platform_keys.py",
        "env_file": ".env",
    }


async def _http_check(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict | None = None,
) -> tuple[bool, str, int | None]:
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status == 200:
                    return True, "ok", resp.status
                text = (await resp.text())[:120]
                return False, f"HTTP {resp.status}: {text}", resp.status
    except aiohttp.ClientError as exc:
        return False, str(exc)[:120], None


async def verify_lunarcrush(key: str | None = None) -> dict[str, Any]:
    token = (key or os.getenv("LUNARCRUSH_API_KEY", "")).strip()
    if not token:
        return {"service": "lunarcrush", "configured": False, "valid": False, "reason": "LUNARCRUSH_API_KEY not set"}
    ok, msg, status = await _http_check(
        "https://lunarcrush.com/api4/public/coins/btc/v1",
        headers={"Authorization": f"Bearer {token}"},
    )
    return {
        "service": "lunarcrush",
        "configured": True,
        "valid": ok,
        "http_status": status,
        "message": msg,
        "endpoint": "/api/platform/social/lunarcrush",
    }


async def verify_coinmarketcal(key: str | None = None) -> dict[str, Any]:
    token = (key or os.getenv("COINMARKETCAL_API_KEY", "")).strip()
    if not token:
        return {"service": "coinmarketcal", "configured": False, "valid": False, "reason": "COINMARKETCAL_API_KEY not set"}
    ok, msg, status = await _http_check(
        "https://developers.coinmarketcal.com/v1/events",
        headers={"x-api-key": token, "Accept": "application/json"},
        params={"max": 3, "page": 1},
    )
    return {
        "service": "coinmarketcal",
        "configured": True,
        "valid": ok,
        "http_status": status,
        "message": msg,
        "endpoint": "/api/platform/events/calendar",
    }


async def verify_debank(key: str | None = None) -> dict[str, Any]:
    token = (key or os.getenv("DEBANK_API_KEY", "")).strip()
    if not token:
        return {"service": "debank", "configured": False, "valid": False, "reason": "DEBANK_API_KEY not set"}
    ok, msg, status = await _http_check(
        "https://pro-openapi.debank.com/v1/account/units",
        headers={"AccessKey": token, "accept": "application/json"},
    )
    return {
        "service": "debank",
        "configured": True,
        "valid": ok,
        "http_status": status,
        "message": msg,
        "endpoint": "/api/platform/wallet/debank",
    }


async def verify_all_keys() -> dict[str, Any]:
    results = [
        await verify_lunarcrush(),
        await verify_coinmarketcal(),
        await verify_debank(),
    ]
    valid = sum(1 for r in results if r.get("valid"))
    configured = sum(1 for r in results if r.get("configured"))
    return {
        "timestamp": _utcnow(),
        "configured_count": configured,
        "valid_count": valid,
        "results": results,
    }


def _read_env_lines() -> list[str]:
    if not _ENV_PATH.exists():
        example = _ENV_PATH.parent / ".env.example"
        if example.exists():
            return example.read_text(encoding="utf-8").splitlines()
        return ["# BLACKDARK"]
    return _ENV_PATH.read_text(encoding="utf-8").splitlines()


def _upsert_env_line(key: str, value: str, lines: list[str]) -> list[str]:
    prefix = f"{key}="
    for idx, line in enumerate(lines):
        if line.startswith(prefix) or line.startswith(f"{key} ="):
            lines[idx] = f"{prefix}{value}"
            return lines
    if lines and lines[-1].strip():
        lines.append("")
    lines.append(f"{prefix}{value}")
    return lines


def _write_env_lines(lines: list[str]) -> None:
    _ENV_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


async def save_platform_keys(payload: dict[str, str], *, verify: bool = True) -> dict[str, Any]:
    """Validate (optional) and persist platform API keys to .env."""
    env_map = {
        "lunarcrush": "LUNARCRUSH_API_KEY",
        "LUNARCRUSH_API_KEY": "LUNARCRUSH_API_KEY",
        "coinmarketcal": "COINMARKETCAL_API_KEY",
        "COINMARKETCAL_API_KEY": "COINMARKETCAL_API_KEY",
        "debank": "DEBANK_API_KEY",
        "DEBANK_API_KEY": "DEBANK_API_KEY",
    }
    verify_fns = {
        "LUNARCRUSH_API_KEY": verify_lunarcrush,
        "COINMARKETCAL_API_KEY": verify_coinmarketcal,
        "DEBANK_API_KEY": verify_debank,
    }

    lines = _read_env_lines()
    saved: list[str] = []
    results: list[dict[str, Any]] = []

    for raw_key, value in payload.items():
        env_key = env_map.get(raw_key)
        if not env_key:
            continue
        token = (value or "").strip()
        if not token:
            continue
        check: dict[str, Any] = {"env": env_key, "saved": False}
        if verify:
            check = await verify_fns[env_key](token)
            check["env"] = env_key
            if not check.get("valid"):
                results.append(check)
                continue
        lines = _upsert_env_line(env_key, token, lines)
        os.environ[env_key] = token
        saved.append(env_key)
        check["saved"] = True
        results.append(check)

    if saved:
        _write_env_lines(lines)

    return {
        "timestamp": _utcnow(),
        "saved_count": len(saved),
        "saved_keys": saved,
        "results": results,
        "env_file": str(_ENV_PATH),
    }
