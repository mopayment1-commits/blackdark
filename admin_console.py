"""Admin console — site health probes, user admin, audit reads (DB-backed)."""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import UTC, datetime
from typing import Any
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from billing.plan_registry import normalize_plan


def _base_url() -> str:
    return (os.getenv("APP_BASE_URL") or os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")


def probe_surface(path: str, timeout: float = 8.0) -> dict[str, Any]:
    base = _base_url()
    if not base:
        return {"path": path, "ok": False, "status": None, "ms": None, "error": "APP_BASE_URL unset"}
    url = f"{base}{path}"
    t0 = time.perf_counter()
    try:
        req = urlrequest.Request(url, headers={"User-Agent": "BLACKDARK-admin-health/1.0", "Accept": "text/html"})
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            code = int(getattr(resp, "status", 200) or 200)
            ok = 200 <= code < 400
            ms = int((time.perf_counter() - t0) * 1000)
            return {"path": path, "ok": ok, "status": code, "ms": ms, "error": None}
    except HTTPError as exc:
        ms = int((time.perf_counter() - t0) * 1000)
        return {"path": path, "ok": False, "status": exc.code, "ms": ms, "error": str(exc.reason)}
    except (URLError, TimeoutError, OSError) as exc:
        ms = int((time.perf_counter() - t0) * 1000)
        return {"path": path, "ok": False, "status": None, "ms": ms, "error": str(exc)}


async def fetch_site_health() -> dict[str, Any]:
    paths = ("/", "/login", "/oracle/BTC")
    probes = [probe_surface(p) for p in paths]
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "base_url": _base_url() or None,
        "surfaces": probes,
        "all_ok": all(p.get("ok") for p in probes),
    }


async def search_users(q: str = "", limit: int = 50) -> list[dict[str, Any]]:
    from database import get_connection

    limit = max(1, min(int(limit), 200))
    q = (q or "").strip().lower()
    async with get_connection() as db:
        if q:
            like = f"%{q}%"
            rows = await (
                await db.execute(
                    """
                    SELECT u.id, u.email, u.name, u.created_at, u.last_login_at,
                           COALESCE(s.plan, 'free') AS plan,
                           COALESCE(s.subscription_status, 'active') AS subscription_status
                    FROM users u
                    LEFT JOIN subscription_accounts s ON s.user_id = u.id
                    WHERE LOWER(u.email) LIKE ? OR LOWER(COALESCE(u.name,'')) LIKE ?
                    ORDER BY u.id DESC
                    LIMIT ?
                    """,
                    (like, like, limit),
                )
            ).fetchall()
        else:
            rows = await (
                await db.execute(
                    """
                    SELECT u.id, u.email, u.name, u.created_at, u.last_login_at,
                           COALESCE(s.plan, 'free') AS plan,
                           COALESCE(s.subscription_status, 'active') AS subscription_status
                    FROM users u
                    LEFT JOIN subscription_accounts s ON s.user_id = u.id
                    ORDER BY u.id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows or []:
        if isinstance(row, dict):
            out.append(dict(row))
        else:
            out.append(
                {
                    "id": row[0],
                    "email": row[1],
                    "name": row[2],
                    "created_at": row[3],
                    "last_login_at": row[4],
                    "plan": row[5],
                    "subscription_status": row[6],
                }
            )
    return out


async def update_user_admin(
    user_id: int,
    *,
    plan: str | None,
    subscription_status: str | None,
) -> dict[str, Any]:
    from database import get_connection

    uid = int(user_id)
    now = datetime.now(UTC).isoformat()
    async with get_connection() as db:
        user = await (await db.execute("SELECT id, email FROM users WHERE id = ?", (uid,))).fetchone()
        if not user:
            raise ValueError("user_not_found")
        email = user["email"] if isinstance(user, dict) else user[1]
        sub = await (
            await db.execute("SELECT id FROM subscription_accounts WHERE user_id = ?", (uid,))
        ).fetchone()
        if plan is not None:
            plan = normalize_plan(plan)
        if sub:
            if plan is not None:
                await db.execute(
                    "UPDATE subscription_accounts SET plan = ?, updated_at = ? WHERE user_id = ?",
                    (plan, now, uid),
                )
            if subscription_status is not None:
                await db.execute(
                    "UPDATE subscription_accounts SET subscription_status = ?, updated_at = ? WHERE user_id = ?",
                    (subscription_status, now, uid),
                )
        else:
            await db.execute(
                """
                INSERT INTO subscription_accounts (
                    user_id, email, plan, subscription_status, payment_status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'none', ?, ?)
                """,
                (
                    uid,
                    email,
                    normalize_plan(plan or "free"),
                    subscription_status or "active",
                    now,
                    now,
                ),
            )
        await db.commit()
    matches = await search_users(str(email), limit=1)
    return matches[0] if matches else {"id": uid, "email": email}


def payload_hash_obj(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
