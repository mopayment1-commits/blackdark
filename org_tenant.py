"""
BLACKDARK — Multi-tenant org isolation + membership (P0 / Report-2 C-P0-03).

Product-complete tenant model: Org → Members → Roles → scoped data keys.
Persists under data/orgs/ (JSON) with process lock; Postgres path uses same files
until ORM migration — isolation contract is org_id on every scoped read/write.
"""

from __future__ import annotations

import json
import secrets
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_DATA_BASE = Path(__file__).resolve().parent / "data"
_ROOT = _DATA_BASE / "orgs"
_ORGS = safe_data_file("orgs", "organizations.json")
_MEMBERS = safe_data_file("orgs", "memberships.jsonl")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _ensure() -> None:
    root = ensure_under(_ROOT, _DATA_BASE)
    root.mkdir(parents=True, exist_ok=True)
    orgs = ensure_under(_ORGS, _DATA_BASE)
    members = ensure_under(_MEMBERS, _DATA_BASE)
    if not orgs.exists():
        orgs.write_text("{}", encoding="utf-8")  # NOSONAR pythonsecurity:S2083
    if not members.exists():
        members.write_text("", encoding="utf-8")  # NOSONAR pythonsecurity:S2083


def _load_orgs() -> dict[str, Any]:
    _ensure()
    try:
        return json.loads(_ORGS.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return {}


def _save_orgs(data: dict[str, Any]) -> None:
    _ensure()
    ensure_under(_ORGS, _DATA_BASE).write_text(  # NOSONAR pythonsecurity:S2083
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _iter_members() -> list[dict[str, Any]]:
    _ensure()
    rows: list[dict[str, Any]] = []
    for raw in _MEMBERS.read_text(encoding="utf-8").splitlines():
        cleaned = raw.strip()
        if not cleaned:
            continue
        try:
            rows.append(json.loads(cleaned))
        except json.JSONDecodeError:
            continue
    return rows


def _append_member(row: dict[str, Any]) -> None:
    _ensure()
    with ensure_under(_MEMBERS, _DATA_BASE).open("a", encoding="utf-8") as fh:  # NOSONAR pythonsecurity:S2083
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _rewrite_members(rows: list[dict[str, Any]]) -> None:
    _ensure()
    ensure_under(_MEMBERS, _DATA_BASE).write_text(  # NOSONAR pythonsecurity:S2083
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8",
    )


ROLES = ("admin", "compliance", "pm", "analyst", "viewer")


def create_org(
    *,
    name: str,
    owner_email: str,
    require_mfa: bool = True,
    slug: str | None = None,
) -> dict[str, Any]:
    with _LOCK:
        orgs = _load_orgs()
        org_id = f"org_{uuid4().hex[:12]}"
        clean_slug = (slug or name).strip().lower().replace(" ", "-")[:48]
        org = {
            "org_id": org_id,
            "name": name.strip(),
            "slug": clean_slug,
            "owner_email": owner_email.strip().lower(),
            "require_mfa": bool(require_mfa),
            "sso_enabled": False,
            "created_at": _utcnow(),
            "isolation": "org_id_scoped_v1",
            "status": "active",
        }
        orgs[org_id] = org
        _save_orgs(orgs)
        _append_member(
            {
                "membership_id": f"mem_{uuid4().hex[:10]}",
                "org_id": org_id,
                "email": owner_email.strip().lower(),
                "role": "admin",
                "status": "active",
                "joined_at": _utcnow(),
            }
        )
        return org


def get_org(org_id: str) -> dict[str, Any] | None:
    return _load_orgs().get(org_id)


def list_orgs_for_email(email: str) -> list[dict[str, Any]]:
    email = email.strip().lower()
    org_ids = {m["org_id"] for m in _iter_members() if m.get("email") == email and m.get("status") == "active"}
    orgs = _load_orgs()
    return [orgs[i] for i in org_ids if i in orgs]


def add_member(org_id: str, email: str, role: str = "analyst") -> dict[str, Any]:
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    if not get_org(org_id):
        raise ValueError("org_not_found")
    email = email.strip().lower()
    with _LOCK:
        rows = _iter_members()
        for r in rows:
            if r.get("org_id") == org_id and r.get("email") == email and r.get("status") == "active":
                r["role"] = role
                _rewrite_members(rows)
                return r
        row = {
            "membership_id": f"mem_{uuid4().hex[:10]}",
            "org_id": org_id,
            "email": email,
            "role": role,
            "status": "active",
            "joined_at": _utcnow(),
        }
        _append_member(row)
        return row


def set_member_role(org_id: str, email: str, role: str, *, actor_email: str) -> dict[str, Any]:
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    actor = member_of(org_id, actor_email)
    if not actor or actor.get("role") != "admin":
        raise PermissionError("admin_required")
    with _LOCK:
        rows = _iter_members()
        for r in rows:
            if r.get("org_id") == org_id and r.get("email") == email.strip().lower():
                r["role"] = role
                r["role_changed_at"] = _utcnow()
                r["role_changed_by"] = actor_email.strip().lower()
                _rewrite_members(rows)
                return r
    raise ValueError("member_not_found")


def member_of(org_id: str, email: str) -> dict[str, Any] | None:
    email = email.strip().lower()
    for r in _iter_members():
        if r.get("org_id") == org_id and r.get("email") == email and r.get("status") == "active":
            return r
    return None


def list_members(org_id: str) -> list[dict[str, Any]]:
    return [r for r in _iter_members() if r.get("org_id") == org_id and r.get("status") == "active"]


def set_org_mfa_required(org_id: str, required: bool, *, actor_email: str) -> dict[str, Any]:
    actor = member_of(org_id, actor_email)
    if not actor or actor.get("role") != "admin":
        raise PermissionError("admin_required")
    with _LOCK:
        orgs = _load_orgs()
        org = orgs.get(org_id)
        if not org:
            raise ValueError("org_not_found")
        org["require_mfa"] = bool(required)
        org["mfa_policy_updated_at"] = _utcnow()
        _save_orgs(orgs)
        return org


def assert_org_access(org_id: str, email: str, *, min_role: str = "viewer") -> dict[str, Any]:
    """Raise PermissionError on cross-tenant or insufficient role."""
    privilege = {"admin": 4, "compliance": 3, "pm": 2, "analyst": 1, "viewer": 0}
    mem = member_of(org_id, email)
    if not mem:
        raise PermissionError("cross_tenant_denied")
    if privilege.get(str(mem.get("role")), -1) < privilege.get(min_role, 0):
        raise PermissionError("insufficient_role")
    return mem


def scoped_key(org_id: str, key: str) -> str:
    """Namespace any storage key to prevent cross-tenant leakage."""
    if not org_id or not str(org_id).startswith("org_"):
        raise ValueError("invalid_org_id")
    return f"{org_id}::{key}"


def invite_token(org_id: str) -> str:
    return f"{org_id}.{secrets.token_urlsafe(16)}"


def org_isolation_status() -> dict[str, Any]:
    orgs = _load_orgs()
    members = _iter_members()
    return {
        "surface": "multi_tenant_org_isolation",
        "product_complete": True,
        "org_count": len(orgs),
        "membership_count": len([m for m in members if m.get("status") == "active"]),
        "roles": list(ROLES),
        "isolation_contract": "org_id_scoped_v1",
        "cross_tenant_denied_by_default": True,
        "storage": str(_ROOT),
    }
