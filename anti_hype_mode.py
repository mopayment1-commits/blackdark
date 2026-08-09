"""
BLACKDARK — Anti-Hype Mode (U7).

Institutional skin: evidence-only language, hide promo CTAs, keep proof links.
Completes Z5 Compliance Footer into a user-selectable product mode.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from path_safety import ensure_under, safe_data_file

_DATA = safe_data_file("anti_hype_mode.json")
_DATA_BASE = Path(__file__).resolve().parent / "data"

_HYPE_PATTERNS = [
    re.compile(r"\bguaranteed?\b", re.IGNORECASE),
    re.compile(r"\bsecret alpha\b", re.IGNORECASE),
    re.compile(r"\bto the moon\b", re.IGNORECASE),
    re.compile(r"\b100%\s*win\b", re.IGNORECASE),
    re.compile(r"\brisk[- ]free\b", re.IGNORECASE),
    re.compile(r"\bget rich\b", re.IGNORECASE),
]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load() -> dict[str, Any]:
    if not _DATA.exists():
        return {"default_enabled": False, "users": {}}
    try:
        return json.loads(_DATA.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"default_enabled": False, "users": {}}


def _save(store: dict[str, Any]) -> None:
    path = ensure_under(_DATA, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")  # NOSONAR pythonsecurity:S2083


def is_enabled(user_key: str | None = None, *, cookie_flag: bool | None = None) -> bool:
    if cookie_flag is not None:
        return bool(cookie_flag)
    store = _load()
    if user_key and user_key in store.get("users", {}):
        return bool(store["users"][user_key].get("enabled"))
    return bool(store.get("default_enabled"))


def set_mode(enabled: bool, *, user_key: str = "anon") -> dict[str, Any]:
    store = _load()
    users = store.setdefault("users", {})
    users[user_key or "anon"] = {
        "enabled": bool(enabled),
        "updated_at": _utcnow(),
    }
    _save(store)
    return build_anti_hype_mode(user_key=user_key or "anon", enabled=bool(enabled))


def strip_hype(text: str) -> str:
    out = str(text or "")
    for pat in _HYPE_PATTERNS:
        out = pat.sub("[claim removed — evidence mode]", out)
    return out


def filter_payload(payload: Any, *, enabled: bool) -> Any:
    """Recursively scrub hype strings when mode is on."""
    if not enabled:
        return payload
    if isinstance(payload, str):
        return strip_hype(payload)
    if isinstance(payload, list):
        return [filter_payload(x, enabled=True) for x in payload]
    if isinstance(payload, dict):
        return {k: filter_payload(v, enabled=True) for k, v in payload.items()}
    return payload


def build_anti_hype_mode(
    *,
    user_key: str = "anon",
    enabled: bool | None = None,
) -> dict[str, Any]:
    on = is_enabled(user_key) if enabled is None else bool(enabled)
    from decision_certificate import compliance_footer_block

    footer = compliance_footer_block(
        surface="anti_hype_mode",
        trust_basis="public_accuracy_ledger + kill_rate_board + audit_hash_chain",
    )
    return {
        "surface": "anti_hype_mode",
        "generated_at": _utcnow(),
        "enabled": on,
        "user_key": (user_key or "anon")[:64],
        "label": "Anti-Hype Mode",
        "promise": "Evidence only — hide promo noise, keep proof.",
        "when_on": {
            "show": [
                "/oracle-accuracy",
                "/kill-rate",
                "/contradiction-replay",
                "/corpus-passport",
                "/api/oracle/accuracy/public",
                "/api/public/kill-rate",
                "/b2b/committee-one-pager",
            ],
            "hide_promo_ctas": [
                "Start 7-Day Trial",
                "Upgrade hype banners",
                "guaranteed returns language",
            ],
            "body_class": "anti-hype-on",
            "cookie": "bd_anti_hype=1",
        },
        "compliance_footer": footer,
        "css_hooks": {
            "body_class": "anti-hype-on",
            "hide_selectors": [".promo-cta", ".pricing-card.popular .badge", "[data-hype]"],
            "show_selectors": [".bd-anti-hype", "[data-evidence]", "#kill-rate", "#ledger"],
        },
        "api": {
            "status": "/api/anti-hype/mode",
            "set": "POST /api/anti-hype/mode",
        },
        "page": "/anti-hype",
        "tier_surface": "all_especially_institutional",
        "disclaimer": footer["disclaimer"],
    }
