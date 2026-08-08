"""Auto-import platform API keys from keys/platform_keys.env — zero prompts."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
KEYS_DIR = ROOT / "keys"
KEYS_FILE = KEYS_DIR / "platform_keys.env"
KEYS_EXAMPLE = KEYS_DIR / "platform_keys.env.example"

_ENV_TO_ID = {
    "LUNARCRUSH_API_KEY": "lunarcrush",
    "COINMARKETCAL_API_KEY": "coinmarketcal",
    "DEBANK_API_KEY": "debank",
}


def ensure_keys_file() -> Path:
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    if not KEYS_FILE.exists():
        if KEYS_EXAMPLE.exists():
            shutil.copy(KEYS_EXAMPLE, KEYS_FILE)
        else:
            KEYS_FILE.write_text(
                "# الصق المفاتيح هنا ثم احفظ — أو اتركها فارغة للوضع المجاني\n"
                "LUNARCRUSH_API_KEY=\n"
                "COINMARKETCAL_API_KEY=\n"
                "DEBANK_API_KEY=\n",
                encoding="utf-8",
            )
    return KEYS_FILE


def parse_keys_file(path: Path | None = None) -> dict[str, str]:
    """Read KEY=value lines; returns env var names -> values."""
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
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in _ENV_TO_ID and value:
            out[key] = value
    return out


def payload_from_env_file(path: Path | None = None) -> dict[str, str]:
    return {_ENV_TO_ID[k]: v for k, v in parse_keys_file(path).items()}


async def auto_import_keys(*, verify: bool = True, silent: bool = False) -> dict[str, Any]:
    """
    Import keys from keys/platform_keys.env into .env.
    If file empty — free-tier mode (no keys required).
    """
    from bd_platform.key_manager import keys_status, save_platform_keys, verify_all_keys

    ensure_keys_file()
    parse_keys_file()
    payload = payload_from_env_file()

    if not payload:
        status = keys_status()
        return {
            "mode": "free",
            "message": "الوضع المجاني — لا حاجة لمفاتيح. socialtickers + DeFiLlama + Tracely يعملون تلقائياً.",
            "keys_file": str(KEYS_FILE),
            "configured_count": status["configured_count"],
            "free_sources": [
                "LunarCrush → socialtickers.com",
                "CoinMarketCal → DeFiLlama + CoinGecko",
                "DeBank → Tracely portfolio",
            ],
        }

    result = await save_platform_keys(payload, verify=verify)
    verify_report = await verify_all_keys()
    return {
        "mode": "keys",
        "keys_file": str(KEYS_FILE),
        "import": result,
        "verify": verify_report,
        "message": f"تم استيراد {result.get('saved_count', 0)} مفتاح من {KEYS_FILE.name}",
    }


def apply_keys_to_process_env() -> int:
    """Load keys file into os.environ (sync, no verify). Returns count applied."""
    count = 0
    for key, value in parse_keys_file().items():
        os.environ[key] = value
        count += 1
    return count
