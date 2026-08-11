"""
BLACKDARK — Exchange API keys for live auto-execution (Priority #2).

Reads keys/exchange_keys.env — verifies Binance, updates .env, enables dry-run or live.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import aiohttp

ROOT = Path(__file__).resolve().parent
KEYS_DIR = ROOT / "keys"
KEYS_FILE = KEYS_DIR / "exchange_keys.env"
KEYS_EXAMPLE = KEYS_DIR / "exchange_keys.env.example"
_ENV_PATH = ROOT / ".env"

_EXEC_ENV_KEYS = (
    "BINANCE_API_KEY",
    "BINANCE_API_SECRET",
    "BINANCE_TESTNET",
    "AUTO_EXECUTION_ENABLED",
    "AUTO_EXECUTION_DRY_RUN",
    "AUTO_EXECUTION_LOOP",
    "AUTO_EXECUTION_INTERVAL_SEC",
    "AUTO_EXECUTION_MIN_PROFIT_USDT",
    "AUTO_EXECUTION_QUOTE_USD",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def ensure_keys_file() -> Path:
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    if not KEYS_FILE.exists():
        if KEYS_EXAMPLE.exists():
            shutil.copy(KEYS_EXAMPLE, KEYS_FILE)
        else:
            KEYS_FILE.write_text(
                "BINANCE_API_KEY=\nBINANCE_API_SECRET=\nAUTO_EXECUTION_DRY_RUN=true\n",
                encoding="utf-8",
            )
    return KEYS_FILE


def parse_exchange_keys_file(path: Path | None = None) -> dict[str, str]:
    target = path or KEYS_FILE
    if not target.exists():
        return {}
    out: dict[str, str] = {}
    for raw in target.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key in _EXEC_ENV_KEYS and value:
            out[key] = value
    return out


def apply_exchange_keys_to_env() -> int:
    count = 0
    for key, value in parse_exchange_keys_file().items():
        os.environ[key] = value
        count += 1
    return count


def _read_env_lines() -> list[str]:
    if not _ENV_PATH.exists():
        example = ROOT / ".env.example"
        return example.read_text(encoding="utf-8").splitlines() if example.exists() else ["# BLACKDARK"]
    return _ENV_PATH.read_text(encoding="utf-8").splitlines()


def _upsert_env_line(key: str, value: str, lines: list[str]) -> list[str]:
    prefix = f"{key}="
    for idx, line in enumerate(lines):
        if line.startswith((prefix, f"{key} =")):
            lines[idx] = f"{prefix}{value}"
            return lines
    if lines and lines[-1].strip():
        lines.append("")
    lines.append(f"{prefix}{value}")
    return lines


def _write_env_lines(lines: list[str]) -> None:
    env_path = ROOT / ".env"
    env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def save_exchange_keys_to_env(parsed: dict[str, str]) -> None:
    """Persist execution flags to .env — refuse writing secrets in production."""
    prod = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "")).lower() in {
        "production",
        "prod",
        "live",
    }
    secret_keys = {
        "BINANCE_API_KEY",
        "BINANCE_API_SECRET",
        "OKX_API_KEY",
        "OKX_API_SECRET",
        "OKX_PASSPHRASE",
    }
    lines = _read_env_lines()
    for key, value in parsed.items():
        if key not in _EXEC_ENV_KEYS:
            continue
        if prod and key in secret_keys:
            # Keep secrets in process env / vault file only — never rewrite .env in prod
            os.environ[key] = value
            continue
        lines = _upsert_env_line(key, value, lines)
        os.environ[key] = value
    _write_env_lines(lines)


def _binance_base_url() -> str:
    testnet = os.getenv("BINANCE_TESTNET", "false").lower() in {"1", "true", "yes"}
    return "https://testnet.binance.vision" if testnet else "https://api.binance.com"


def _sign_params(secret: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urlencode(params)
    signed = dict(params)
    signed["signature"] = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    return signed


async def _binance_withdraw_permission(
    session: aiohttp.ClientSession,
    secret: str,
    headers: dict[str, str],
    current: bool,
) -> bool:
    try:
        perm_params = _sign_params(secret, {"timestamp": int(time.time() * 1000)})
        perm_url = f"{_binance_base_url()}/sapi/v1/account/apiRestrictions"
        async with session.get(perm_url, params=perm_params, headers=headers) as perm_resp:
            if perm_resp.status != 200:
                return current
            perms = await perm_resp.json()
            if not isinstance(perms, dict):
                return current
            # Explicit withdraw enable flags from Binance
            if "enableWithdrawals" in perms:
                return bool(perms.get("enableWithdrawals"))
            if "ipRestrict" in perms and perms.get("enableWithdrawals") is False:
                return False
    except Exception:
        pass
    return current


async def verify_binance_keys(
    api_key: str | None = None,
    api_secret: str | None = None,
) -> dict[str, Any]:
    key = (api_key or os.getenv("BINANCE_API_KEY", "")).strip()
    secret = (api_secret or os.getenv("BINANCE_API_SECRET", "")).strip()
    if not key or not secret:
        return {
            "exchange": "binance",
            "configured": False,
            "valid": False,
            "reason": "BINANCE_API_KEY / BINANCE_API_SECRET not set",
        }

    params = _sign_params(secret, {"timestamp": int(time.time() * 1000)})
    url = f"{_binance_base_url()}/api/v3/account"
    headers = {"X-MBX-APIKEY": key}
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params, headers=headers) as resp:
                data = await resp.json()
                if resp.status == 200:
                    # Spot account exposes canTrade / canWithdraw / canDeposit.
                    # Also probe API key permissions endpoint when available.
                    can_withdraw = bool(data.get("canWithdraw"))
                    can_withdraw = await _binance_withdraw_permission(session, secret, headers, can_withdraw)
                    return {
                        "exchange": "binance",
                        "configured": True,
                        "valid": True,
                        "can_trade": bool(data.get("canTrade")),
                        "can_withdraw": can_withdraw,
                        "can_deposit": bool(data.get("canDeposit")),
                        "testnet": _binance_base_url().endswith("vision"),
                        "message": "ok",
                    }
                return {
                    "exchange": "binance",
                    "configured": True,
                    "valid": False,
                    "http_status": resp.status,
                    "message": str(data.get("msg") or data)[:120],
                }
    except aiohttp.ClientError as exc:
        return {
            "exchange": "binance",
            "configured": True,
            "valid": False,
            "message": str(exc)[:120],
        }


def execution_keys_status() -> dict[str, Any]:
    parsed = parse_exchange_keys_file()
    dry_run = os.getenv("AUTO_EXECUTION_DRY_RUN", "true").lower() in {"1", "true", "yes"}
    live_flag = os.getenv("AUTO_EXECUTION_ENABLED", "false").lower() in {"1", "true", "yes"}
    has_keys = bool(
        parsed.get("BINANCE_API_KEY") or os.getenv("BINANCE_API_KEY")
    ) and bool(parsed.get("BINANCE_API_SECRET") or os.getenv("BINANCE_API_SECRET"))
    if live_flag and has_keys and not dry_run:
        mode = "live"
    elif dry_run:
        mode = "dry_run"
    else:
        mode = "off"

    return {
        "timestamp": _utcnow(),
        "keys_file": str(KEYS_FILE),
        "has_binance_keys": has_keys,
        "auto_execution_dry_run": dry_run,
        "auto_execution_live_flag": live_flag,
        "mode": mode,
        "binance_testnet": os.getenv("BINANCE_TESTNET", "false"),
        "setup_script": "python scripts/activate_live_execution.py",
    }


def _prepare_execution_config(parsed: dict[str, str], *, enable_live: bool, enable_auto_loop: bool) -> None:
    if not parsed.get("AUTO_EXECUTION_DRY_RUN"):
        parsed["AUTO_EXECUTION_DRY_RUN"] = "true" if not enable_live else "false"
    if enable_auto_loop:
        parsed.setdefault("AUTO_EXECUTION_LOOP", "true")
        parsed.setdefault("AUTO_EXECUTION_INTERVAL_SEC", "5")
    parsed.setdefault("AUTO_EXECUTION_MIN_PROFIT_USDT", "0.25")
    parsed.setdefault("AUTO_EXECUTION_QUOTE_USD", "100")


def _apply_live_mode(parsed: dict[str, str], *, enable_live: bool, has_keys: bool, verify_result: dict[str, Any] | None) -> bool:
    if enable_live and has_keys and verify_result and verify_result.get("valid"):
        parsed["AUTO_EXECUTION_ENABLED"] = "true"
        parsed["AUTO_EXECUTION_DRY_RUN"] = "false"
        return True
    parsed["AUTO_EXECUTION_ENABLED"] = "false"
    if enable_live and has_keys:
        parsed["AUTO_EXECUTION_DRY_RUN"] = "true"
    elif "AUTO_EXECUTION_DRY_RUN" not in parsed:
        parsed["AUTO_EXECUTION_DRY_RUN"] = "true"
    return False


async def _persist_execution_state(parsed: dict[str, str]) -> bool:
    auto_on = parsed.get("AUTO_EXECUTION_LOOP", "true").lower() in {"1", "true", "yes"}
    try:
        from database import init_db, set_execution_state

        await init_db()
        await set_execution_state(auto_execution_enabled=auto_on, panic_active=False)
    except Exception:
        pass
    return auto_on


async def activate_live_execution(
    *,
    enable_live: bool = False,
    enable_auto_loop: bool = True,
    verify: bool = True,
) -> dict[str, Any]:
    """
    Import keys/exchange_keys.env → .env.
    Default: dry-run auto-execution ON (safe). Live only if enable_live + valid keys.
    """
    ensure_keys_file()
    parsed = parse_exchange_keys_file()
    _prepare_execution_config(parsed, enable_live=enable_live, enable_auto_loop=enable_auto_loop)

    verify_result: dict[str, Any] | None = None
    has_keys = bool(parsed.get("BINANCE_API_KEY") and parsed.get("BINANCE_API_SECRET"))

    if has_keys and verify:
        verify_result = await verify_binance_keys(
            parsed.get("BINANCE_API_KEY"),
            parsed.get("BINANCE_API_SECRET"),
        )

    _apply_live_mode(parsed, enable_live=enable_live, has_keys=has_keys, verify_result=verify_result)

    save_exchange_keys_to_env(parsed)
    auto_on = await _persist_execution_state(parsed)

    mode = "live" if parsed.get("AUTO_EXECUTION_ENABLED") == "true" else "dry_run"
    msg = {
        "live": "Live execution enabled — real Binance orders",
        "dry_run": "Auto-execution enabled — dry-run mode (safe, no real funds)",
    }[mode]

    return {
        "timestamp": _utcnow(),
        "mode": mode,
        "message": msg,
        "verify": verify_result,
        "saved_keys": list(parsed.keys()),
        "keys_file": str(KEYS_FILE),
        "auto_execution_enabled": auto_on,
        "disclaimer": (
            "Live depends on Binance API latency. Panic Stop is always available. "
            "Not financial advice."
        ),
    }
