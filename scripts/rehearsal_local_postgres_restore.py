#!/usr/bin/env python3
"""Isolated local Postgres backup/restore rehearsal for Production Readiness §10."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "data" / "production_readiness"
EVIDENCE_PATH = EVIDENCE_DIR / "local_postgres_restore_rehearsal.json"

DB_NAME = "blackdark_pr_restore_rehearsal"
MARKER_TABLE = "pr_restore_marker"
MARKER_VALUE = "pr-restore-marker-v1"

# Fixed rehearsal SQL (constants only — no dynamic SQL composition for Bandit B608).
_SQL_DROP_DB = "DROP DATABASE IF EXISTS blackdark_pr_restore_rehearsal;"
_SQL_CREATE_DB = "CREATE DATABASE blackdark_pr_restore_rehearsal;"
_SQL_CREATE_MARKER = (
    "CREATE TABLE pr_restore_marker (id serial PRIMARY KEY, marker text NOT NULL, "
    "created_at timestamptz DEFAULT now());"
)
_SQL_INSERT_MARKER = "INSERT INTO pr_restore_marker (marker) VALUES ('pr-restore-marker-v1');"
_SQL_DELETE_MARKERS = "DELETE FROM pr_restore_marker;"
_SQL_COUNT_MARKERS = "SELECT count(*) FROM pr_restore_marker;"
_SQL_SELECT_MARKER = "SELECT marker FROM pr_restore_marker LIMIT 1;"
_SQL_SCHEMA_CHECK = (
    "SELECT count(*) FROM information_schema.tables WHERE table_name = 'pr_restore_marker';"
)


def _run(cmd: list[str], *, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=env or os.environ.copy())
    if check and proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr[-500:]}")
    return proc


def _psql(sql: str) -> None:
    _run(["sudo", "-u", "postgres", "psql", "-v", "ON_ERROR_STOP=1", "-c", sql])


def _psql_db(sql: str) -> None:
    _run(["sudo", "-u", "postgres", "psql", "-v", "ON_ERROR_STOP=1", "-d", DB_NAME, "-c", sql])


def _database_url() -> str:
    # Local peer auth via postgres OS user during rehearsal.
    return f"postgresql:///{DB_NAME}"


def main() -> int:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = Path(tempfile.mkdtemp(prefix="blackdark_pr_rehearsal_backups_"))
    os.chmod(out_dir, 0o700)
    gaps: list[str] = []
    evidence: dict[str, object] = {
        "LOCAL_POSTGRES_RESTORE_REHEARSAL_PERFORMED": True,
        "database": DB_NAME,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    try:
        _psql(_SQL_DROP_DB)
        _psql(_SQL_CREATE_DB)
        _psql_db(_SQL_CREATE_MARKER)
        _psql_db(_SQL_INSERT_MARKER)

        env = os.environ.copy()
        env["DATABASE_URL"] = _database_url()
        _run(
            ["sudo", "-u", "postgres", "env", f"DATABASE_URL={_database_url()}", sys.executable, "scripts/backup_postgres.py", "--out", str(out_dir)],
            env=env,
        )

        backups = sorted(out_dir.glob("blackdark_*.sql.gz"))
        if not backups:
            gaps.append("backup_file_missing")
        else:
            evidence["BACKUP_CREATION_VERIFIED"] = True
            dump_path = backups[-1]

            _psql_db(_SQL_DELETE_MARKERS)
            count = _run(
                ["sudo", "-u", "postgres", "psql", "-tAc", _SQL_COUNT_MARKERS, "-d", DB_NAME],
                check=True,
            ).stdout.strip()
            if count != "0":
                gaps.append("controlled_delete_failed")

            # Destructive restore requires clean database (plain SQL dump includes CREATE).
            _psql(_SQL_DROP_DB)
            _psql(_SQL_CREATE_DB)

            restore = _run(
                [
                    "sudo",
                    "-u",
                    "postgres",
                    "env",
                    f"DATABASE_URL={_database_url()}",
                    sys.executable,
                    "scripts/restore_postgres.py",
                    str(dump_path),
                    "--yes",
                ],
                env=env,
                check=False,
            )
            if restore.returncode != 0:
                gaps.append("restore_execution_failed")
            else:
                evidence["RESTORE_EXECUTION_VERIFIED"] = True

            restored = _run(
                ["sudo", "-u", "postgres", "psql", "-tAc", _SQL_SELECT_MARKER, "-d", DB_NAME],
                check=True,
            ).stdout.strip()
            if restored != MARKER_VALUE:
                gaps.append("restored_data_integrity_failed")
            else:
                evidence["RESTORED_DATA_INTEGRITY_VERIFIED"] = True

            schema = _run(
                [
                    "sudo",
                    "-u",
                    "postgres",
                    "psql",
                    "-tAc",
                    _SQL_SCHEMA_CHECK,
                    "-d",
                    DB_NAME,
                ],
                check=True,
            ).stdout.strip()
            if schema != "1":
                gaps.append("schema_integrity_failed")

            boot = _run(
                [
                    sys.executable,
                    "-c",
                    "import os; os.environ['DATABASE_URL']=%r; from database import init_db; init_db(); print('boot_ok')"
                    % _database_url(),
                ],
                check=False,
            )
            if boot.returncode != 0 or "boot_ok" not in boot.stdout:
                gaps.append("restored_app_boot_failed")
            else:
                evidence["RESTORED_APP_BOOT_VERIFIED"] = True

    except Exception as exc:
        gaps.append(f"exception:{exc}")

    evidence["TRUE_LOCAL_RESTORE_GAPS"] = len(gaps)
    evidence["gaps"] = gaps
    evidence["GENUINE_EXTERNAL_RESTORE_VALIDATION_PENDING"] = 1
    evidence["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 0 if not gaps else 1


if __name__ == "__main__":
    raise SystemExit(main())
