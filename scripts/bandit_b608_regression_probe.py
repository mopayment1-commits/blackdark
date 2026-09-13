#!/usr/bin/env python3
"""Regression probes for Bandit B608 fail-closed behavior (no baseline)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANDIT = ROOT / ".venv" / "bin" / "bandit"
CI_CMD = [str(BANDIT), "-r", ".", "--ini", ".bandit", "-ll", "-f", "json", "-q"]


def _run(workdir: Path) -> tuple[int, list[dict]]:
    proc = subprocess.run(CI_CMD, cwd=workdir, capture_output=True, text=True)
    findings = json.loads(proc.stdout).get("results", []) if proc.stdout.strip() else []
    return proc.returncode, findings


def _copy_repo() -> Path:
    td = Path(tempfile.mkdtemp(prefix="bandit-b608-reg-"))
    shutil.copytree(
        ROOT,
        td,
        ignore=shutil.ignore_patterns(".venv", ".git", "data", "__pycache__"),
        dirs_exist_ok=True,
    )
    return td


def main() -> int:
    results: dict[str, object] = {"bandit_version": subprocess.check_output([str(BANDIT), "--version"], text=True).strip()}

    # TEST 1 — known reviewed production tree passes
    td1 = _copy_repo()
    rc1, f1 = _run(td1)
    results["test1_known_tree"] = {"exit_code": rc1, "new_findings": len(f1), "pass": rc1 == 0 and len(f1) == 0}

    # TEST 2 — brand-new production B608 must fail
    td2 = _copy_repo()
    (td2 / "bandit_regression_probe_module.py").write_text(
        textwrap.dedent(
            """
            async def bandit_regression_probe(db, user_table):
                user_table = "users"
                await db.execute(f"SELECT * FROM {user_table} WHERE id = ?", (1,))
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    rc2, f2 = _run(td2)
    results["test2_new_production_b608"] = {
        "exit_code": rc2,
        "new_findings": len(f2),
        "pass": rc2 != 0 and len(f2) >= 1,
    }

    # TEST 3 — second B608 in already-reviewed file must fail (no baseline swallow)
    td3 = _copy_repo()
    orig = (ROOT / "audit_registry.py").read_text(encoding="utf-8")
    insert = (
        "\nasync def bandit_regression_duplicate_b608(db, table_name: str):\n"
        '    table_name = "audit_logs"\n'
        '    await db.execute(f"SELECT id FROM {table_name} LIMIT 1")\n\n'
    )
    (td3 / "audit_registry.py").write_text(
        orig.replace("async def fetch_audit_logs", insert + "async def fetch_audit_logs", 1),
        encoding="utf-8",
    )
    rc3, f3 = _run(td3)
    results["test3_duplicate_in_reviewed_file"] = {
        "exit_code": rc3,
        "new_findings": len(f3),
        "pass": rc3 != 0 and len(f3) >= 1,
    }

    print(json.dumps(results, indent=2))
    ok = all(results[k]["pass"] for k in ("test1_known_tree", "test2_new_production_b608", "test3_duplicate_in_reviewed_file"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
