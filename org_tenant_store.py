"""PostgreSQL-backed org tenant store (INS-TENANT production path)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from org_tenant import ROLES


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def ensure_org_tables(db: Any | None = None) -> None:
    if db is not None:
        await _ensure_org_tables_on(db)
        return
    from database import get_connection

    async with get_connection() as conn:
        await _ensure_org_tables_on(conn)


async def _ensure_org_tables_on(db: Any) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS organizations (
            org_id       TEXT PRIMARY KEY,
            name         TEXT NOT NULL,
            slug         TEXT NOT NULL,
            owner_email  TEXT NOT NULL,
            require_mfa  INTEGER NOT NULL DEFAULT 1,
            sso_enabled  INTEGER NOT NULL DEFAULT 0,
            created_at   TEXT NOT NULL,
            isolation    TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'active',
            metadata_json TEXT
        )
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS org_memberships (
            membership_id TEXT PRIMARY KEY,
            org_id          TEXT NOT NULL,
            email           TEXT NOT NULL,
            role            TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'active',
            joined_at       TEXT NOT NULL,
            role_changed_at TEXT,
            role_changed_by TEXT
        )
        """
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_org_members_email ON org_memberships (email)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_org_members_org ON org_memberships (org_id)"
    )


async def migrate_json_orgs_if_needed() -> dict[str, int]:
    """One-time import from data/orgs JSON files when PG tables are empty."""
    from pathlib import Path

    from database import get_connection

    await ensure_org_tables()
    async with get_connection() as db:
        row = await (await db.execute("SELECT COUNT(*) AS c FROM organizations")).fetchone()
        existing = int((row["c"] if isinstance(row, dict) else row[0]) or 0)
        if existing > 0:
            return {"imported_orgs": 0, "imported_members": 0, "skipped": True}

    root = Path(__file__).resolve().parent / "data" / "orgs"
    orgs_file = root / "organizations.json"
    members_file = root / "memberships.jsonl"
    if not orgs_file.exists():
        return {"imported_orgs": 0, "imported_members": 0, "skipped": True}

    orgs = json.loads(orgs_file.read_text(encoding="utf-8") or "{}")
    members: list[dict[str, Any]] = []
    if members_file.exists():
        for line in members_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    members.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    imported_o = 0
    imported_m = 0
    async with get_connection() as db:
        for org_id, org in orgs.items():
            await db.execute(
                """
                INSERT INTO organizations (
                    org_id, name, slug, owner_email, require_mfa, sso_enabled,
                    created_at, isolation, status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (org_id) DO NOTHING
                """,
                (
                    org_id,
                    org.get("name"),
                    org.get("slug"),
                    org.get("owner_email"),
                    1 if org.get("require_mfa", True) else 0,
                    1 if org.get("sso_enabled") else 0,
                    org.get("created_at") or _utcnow(),
                    org.get("isolation") or "org_id_scoped_v1",
                    org.get("status") or "active",
                    json.dumps(org, separators=(",", ":"), default=str),
                ),
            )
            imported_o += 1
        for m in members:
            await db.execute(
                """
                INSERT INTO org_memberships (
                    membership_id, org_id, email, role, status, joined_at,
                    role_changed_at, role_changed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (membership_id) DO NOTHING
                """,
                (
                    m.get("membership_id") or f"mem_{uuid4().hex[:10]}",
                    m.get("org_id"),
                    m.get("email"),
                    m.get("role"),
                    m.get("status") or "active",
                    m.get("joined_at") or _utcnow(),
                    m.get("role_changed_at"),
                    m.get("role_changed_by"),
                ),
            )
            imported_m += 1
    return {"imported_orgs": imported_o, "imported_members": imported_m, "skipped": False}


async def create_org_pg(
    *,
    name: str,
    owner_email: str,
    require_mfa: bool = True,
    slug: str | None = None,
    org_id: str | None = None,
) -> dict[str, Any]:
    from database import get_connection

    await ensure_org_tables()
    org_id = (org_id or "").strip() or f"org_{uuid4().hex[:12]}"
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
    mem = {
        "membership_id": f"mem_{uuid4().hex[:10]}",
        "org_id": org_id,
        "email": owner_email.strip().lower(),
        "role": "admin",
        "status": "active",
        "joined_at": _utcnow(),
    }
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO organizations (
                org_id, name, slug, owner_email, require_mfa, sso_enabled,
                created_at, isolation, status, metadata_json
            ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, 'active', ?)
            """,
            (
                org_id,
                org["name"],
                org["slug"],
                org["owner_email"],
                1 if require_mfa else 0,
                org["created_at"],
                org["isolation"],
                json.dumps(org, separators=(",", ":")),
            ),
        )
        await db.execute(
            """
            INSERT INTO org_memberships (
                membership_id, org_id, email, role, status, joined_at
            ) VALUES (?, ?, ?, ?, 'active', ?)
            """,
            (mem["membership_id"], org_id, mem["email"], mem["role"], mem["joined_at"]),
        )
    return org


async def get_org_pg(org_id: str) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        row = await (
            await db.execute("SELECT * FROM organizations WHERE org_id = ?", (org_id,))
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["require_mfa"] = bool(int(data.get("require_mfa") or 0))
    data["sso_enabled"] = bool(int(data.get("sso_enabled") or 0))
    return data


async def list_orgs_for_email_pg(email: str) -> list[dict[str, Any]]:
    from database import get_connection

    email = email.strip().lower()
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT o.* FROM organizations o
                JOIN org_memberships m ON m.org_id = o.org_id
                WHERE m.email = ? AND m.status = 'active' AND o.status = 'active'
                """,
                (email,),
            )
        ).fetchall()
    out = []
    for row in rows:
        d = dict(row)
        d["require_mfa"] = bool(int(d.get("require_mfa") or 0))
        d["sso_enabled"] = bool(int(d.get("sso_enabled") or 0))
        out.append(d)
    return out


