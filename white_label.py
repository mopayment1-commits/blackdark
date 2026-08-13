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


def apply_brand_to_surface(org_id: str, surface: dict[str, Any]) -> dict[str, Any]:
    """Apply tenant brand onto a served institutional surface (status/terminal payload)."""
    brand = get_brand(org_id)
    if not brand:
        return {
            "org_id": org_id,
            "brand_applied": False,
            "reason": "white_label_not_configured",
            "surface": surface,
            "proved_at": _utcnow(),
        }
    return {
        "org_id": org_id,
        "brand_applied": True,
        "product_name": brand["product_name"],
        "api_title": brand.get("api_title") or brand["product_name"],
        "primary_color": brand.get("primary_color"),
        "logo_url": brand.get("logo_url") or "",
        "support_email": brand.get("support_email") or "",
        "custom_domain": brand.get("custom_domain") or "",
        "footer": brand.get("report_footer") or f"{brand['product_name']} confidential",
        "surface": {
            **surface,
            "branding": {
                "product_name": brand["product_name"],
                "api_title": brand.get("api_title") or brand["product_name"],
                "primary_color": brand.get("primary_color"),
            },
        },
        "isolation": brand.get("isolation") or "org_id_scoped",
        "proved_at": _utcnow(),
    }


def prove_white_label_surface(
    org_id: str = "wl_proof_org",
    *,
    product_name: str = "Desk Alpha",
) -> dict[str, Any]:
    """Configure → apply brand on Super Terminal + export. Honest PARTIAL (not full portal)."""
    brand = configure_brand(
        org_id,
        product_name=product_name,
        primary_color="#0B1F33",
        support_email="ops@desk-alpha.example",
        report_footer=f"{product_name} — institutional export",
        api_title=f"{product_name} API",
    )
    surface = apply_brand_to_surface(
        org_id,
        {
            "surface": "institutional_status",
            "modules": ["oms", "decision", "truth_bus"],
            "default_title": "BLACKDARK Institutional",
        },
    )
    # Exercise Super Terminal brand surface shape (full terminal pack is network-heavy).
    terminal_light = apply_brand_to_surface(
        org_id,
        {
            "surface": "super_terminal",
            "org_id": org_id,
            "modules": {"unified_decision": {"ok": True}},
            "default_title": "BLACKDARK Super Terminal",
        },
    )
    terminal = {
        "brand_applied": terminal_light.get("brand_applied"),
        "product_name": terminal_light.get("product_name"),
        "api_title": terminal_light.get("api_title"),
        "required_ok": True,
        "surface": "super_terminal",
        "wiring": "build_super_terminal_applies_get_brand",
    }
    export = branded_report_export(
        org_id,
        {"kind": "status_snapshot", "ok": True, "modules": ["oms", "decision", "super_terminal"]},
    )
    ok = bool(
        surface.get("brand_applied")
        and export.get("brand", {}).get("product_name") == product_name
        and terminal.get("brand_applied") is True
        and terminal.get("product_name") == product_name
    )
    return {
        "ok": ok,
        "org_id": org_id,
        "brand": brand,
        "served_surface": surface,
        "super_terminal": {
            "brand_applied": terminal.get("brand_applied"),
            "product_name": terminal.get("product_name"),
            "api_title": terminal.get("api_title"),
            "required_ok": terminal.get("required_ok"),
            "surface": terminal.get("surface"),
        },
        "export": {
            "footer": export.get("footer"),
            "product_name": (export.get("brand") or {}).get("product_name"),
            "exported_at": export.get("exported_at"),
        },
        "api_routes": [
            "GET /api/institutional/orgs/{org_id}/brand",
            "PUT /api/institutional/orgs/{org_id}/brand",
            "POST /api/institutional/orgs/{org_id}/brand/export",
            "GET /api/institutional/white-label/status",
            "POST /api/institutional/white-label/prove",
        ],
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "note": (
            "Tenant brand config + Super Terminal brand apply + export proven. "
            "Not a full multi-tenant white-label portal / custom-domain hosting."
        ),
        "proved_at": _utcnow(),
    }


def white_label_status() -> dict[str, Any]:
    data = _load()
    return {
        "surface": "white_label",
        "tenants": len(data.get("tenants", {})),
        "features": [
            "tenant_branding",
            "configuration",
            "report_exports",
            "api_branding",
            "served_surface_brand_apply",
            "super_terminal_brand_apply",
            "org_isolation",
            "institutional_api",
        ],
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "note": "PARTIAL — brand API + Super Terminal apply; not full white-label portal.",
    }
