#!/usr/bin/env python3
"""Restore a gzipped SQL dump created by scripts/backup_postgres.py.

  DATABASE_URL=postgresql://… python scripts/restore_postgres.py data/backups/blackdark_….sql.gz
"""

from __future__ import annotations

import argparse
import gzip
import os
import shutil
import subprocess  # nosec B404 — intentional admin tooling
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dump", help="Path to .sql.gz dump")
    parser.add_argument("--yes", action="store_true", help="Confirm destructive restore")
    args = parser.parse_args()
    if not args.yes:
        print("Refusing restore without --yes (destructive).", file=sys.stderr)
        return 2
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url.startswith("postgres"):
        print("DATABASE_URL must be postgresql://…", file=sys.stderr)
        return 2
    dump = Path(args.dump)
    if not dump.is_file():
        print(f"Missing dump: {dump}", file=sys.stderr)
        return 2
    psql = shutil.which("psql")
    if not psql:
        print("psql not found", file=sys.stderr)
        return 2
    with gzip.open(dump, "rb") as src, tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as tmp:
        shutil.copyfileobj(src, tmp)
        tmp_path = tmp.name
    try:
        proc = subprocess.run(  # nosec B603 — fixed argv, shell=False, no user input
            [psql, url, "-v", "ON_ERROR_STOP=1", "-f", tmp_path],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(proc.stderr, file=sys.stderr)
            return proc.returncode
        print("OK restore complete")
        return 0
    finally:
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
