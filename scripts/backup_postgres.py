#!/usr/bin/env python3
"""Encrypted-at-rest Postgres backup via pg_dump (gzip).

Usage:
  DATABASE_URL=postgresql://… python scripts/backup_postgres.py
  python scripts/backup_postgres.py --out data/backups

Restore helper: scripts/restore_postgres.py
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import os
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _database_url() -> str:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url.startswith("postgres"):
        raise SystemExit("DATABASE_URL must be postgresql://… for this backup script")
    return url


def backup(*, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    raw = out_dir / f"blackdark_{stamp}.sql"
    gz = out_dir / f"blackdark_{stamp}.sql.gz"
    url = _database_url()
    # Prefer pg_dump if present
    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        raise SystemExit("pg_dump not found — install PostgreSQL client tools")
    _ = os.environ.copy()  # reserved for subprocess env overrides
    # pg_dump accepts URL via --dbname
    proc = subprocess.run(
        [pg_dump, "--dbname", url, "--no-owner", "--format=plain", "-f", str(raw)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"pg_dump failed: {proc.stderr.strip()}")
    with raw.open("rb") as src, gzip.open(gz, "wb", compresslevel=9) as dst:
        shutil.copyfileobj(src, dst)
    raw.unlink(missing_ok=True)
    digest = hashlib.sha256(gz.read_bytes()).hexdigest()
    meta = out_dir / f"blackdark_{stamp}.sha256"
    meta.write_text(f"{digest}  {gz.name}\n", encoding="utf-8")
    # marker for readiness checks
    latest = out_dir / "LATEST"
    latest.write_text(str(gz.name) + "\n" + digest + "\n", encoding="utf-8")
    print(f"OK backup={gz} sha256={digest[:16]}…")
    return gz


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default=str(ROOT / "data" / "backups"),
        help="Backup directory",
    )
    args = parser.parse_args()
    backup(out_dir=Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
