"""White-label tenant branding — configuration, exports, API branding, isolation."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("white_label.json")
_DATA_BASE = Path(__file__).resolve().parent / "data"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load() -> dict[str, Any]:
    if not _PATH.exists():
        return {"tenants": {}}
    try:
        return json.loads(_PATH.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return {"tenants": {}}


def _save(data: dict[str, Any]) -> None:
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def configure_brand(
    org_id: str,
    *,
    product_name: str,
    primary_color: str = "#0B1F33",
    logo_url: str = "",
    support_email: str = "",
    custom_domain: str = "",
    report_footer: str = "",
    api_title: str = "",
) -> dict[str, Any]:
    if not org_id or not product_name.strip():
        raise ValueError("org_id_and_product_name_required")
    with _LOCK:
        data = _load()
        row = {
            "org_id": org_id,
            "product_name": product_name.strip(),
            "primary_color": primary_color,
            "logo_url": logo_url,
            "support_email": support_email,
            "custom_domain": custom_domain,
            "report_footer": report_footer,
            "api_title": api_title or product_name.strip(),
            "updated_at": _utcnow(),
            "isolation": "org_id_scoped",
        }
        data.setdefault("tenants", {})[org_id] = row
        _save(data)
        return dict(row)


def get_brand(org_id: str) -> dict[str, Any] | None:
    return _load().get("tenants", {}).get(org_id)


def branded_report_export(org_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    brand = get_brand(org_id)
    if not brand:
        raise ValueError("white_label_not_configured")
    return {
        "org_id": org_id,
        "brand": brand,
        "payload": payload,
        "footer": brand.get("report_footer") or f"{brand['product_name']} confidential",
        "exported_at": _utcnow(),
    }


def white_label_status() -> dict[str, Any]:
    data = _load()
    return {
        "surface": "white_label",
        "tenants": len(data.get("tenants", {})),
        "product_complete": False,
        "features": [
            "tenant_branding",
            "configuration",
            "report_exports",
            "api_branding",
            "org_isolation",
        ],
    }
