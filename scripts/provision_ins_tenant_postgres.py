"""INS-TENANT — provision and verify Postgres multi-tenant production path."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def provision(*, migrate_json: bool = True) -> dict:
    from database import init_db
    from org_tenant_store import migrate_json_orgs_if_needed, org_isolation_status_pg, verify_postgres_tenant_smoke
    from postgres_backend import init_postgres, pool_stats, use_postgres

    if not use_postgres():
        raise RuntimeError("DATABASE_URL must be set to postgresql://...")

    await init_postgres()
    await init_db()
    migration = {"imported_orgs": 0, "imported_members": 0, "skipped": True}
    if migrate_json:
        migration = await migrate_json_orgs_if_needed()
    smoke = await verify_postgres_tenant_smoke()
    status = await org_isolation_status_pg()
    return {
        "engine": "postgresql",
        "pool": pool_stats(),
        "migration": migration,
        "smoke": smoke,
        "status": status,
        "ins_tenant_ready": smoke.get("smoke_pass") and status.get("postgres_active"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision INS-TENANT on Postgres")
    parser.add_argument("--no-json-migrate", action="store_true")
    parser.add_argument("--out", default="", help="Write evidence JSON path")
    args = parser.parse_args()

    url = os.getenv("DATABASE_URL", "")
    if not url.startswith(("postgres://", "postgresql://")):
        print("ERROR: DATABASE_URL not set to PostgreSQL", file=sys.stderr)
        return 1

    # Redact credentials in logs
    safe = url.split("@")[-1] if "@" in url else "configured"
    print(f"INS-TENANT provision | target=***@{safe}")

    result = asyncio.run(provision(migrate_json=not args.no_json_migrate))
    print(json.dumps(result, indent=2, default=str))
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    return 0 if result.get("ins_tenant_ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
