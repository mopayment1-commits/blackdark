"""SCIM 2.0 User/Group provisioning — real persistence, not a 501 stub."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("scim_store.json")
_DATA_BASE = Path(__file__).resolve().parent / "data"

SCIM_SCHEMA_USER = "urn:ietf:params:scim:schemas:core:2.0:User"
SCIM_SCHEMA_GROUP = "urn:ietf:params:scim:schemas:core:2.0:Group"
SCIM_SCHEMA_LIST = "urn:ietf:params:scim:api:messages:2.0:ListResponse"
SCIM_SCHEMA_ERROR = "urn:ietf:params:scim:api:messages:2.0:Error"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load() -> dict[str, Any]:
    if not _PATH.exists():
        return {"users": {}, "groups": {}}
    try:
        return json.loads(_PATH.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return {"users": {}, "groups": {}}


def _save(data: dict[str, Any]) -> None:
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def scim_env_bearer_configured() -> bool:
    import os

    return bool(os.getenv("SCIM_BEARER_TOKEN", "").strip())


def scim_bearer_configured() -> bool:
    if scim_env_bearer_configured():
        return True
    try:
        from org_tenant import _load_orgs

        return any(bool(o.get("scim_key_hash")) for o in _load_orgs().values())
    except Exception:
        return False


def scim_ready() -> bool:
    """Ready when env bearer OR an org-scoped SCIM key has been issued."""
    return scim_bearer_configured()


def scim_status() -> dict[str, Any]:
    data = _load()
    bearer = scim_bearer_configured()
    env_bearer = scim_env_bearer_configured()
    return {
        "surface": "scim",
        "implemented": True,
        "scim_ready": bearer,
        "bearer_configured": bearer,
        "product_complete": env_bearer,
        "users": len(data.get("users", {})),
        "groups": len(data.get("groups", {})),
        "endpoints": [
            "GET /api/institutional/scim/v2/Users",
            "POST /api/institutional/scim/v2/Users",
            "GET /api/institutional/scim/v2/Users/{id}",
            "PATCH /api/institutional/scim/v2/Users/{id}",
            "DELETE /api/institutional/scim/v2/Users/{id}",
            "GET /api/institutional/scim/v2/Groups",
            "POST /api/institutional/scim/v2/Groups",
        ],
        "note": (
            "SCIM User/Group CRUD implemented. Ready when SCIM_BEARER_TOKEN is set "
            "or an org issues a hashed bd_scim_ key (plaintext once)."
        ),
    }


def require_scim_bearer(authorization: str | None) -> dict[str, Any] | None:
    """Fail closed SCIM API calls without matching env or org-scoped bearer."""
    import hmac
    import os

    if not authorization or not authorization.lower().startswith("bearer "):
        raise PermissionError("scim_unauthorized")
    got = authorization.split(" ", 1)[1].strip()
    expected = os.getenv("SCIM_BEARER_TOKEN", "").strip()
    if expected and len(got) == len(expected) and hmac.compare_digest(got, expected):
        return {"scope": "env"}
    try:
        from org_tenant import verify_org_scim_key

        hit = verify_org_scim_key(got)
    except Exception:
        hit = None
    if hit:
        return {"scope": "org", **hit}
    raise PermissionError("scim_unauthorized")


def _user_resource(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemas": [SCIM_SCHEMA_USER],
        "id": row["id"],
        "externalId": row.get("external_id") or row["id"],
        "userName": row["user_name"],
        "name": {"formatted": row.get("display_name") or row["user_name"]},
        "displayName": row.get("display_name") or row["user_name"],
        "emails": [{"value": row["email"], "primary": True, "type": "work"}],
        "active": bool(row.get("active", True)),
        "meta": {
            "resourceType": "User",
            "created": row["created_at"],
            "lastModified": row["updated_at"],
        },
        "urn:blackdark:params:scim:schemas:extension:tenant:2.0:User": {
            "org_id": row["org_id"],
            "role": row.get("role") or "analyst",
        },
    }


def create_user(
    *,
    org_id: str,
    user_name: str,
    email: str,
    display_name: str = "",
    role: str = "analyst",
    external_id: str = "",
    active: bool = True,
) -> dict[str, Any]:
    email = email.strip().lower()
    user_name = user_name.strip()
    if not org_id or not user_name or not email:
        raise ValueError("org_id_userName_email_required")
    with _LOCK:
        data = _load()
        for u in data.get("users", {}).values():
            if u.get("org_id") == org_id and (
                u.get("user_name") == user_name or u.get("email") == email
            ):
                raise ValueError("scim_user_conflict")
        uid = f"scim_u_{uuid.uuid4().hex[:16]}"
        now = _utcnow()
        row = {
            "id": uid,
            "org_id": org_id,
            "user_name": user_name,
            "email": email,
            "display_name": display_name or user_name,
            "role": role,
            "external_id": external_id or uid,
            "active": active,
            "created_at": now,
            "updated_at": now,
        }
        data.setdefault("users", {})[uid] = row
        _save(data)
        # Mirror into org membership
        try:
            from org_tenant import add_member, get_org

            if get_org(org_id):
                add_member(org_id, email, role=role if role in {"admin", "compliance", "pm", "analyst", "viewer"} else "analyst")
        except Exception:
            pass
        return _user_resource(row)


def get_user(user_id: str, *, org_id: str | None = None) -> dict[str, Any] | None:
    row = _load().get("users", {}).get(user_id)
    if not row:
        return None
    if org_id and row.get("org_id") != org_id:
        return None
    return _user_resource(row)


def list_users(*, org_id: str, filter_expr: str = "", start_index: int = 1, count: int = 100) -> dict[str, Any]:
    users = [u for u in _load().get("users", {}).values() if u.get("org_id") == org_id]
    if filter_expr:
        # Minimal RFC7644 filter: userName eq "x" / emails eq "x"
        needle = filter_expr.lower()
        filtered = []
        for u in users:
            blob = f"{u.get('user_name','')} {u.get('email','')}".lower()
            if "eq" in needle:
                # extract quoted value
                import re

                m = re.search(r'"([^"]+)"', filter_expr)
                if m and m.group(1).lower() in blob:
                    filtered.append(u)
            elif needle in blob:
                filtered.append(u)
        users = filtered
    start = max(1, int(start_index)) - 1
    page = users[start : start + max(1, int(count))]
    return {
        "schemas": [SCIM_SCHEMA_LIST],
        "totalResults": len(users),
        "startIndex": start + 1,
        "itemsPerPage": len(page),
        "Resources": [_user_resource(u) for u in page],
    }


def patch_user(user_id: str, *, org_id: str, operations: list[dict[str, Any]]) -> dict[str, Any]:
    with _LOCK:
        data = _load()
        row = data.get("users", {}).get(user_id)
        if not row or row.get("org_id") != org_id:
            raise ValueError("scim_user_not_found")
        for op in operations:
            path = str(op.get("path") or "").lower()
            value = op.get("value")
            op_name = str(op.get("op") or "replace").lower()
            if op_name not in {"replace", "add", "remove"}:
                raise ValueError("scim_op_unsupported")
            if path in {"active", ""} and isinstance(value, dict) and "active" in value:
                row["active"] = bool(value["active"])
            elif path == "active":
                row["active"] = bool(value)
            elif path in {"displayname", "name.formatted"}:
                row["display_name"] = str(value)
            elif path == "emails" and isinstance(value, list) and value:
                row["email"] = str(value[0].get("value") or row["email"]).lower()
            elif op_name == "remove" and path == "active":
                row["active"] = False
        row["updated_at"] = _utcnow()
        data["users"][user_id] = row
        _save(data)
        return _user_resource(row)


def delete_user(user_id: str, *, org_id: str) -> None:
    with _LOCK:
        data = _load()
        row = data.get("users", {}).get(user_id)
        if not row or row.get("org_id") != org_id:
            raise ValueError("scim_user_not_found")
        del data["users"][user_id]
        _save(data)


def create_group(*, org_id: str, display_name: str, members: list[str] | None = None) -> dict[str, Any]:
    if not display_name.strip():
        raise ValueError("display_name_required")
    with _LOCK:
        data = _load()
        gid = f"scim_g_{uuid.uuid4().hex[:16]}"
        now = _utcnow()
        row = {
            "id": gid,
            "org_id": org_id,
            "display_name": display_name.strip(),
            "members": list(members or []),
            "created_at": now,
            "updated_at": now,
        }
        data.setdefault("groups", {})[gid] = row
        _save(data)
        return {
            "schemas": [SCIM_SCHEMA_GROUP],
            "id": gid,
            "displayName": row["display_name"],
            "members": [{"value": m} for m in row["members"]],
            "meta": {"resourceType": "Group", "created": now, "lastModified": now},
        }


def list_groups(*, org_id: str) -> dict[str, Any]:
    groups = [g for g in _load().get("groups", {}).values() if g.get("org_id") == org_id]
    resources = [
        {
            "schemas": [SCIM_SCHEMA_GROUP],
            "id": g["id"],
            "displayName": g["display_name"],
            "members": [{"value": m} for m in g.get("members") or []],
        }
        for g in groups
    ]
    return {
        "schemas": [SCIM_SCHEMA_LIST],
        "totalResults": len(resources),
        "Resources": resources,
    }


def scim_error(detail: str, status: int = 400) -> dict[str, Any]:
    return {
        "schemas": [SCIM_SCHEMA_ERROR],
        "detail": detail,
        "status": str(status),
    }
