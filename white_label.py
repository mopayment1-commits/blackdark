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
    # Exercise the real Super Terminal builder brand path (not a hand-built fake pack).
    from super_terminal import build_super_terminal

    terminal_pack = build_super_terminal(symbol="BTC/USDT", org_id=org_id)
    builder_invoked = isinstance(terminal_pack, dict) and "modules" in terminal_pack
    terminal = {
        "brand_applied": bool(terminal_pack.get("brand_applied")),
        "product_name": terminal_pack.get("product_name"),
        "api_title": terminal_pack.get("api_title"),
        "required_ok": bool(terminal_pack.get("required_ok")),
        "module_keys": list(terminal_pack.get("module_keys") or []),
        "surface": "super_terminal",
        "wiring": "build_super_terminal_applies_get_brand",
        "builder_invoked": bool(builder_invoked),
    }
    export = branded_report_export(
        org_id,
        {"kind": "status_snapshot", "ok": True, "modules": ["oms", "decision", "super_terminal"]},
    )
    # Multi-org isolation negative prove: peer org must not inherit this brand.
    peer_org = f"{org_id}_peer_isolation"
    peer_surface = apply_brand_to_surface(
        peer_org,
        {"surface": "institutional_status", "default_title": "BLACKDARK Institutional"},
    )
    isolation = {
        "ok": peer_surface.get("brand_applied") is False,
        "peer_org": peer_org,
        "peer_brand_applied": bool(peer_surface.get("brand_applied")),
        "peer_reason": peer_surface.get("reason"),
    }
    theme_tokens = {
        "product_name": brand.get("product_name"),
        "api_title": brand.get("api_title"),
        "primary_color": brand.get("primary_color"),
        "logo_url": brand.get("logo_url") or "",
        "css_vars": {
            "--bd-brand-primary": brand.get("primary_color"),
            "--bd-brand-name": brand.get("product_name"),
        },
    }
    portal = build_white_label_portal(org_id)
    ok = bool(
        surface.get("brand_applied")
        and export.get("brand", {}).get("product_name") == product_name
        and terminal.get("brand_applied") is True
        and terminal.get("product_name") == product_name
        and terminal.get("builder_invoked") is True
        and isolation.get("ok") is True
        and portal.get("ok") is True
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
            "module_keys": terminal.get("module_keys"),
            "builder_invoked": terminal.get("builder_invoked"),
            "wiring": terminal.get("wiring"),
            "surface": terminal.get("surface"),
        },
        "portal": {
            "ok": portal.get("ok"),
            "product_name": (portal.get("portal") or {}).get("product_name"),
            "hosted_custom_domain": (portal.get("portal") or {}).get("hosted_custom_domain"),
            "nav": (portal.get("portal") or {}).get("nav"),
            "modules": ((portal.get("portal") or {}).get("modules") or {}),
            "client_gateway_ok": bool(
                ((portal.get("portal") or {}).get("modules") or {})
                .get("client_gateway", {})
                .get("ok")
            ),
            "client_gateway_hosted": bool(
                ((portal.get("portal") or {}).get("modules") or {})
                .get("client_gateway", {})
                .get("hosted")
            ),
        },
        "isolation": isolation,
        "theme_tokens": theme_tokens,
        "export": {
            "footer": export.get("footer"),
            "product_name": (export.get("brand") or {}).get("product_name"),
            "exported_at": export.get("exported_at"),
        },
        "api_routes": [
            "GET /api/institutional/orgs/{org_id}/brand",
            "PUT /api/institutional/orgs/{org_id}/brand",
            "POST /api/institutional/orgs/{org_id}/brand/export",
            "GET /api/institutional/orgs/{org_id}/portal",
            "GET /api/institutional/orgs/{org_id}/terminal",
            "GET /api/institutional/orgs/{org_id}/exports",
            "GET /api/institutional/orgs/{org_id}/status",
            "GET /api/institutional/white-label/status",
            "POST /api/institutional/white-label/prove",
        ],
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "note": (
            "Tenant brand config + Super Terminal brand apply + export + org isolation proven. "
            "Not a full multi-tenant white-label portal / custom-domain hosting."
        ),
        "proved_at": _utcnow(),
    }


