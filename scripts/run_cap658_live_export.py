#!/usr/bin/env python3
"""Run CAP-658 export using DATABASE_URL + BigQuery credentials from the environment."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def _ensure_lake_rows() -> None:
    from database import fetch_ingestion_snapshots_for_export

    rows = await fetch_ingestion_snapshots_for_export(limit=1)
    if rows:
        return
    import aiohttp

    import config
    from ingestion_fetchers import ingest_category

    timeout = aiohttp.ClientTimeout(total=config.INGESTION_FETCH_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        await ingest_category(session, "prices")  # type: ignore[arg-type]


async def main() -> int:
    required = ["DATABASE_URL", "BIGQUERY_PROJECT_ID", "BIGQUERY_CREDENTIALS_JSON"]
    missing = [name for name in required if not os.getenv(name, "").strip()]
    if missing:
        raise SystemExit(f"missing_env: {missing}")

    from database import init_db
    from bigquery_export import export_ingestion_snapshots_to_bigquery, get_export_evidence

    await init_db()
    await _ensure_lake_rows()
    evidence = await export_ingestion_snapshots_to_bigquery(operator="cap658_live_export")
    print(json.dumps({"evidence": evidence, "cached": get_export_evidence()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