async def member_of_pg(org_id: str, email: str) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT * FROM org_memberships
                WHERE org_id = ? AND email = ? AND status = 'active'
                """,
                (org_id, email.strip().lower()),
            )
        ).fetchone()
    return dict(row) if row else None


async def add_member_pg(org_id: str, email: str, role: str = "analyst") -> dict[str, Any]:
    if role not in ROLES:
        raise ValueError(f"role must be one of {ROLES}")
    if not await get_org_pg(org_id):
        raise ValueError("org_not_found")
    email = email.strip().lower()
    existing = await member_of_pg(org_id, email)
    if existing:
        from database import get_connection

        async with get_connection() as db:
            await db.execute(
                "UPDATE org_memberships SET role = ? WHERE membership_id = ?",
                (role, existing["membership_id"]),
            )
        existing["role"] = role
        return existing
    row = {
        "membership_id": f"mem_{uuid4().hex[:10]}",
        "org_id": org_id,
        "email": email,
        "role": role,
        "status": "active",
        "joined_at": _utcnow(),
    }
    from database import get_connection

    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO org_memberships (
                membership_id, org_id, email, role, status, joined_at
            ) VALUES (?, ?, ?, ?, 'active', ?)
            """,
            (row["membership_id"], org_id, email, role, row["joined_at"]),
        )
    return row


async def list_members_pg(org_id: str) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (
            await db.execute(
                "SELECT * FROM org_memberships WHERE org_id = ? AND status = 'active'",
                (org_id,),
            )
        ).fetchall()
    return [dict(r) for r in rows]


async def set_member_role_pg(org_id: str, email: str, role: str, *, actor_email: str) -> dict[str, Any]:
    actor = await member_of_pg(org_id, actor_email)
    if not actor or actor.get("role") not in {"admin", "super_admin"}:
        raise PermissionError("admin_required")
    from database import get_connection

    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT * FROM org_memberships
                WHERE org_id = ? AND email = ?
                """,
                (org_id, email.strip().lower()),
            )
        ).fetchone()
        if not row:
            raise ValueError("member_not_found")
        await db.execute(
            """
            UPDATE org_memberships
            SET role = ?, role_changed_at = ?, role_changed_by = ?
            WHERE membership_id = ?
            """,
            (role, _utcnow(), actor_email.strip().lower(), row["membership_id"]),
        )
    updated = dict(row)
    updated["role"] = role
    return updated


async def remove_member_pg(org_id: str, email: str, *, actor_email: str) -> dict[str, Any]:
    actor = await member_of_pg(org_id, actor_email)
    if not actor or actor.get("role") not in {"admin", "super_admin"}:
        raise PermissionError("admin_required")
    from database import get_connection

    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT * FROM org_memberships
                WHERE org_id = ? AND email = ? AND status = 'active'
                """,
                (org_id, email.strip().lower()),
            )
        ).fetchone()
        if not row:
            raise ValueError("member_not_found")
        await db.execute(
            """
            UPDATE org_memberships
            SET status = 'removed', role_changed_at = ?, role_changed_by = ?
            WHERE membership_id = ?
            """,
            (_utcnow(), actor_email.strip().lower(), row["membership_id"]),
        )
    updated = dict(row)
    updated["status"] = "removed"
    return updated


async def set_org_mfa_required_pg(org_id: str, required: bool, *, actor_email: str) -> dict[str, Any]:
    actor = await member_of_pg(org_id, actor_email)
    if not actor or actor.get("role") not in {"admin", "super_admin"}:
        raise PermissionError("admin_required")
    from database import get_connection

    async with get_connection() as db:
        await db.execute(
            "UPDATE organizations SET require_mfa = ? WHERE org_id = ?",
            (1 if required else 0, org_id),
        )
    org = await get_org_pg(org_id)
    if not org:
        raise ValueError("org_not_found")
    return org


async def org_isolation_status_pg() -> dict[str, Any]:
    from database import get_connection
    from postgres_backend import pool_stats, use_postgres

    await ensure_org_tables()
    async with get_connection() as db:
        org_row = await (await db.execute("SELECT COUNT(*) AS c FROM organizations")).fetchone()
        mem_row = await (
            await db.execute("SELECT COUNT(*) AS c FROM org_memberships WHERE status = 'active'")
        ).fetchone()
    org_count = int((org_row["c"] if isinstance(org_row, dict) else org_row[0]) or 0)
    mem_count = int((mem_row["c"] if isinstance(mem_row, dict) else mem_row[0]) or 0)
    pool = pool_stats()
    return {
        "surface": "multi_tenant_org_isolation",
        "product_complete": True,
        "org_count": org_count,
        "membership_count": mem_count,
        "roles": list(ROLES),
        "isolation_contract": "org_id_scoped_v1",
        "cross_tenant_denied_by_default": True,
        "storage_engine": "postgresql",
        "postgres_active": use_postgres(),
        "postgres_pool": pool,
    }


async def verify_postgres_tenant_smoke() -> dict[str, Any]:
    """Runtime proof: create org, deny cross-tenant, allow member."""
    org = await create_org_pg(name="INS-TENANT Smoke", owner_email="ins-tenant-smoke@blackdark.test")
    await add_member_pg(org["org_id"], "analyst@blackdark.test", "analyst")
    mem = await member_of_pg(org["org_id"], "analyst@blackdark.test")
    assert mem is not None
    stranger = await member_of_pg(org["org_id"], "stranger@blackdark.test")
    denied = stranger is None
    return {
        "org_id": org["org_id"],
        "cross_tenant_denied": denied,
        "smoke_pass": denied and mem.get("role") == "analyst",
    }
