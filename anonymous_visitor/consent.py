"""Privacy/consent boundary — AV §15."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

_CONSENT_PATH = Path("data/anonymous_consent_preferences.json")
_LOCK = threading.Lock()
_DEFAULT = {"essential_only": True, "optional_analytics": False, "optional_marketing": False}


def _load() -> dict[str, dict[str, Any]]:
    if not _CONSENT_PATH.is_file():
        return {}
    try:
        return json.loads(_CONSENT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict[str, dict[str, Any]]) -> None:
    _CONSENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONSENT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def consent_status(*, visitor_key: str) -> dict[str, Any]:
    with _LOCK:
        prefs = _load().get(visitor_key, dict(_DEFAULT))
    return {
        "ok": True,
        "visitor_key": visitor_key,
        "preferences": prefs,
        "essential_only_before_consent": True,
        "reject_as_easy_as_accept": True,
        "no_preticked_optional": True,
        "no_browsing_as_consent": True,
    }


def update_consent(*, visitor_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    prefs = {
        "essential_only": bool(payload.get("essential_only", True)),
        "optional_analytics": bool(payload.get("optional_analytics", False)),
        "optional_marketing": bool(payload.get("optional_marketing", False)),
        "rejected_optional": bool(payload.get("rejected_optional", False)),
    }
    with _LOCK:
        data = _load()
        data[visitor_key] = prefs
        _save(data)
    return consent_status(visitor_key=visitor_key)


def optional_tracking_allowed(*, visitor_key: str) -> bool:
    prefs = _load().get(visitor_key, _DEFAULT)
    return bool(prefs.get("optional_analytics"))
