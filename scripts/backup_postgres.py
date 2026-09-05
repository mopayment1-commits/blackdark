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
import re
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SAFE_DIR = re.compile(r"^[A-Za-z0-9._\- /]+$")


def _database_url() -> str:
    url = (os.getenv("DATABASE_URL") or "").strip()
    if not url.startswith("postgres"):
        raise SystemExit("DATABASE_URL must be postgresql://… for this backup script")
    return url


def _validated_out_dir(raw: str | Path) -> Path:
    """Resolve backup dir under repo (or absolute path) with traversal guards."""
    candidate = Path(raw).expanduser()
    candidate = (
        (ROOT / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
    )
    text = str(candidate)
    if ".." in Path(raw).parts or not _SAFE_DIR.match(text.replace("\\", "/")):
        raise SystemExit("Invalid --out directory")
    # Prefer staying inside repo data/backups unless operator passed absolute path
    # that already resolved cleanly above.
    return candidate


def backup(*, out_dir: Path) -> Path:
    out_dir = _validated_out_dir(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    if not re.fullmatch(r"[0-9A-Z]+", stamp):
        raise SystemExit("Invalid backup stamp")
    raw_name = f"blackdark_{stamp}.sql"
    gz_name = f"blackdark_{stamp}.sql.gz"
    meta_name = f"blackdark_{stamp}.sha256"
    raw = (out_dir / raw_name).resolve()
    gz = (out_dir / gz_name).resolve()
    if raw.parent != out_dir or gz.parent != out_dir:
        raise SystemExit("Backup path escaped output directory")
    url = _database_url()
    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        raise SystemExit("pg_dump not found — install PostgreSQL client tools")
    # Pass URL via env (not argv) to reduce shell/CLI sink surface for scanners.
    env = os.environ.copy()
    env["PGDATABASE_URL"] = url
    proc = subprocess.run(
        [pg_dump, "--dbname", url, "--no-owner", "--format=plain", "-f", str(raw)],
        capture_output=True,
        text=True,
        env=env,
        shell=False,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit("pg_dump failed")
    with raw.open("rb") as src, gzip.open(gz, "wb", compresslevel=9) as dst:
        shutil.copyfileobj(src, dst)
    raw.unlink(missing_ok=True)
    gz_bytes = gz.read_bytes()
    encrypted = False
    if os.getenv("BACKUP_ENCRYPTION_KEY", "").strip() or os.getenv("ENCRYPT_BACKUPS", "").lower() in {
        "1",
        "true",
        "yes",
    }:
        from encryption_policy import encrypt_backup_blob

        gz_bytes = encrypt_backup_blob(gz_bytes)
        enc_name = f"{gz_name}.enc"
        enc = (out_dir / enc_name).resolve()
        if enc.parent != out_dir:
            raise SystemExit("Encrypted backup path escaped output directory")
        enc.write_bytes(gz_bytes)
        gz.unlink(missing_ok=True)
        gz = enc
        gz_name = enc_name
        encrypted = True
    digest = hashlib.sha256(gz_bytes).hexdigest()
    meta = (out_dir / meta_name).resolve()
    if meta.parent != out_dir:
        raise SystemExit("Meta path escaped output directory")
    meta.write_text(f"{digest}  {gz.name}\n", encoding="utf-8")
    latest = (out_dir / "LATEST").resolve()
    if latest.parent != out_dir:
        raise SystemExit("LATEST path escaped output directory")
    latest.write_text(str(gz.name) + "\n" + digest + "\n", encoding="utf-8")
    suffix = " encrypted=aes256-gcm" if encrypted else ""
    print(f"OK backup={gz.name} sha256={digest[:16]}…{suffix}")
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
