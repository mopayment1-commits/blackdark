#!/usr/bin/env python3
"""Prove Batch05 freeze/HEAD ancestry and semantic equivalence."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "docs/BATCH05_FINAL_LOCAL_FREEZE.json"
OUT = ROOT / "docs/BATCH05_FREEZE_HEAD_CONSISTENCY.json"

PRODUCTION_PREFIXES = (
    "cap646/",
    "bd_platform/",
    "api/",
    "blackdark/",
    "billing/",
    "config/",
    "microservices/",
    "ml/",
    "sdk/",
    "static/",
    "templates/",
)
PRODUCTION_ROOT_PY = True


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def classify_path(path: str) -> str:
    if path.startswith("docs/"):
        return "docs"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("scripts/"):
        return "scripts"
    if path.startswith(".github/"):
        return "ci"
    if path.startswith("requirements") or path in {
        "requirements.txt",
        "requirements.lock.txt",
        "requirements.hashes.txt",
        "requirements-prod.txt",
        "requirements-prod.lock.txt",
        "requirements-prod.hashes.txt",
    }:
        return "dependency_lock"
    if path.startswith(PRODUCTION_PREFIXES):
        return "production_runtime"
    if PRODUCTION_ROOT_PY and path.endswith(".py") and "/" not in path:
        return "production_runtime"
    if path.startswith("docs/data-room/"):
        return "docs"
    return "other"


def commit_role(files: list[str]) -> str:
    classes = {classify_path(f) for f in files}
    if classes <= {"docs"}:
        return "docs_stamp"
    if classes <= {"docs", "tests", "scripts"}:
        return "evidence_docs_tests_scripts"
    if "production_runtime" in classes:
        return "production_runtime_change"
    if "dependency_lock" in classes:
        return "dependency_lock_change"
    return "mixed"


def classify_range(older: str, newer: str) -> list[dict[str, Any]]:
    if older == newer:
        return []
    log = _git("log", "--format=%H %s", f"{older}..{newer}").splitlines()
    rows: list[dict[str, Any]] = []
    for line in log:
        sha, _, subject = line.partition(" ")
        files = [p for p in _git("diff-tree", "--no-commit-id", "--name-only", "-r", sha).splitlines() if p]
        classes = sorted({classify_path(f) for f in files})
        rows.append(
            {
                "commit": sha,
                "subject": subject,
                "files": files,
                "path_classes": classes,
                "role": commit_role(files),
                "production_runtime_files": [f for f in files if classify_path(f) == "production_runtime"],
            }
        )
    return rows


def build(current_head: str | None = None) -> dict[str, Any]:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    heads = freeze["freeze_heads"]
    current = current_head or _git("rev-parse", "HEAD")
    source = heads.get("tested_source_head") or heads.get("source_head")
    regression = freeze.get("cross_batch_regression", {}).get("git_commit") or heads.get("regression_head")
    commits = classify_range(source, current)
    prod_files = sorted({f for row in commits for f in row["production_runtime_files"]})
    semantic = not prod_files and all(row["role"] in {"docs_stamp", "evidence_docs_tests_scripts"} or "production_runtime" not in row["path_classes"] for row in commits)
    # semantic equivalence: no production/runtime file drift between tested source and current HEAD
    semantic = len(prod_files) == 0
    doc = {
        "tested_source_head": source,
        "regression_head": regression,
        "artifact_generation_head": heads.get("artifact_generation_head"),
        "artifact_embedded_head": heads.get("artifact_embedded_head"),
        "final_freeze_head": heads.get("final_freeze_head"),
        "source_head": heads.get("source_head"),
        "repository_head_at_generation": heads.get("repository_head"),
        "artifact_container_commit": current,
        "current_repository_head": current,
        "commits_since_tested_source": commits,
        "production_runtime_drift_files": prod_files,
        "production_runtime_drift_count": len(prod_files),
        "frozen_source_head_is_semantically_equivalent_to_current_head": semantic,
        "freeze_flags": {
            "BATCH05_FINAL_LOCAL_FREEZE": freeze.get("BATCH05_FINAL_LOCAL_FREEZE"),
            "LOCAL_GOVERNANCE_COMPLETE": freeze.get("LOCAL_GOVERNANCE_COMPLETE"),
            "known_local_deficiencies": freeze.get("known_local_deficiencies"),
        },
        "roles": {
            "tested_source_head": "Commit whose code/deps were executed for local assurance",
            "regression_head": "Commit recorded in BATCH05_CROSS_BATCH_REGRESSION.json",
            "artifact_generation_head": "HEAD when freeze JSON was generated",
            "artifact_embedded_head": "HEAD embedded inside freeze payload at generation",
            "artifact_container_commit": "Commit that currently contains the freeze file (repository HEAD)",
            "current_repository_head": "git rev-parse HEAD now",
        },
    }
    return doc


def main() -> None:
    doc = build()
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT.name} semantic_eq={doc['frozen_source_head_is_semantically_equivalent_to_current_head']} "
        f"prod_drift={doc['production_runtime_drift_count']}"
    )
    if doc["production_runtime_drift_count"] and doc["freeze_flags"]["BATCH05_FINAL_LOCAL_FREEZE"]:
        raise SystemExit("production/runtime drift under a frozen source — regenerate freeze")


if __name__ == "__main__":
    main()