def _org_oms_snapshot(org_id: str) -> dict[str, Any]:
    """Org-scoped OMS counts for the portal pack — never claims live_fill."""
    try:
        from oms import list_orders

        rows = list_orders(org_id=org_id) or []
        if isinstance(rows, dict):
            rows = list(rows.values()) if rows else []
        n = len(rows) if isinstance(rows, list) else 0
        return {
            "ok": True,
            "org_id": org_id,
            "order_count": n,
            "live_fill": False,
            "note": "Portal snapshot only; live_fill remains externally blocked.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "org_id": org_id, "reason": type(exc).__name__, "live_fill": False}


def _org_decision_snapshot(org_id: str) -> dict[str, Any]:
    """Org-scoped decision e2e summary for the portal pack."""
    try:
        from decision_e2e import run_decision_e2e

        out = run_decision_e2e(org_id=org_id, notional=10_000.0)
        obj = (out or {}).get("decision_object") or {}
        return {
            "ok": bool((out or {}).get("ok")),
            "org_id": org_id,
            "executable": bool(obj.get("executable")),
            "learning_self_grade": bool(obj.get("learning_self_grade")),
            "graph_id": obj.get("graph_id"),
            "returns_source": ((obj.get("market_inputs") or {}).get("returns_source")),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "org_id": org_id, "reason": type(exc).__name__}


def build_white_label_portal(org_id: str) -> dict[str, Any]:
    """Served institutional white-label portal pack (not hosted custom-domain SaaS)."""
    brand = get_brand(org_id)
    if not brand:
        return {
            "ok": False,
            "org_id": org_id,
            "reason": "white_label_not_configured",
            "portal": None,
            "implementation_class": "PARTIAL",
            "product_complete": False,
            "verified_complete": False,
        }
    from super_terminal import build_super_terminal

    terminal = build_super_terminal(symbol="BTC/USDT", org_id=org_id)
    export = branded_report_export(
        org_id,
        {
            "kind": "portal_snapshot",
            "modules": list(terminal.get("module_keys") or []),
            "ok": bool(terminal.get("required_ok")),
        },
    )
    # Client gateway surface (in-process routes + session shape — not hosted SaaS).
    client_gateway = {
        "ok": True,
        "hosted": False,
        "session": {
            "org_id": org_id,
            "product_name": brand["product_name"],
            "isolation": brand.get("isolation") or "org_id_scoped",
            "auth": "org_scoped_api",
        },
        "routes": [
            {"method": "GET", "path": f"/orgs/{org_id}/portal", "surface": "portal_pack"},
            {"method": "GET", "path": f"/orgs/{org_id}/terminal", "surface": "super_terminal"},
            {"method": "POST", "path": f"/orgs/{org_id}/exports", "surface": "branded_export"},
            {"method": "GET", "path": f"/orgs/{org_id}/status", "surface": "branded_status"},
        ],
        "note": "Route map + session shape for tenant clients; not a public custom-domain portal.",
    }
    portal = {
        "org_id": org_id,
        "product_name": brand["product_name"],
        "api_title": brand.get("api_title") or brand["product_name"],
        "primary_color": brand.get("primary_color"),
        "logo_url": brand.get("logo_url") or "",
        "support_email": brand.get("support_email") or "",
        "custom_domain": brand.get("custom_domain") or "",
        "theme": {
            "css_vars": {
                "--bd-brand-primary": brand.get("primary_color"),
                "--bd-brand-name": brand["product_name"],
            }
        },
        "nav": [
            {"id": "terminal", "label": "Terminal"},
            {"id": "reports", "label": "Reports"},
            {"id": "status", "label": "Status"},
            {"id": "gateway", "label": "Client Gateway"},
        ],
        "modules": {
            "super_terminal": {
                "brand_applied": bool(terminal.get("brand_applied")),
                "required_ok": bool(terminal.get("required_ok")),
                "module_keys": list(terminal.get("module_keys") or []),
            },
            "export": {
                "footer": export.get("footer"),
                "product_name": (export.get("brand") or {}).get("product_name"),
            },
            "oms": _org_oms_snapshot(org_id),
            "decision": _org_decision_snapshot(org_id),
            "client_gateway": client_gateway,
        },
        "isolation": brand.get("isolation") or "org_id_scoped",
        "hosted_custom_domain": False,
        "note": "In-process portal pack — not external multi-tenant hosting.",
    }
    return {
        "ok": bool(portal["modules"]["super_terminal"]["brand_applied"]),
        "org_id": org_id,
        "portal": portal,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "verified_complete": False,
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
            "portal_pack",
            "client_gateway_route_map",
        ],
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "note": (
            "PARTIAL — brand API + Super Terminal apply + portal pack + client gateway "
            "route map; not hosted custom-domain multi-tenant SaaS."
        ),
    }
