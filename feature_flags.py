"""
BLACKDARK — Simple feature flag registry (multi-flag, env override).
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

import config

_LOCK = threading.Lock()
_FLAGS_PATH = config.DATA_DIR / "feature_flags.json"

_DEFAULT_FLAGS: dict[str, dict[str, Any]] = {
    "oracle_ml_enrichment": {"enabled": True, "description": "ML adjustment on unified oracle"},
    "auto_execution": {"enabled": False, "description": "Live auto-execution (default off)"},
    "arbitrage_scanner": {"enabled": True, "description": "Cross-exchange arb scanner"},
    "b2b_websocket_hub": {"enabled": True, "description": "B2B signed websocket feed"},
    "reconciliation_alerts": {"enabled": True, "description": "Binance reference reconciliation alerts"},
    "data_lineage_ui": {"enabled": True, "description": "Public data lineage visualization page"},
}


def _env_override(name: str) -> bool | None:
    key = f"FEATURE_FLAG_{name.upper()}"
    raw = os.getenv(key, "").strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return None


def _load() -> dict[str, dict[str, Any]]:
    if _FLAGS_PATH.exists():
        try:
            data = json.loads(_FLAGS_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged = dict(_DEFAULT_FLAGS)
                merged.update(data)
                return merged
        except Exception:
            pass
    return dict(_DEFAULT_FLAGS)


def _save(flags: dict[str, dict[str, Any]]) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    _FLAGS_PATH.write_text(json.dumps(flags, indent=2), encoding="utf-8")


def list_flags() -> dict[str, Any]:
    with _LOCK:
        flags = _load()
    out = {}
    for name, meta in flags.items():
        env = _env_override(name)
        out[name] = {
            **meta,
            "effective": env if env is not None else bool(meta.get("enabled")),
            "env_override": env,
        }
    return out


def is_enabled(name: str, *, default: bool = False) -> bool:
    env = _env_override(name)
    if env is not None:
        return env
    with _LOCK:
        flags = _load()
    meta = flags.get(name)
    if not meta:
        return default
    return bool(meta.get("enabled", default))


def set_flag(name: str, enabled: bool, *, description: str | None = None) -> dict[str, Any]:
    with _LOCK:
        flags = _load()
        row = dict(flags.get(name) or {})
        row["enabled"] = enabled
        if description:
            row["description"] = description
        flags[name] = row
        _save(flags)
    return list_flags()[name]
