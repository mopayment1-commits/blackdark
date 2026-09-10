#!/usr/bin/env python3
"""Strict evidence reconciliation — FINAL GAP CLOSURE CORRECTION."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# §37 external gates absent from base extractor (153 = 146 + 7); 3 §37 rows are TRUE_DUPLICATE elsewhere.
SECTION_37_EXTERNAL_REQUIREMENTS: tuple[dict[str, str], ...] = (
    {
        "source_section": "§37",
        "text": "production CDN/WAF behavior",
        "classification": "REQUIREMENT_WRONGLY_DROPPED",
    },
    {
        "source_section": "§37",
        "text": "production load capacity",
        "classification": "REQUIREMENT_WRONGLY_DROPPED",
    },
    {
        "source_section": "§37",
        "text": "contractual redistribution permission",
        "classification": "REQUIREMENT_WRONGLY_DROPPED",
    },
    {
        "source_section": "§37",
        "text": "production cookie-consent jurisdiction verification",
        "classification": "REQUIREMENT_WRONGLY_DROPPED",
    },
    {
        "source_section": "§37",
        "text": "production SEO indexing outcome",
        "classification": "REQUIREMENT_WRONGLY_DROPPED",
    },
    {
        "source_section": "§37",
        "text": "production analytics vendor behavior",
        "classification": "REQUIREMENT_WRONGLY_DROPPED",
    },
    {
        "source_section": "§37",
        "text": "production DDoS behavior",
        "classification": "REQUIREMENT_WRONGLY_DROPPED",
    },
)

SECTION_37_TRUE_DUPLICATES: tuple[dict[str, str], ...] = (
    {
        "source_section": "§37",
        "text": "jurisdiction-specific legal determination",
        "classification": "TRUE_DUPLICATE",
        "why_not_counted_now": "Covered by LEGAL_REVIEW_REQUIRED normative lines",
    },
    {
        "source_section": "§37",
        "text": "provider commercial-license approval",
        "classification": "TRUE_DUPLICATE",
        "why_not_counted_now": "Covered by AV-11 acceptance requirement",
    },
    {
        "source_section": "§37",
        "text": "external accessibility audit",
        "classification": "TRUE_DUPLICATE",
        "why_not_counted_now": "Covered by external WCAG verification gate",
    },
)


def git_head(ref: str = "HEAD") -> str:
    return subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip()


def head_is_evidence_only() -> bool:
    try:
        files = subprocess.check_output(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip().splitlines()
    except Exception:
        return False
    if not files:
        return False
    allowed = {"docs/ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_FINAL_RECONCILIATION.json"}
    return set(files).issubset(allowed)


def run_pytest_nodeids(path: str = "tests") -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", path, "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    nodeids = [ln.strip() for ln in (proc.stdout + proc.stderr).splitlines() if "::" in ln and not ln.startswith("=")]
    return {"returncode": proc.returncode, "nodeids": nodeids}


def pytest_run(ref: str, junit_path: Path) -> dict[str, Any]:
    subprocess.run(["git", "checkout", ref, "--", "."], cwd=ROOT, capture_output=True)
    env = os.environ.copy()
    env.setdefault("DATABASE_URL", "sqlite:////tmp/regression.db")
    env.setdefault("ENV", "development")
    env.setdefault("COOKIE_SECURE", "false")
    env.setdefault("SECRETS_MASTER_KEY", "regression-test-key")
    env.setdefault("SESSION_TOKEN_PEPPER", "regression-test-pepper")
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests",
            "-q",
            f"--junitxml={junit_path}",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    return {"returncode": proc.returncode, "stdout_tail": proc.stdout[-4000:], "stderr_tail": proc.stderr[-2000:]}


def parse_junit(path: Path) -> dict[str, list[str]]:
    import xml.etree.ElementTree as ET

    if not path.is_file():
        return {"passed": [], "failed": [], "skipped": []}
    root = ET.parse(path).getroot()
    passed: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []
    for case in root.iter("testcase"):
        nid = f"{case.get('classname')}::{case.get('name')}"
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(nid)
        elif case.find("skipped") is not None:
            skipped.append(nid)
        else:
            passed.append(nid)
    return {"passed": passed, "failed": failed, "skipped": skipped}


def main() -> int:
    from anonymous_visitor.traceability import build_traceability_report, extract_spec_requirements
    from anonymous_visitor.reconciliation import reconciliation_semantics_valid

    base = git_head("origin/cursor/financial-data-security-closure-ed16")
    head = git_head()
    report = build_traceability_report(head=head)
    rec = reconciliation_semantics_valid()

    missing_or_different = []
    start_id = len(extract_spec_requirements()) + 1
    for i, row in enumerate(SECTION_37_EXTERNAL_REQUIREMENTS, start=start_id):
        missing_or_different.append(
            {
                "ID": f"REQ-{i:03d}",
                "ORIGINAL_TEXT": row["text"],
                "SOURCE_SECTION": row["source_section"],
                "WHY_NOT_COUNTED_NOW": "§37 external gate omitted from base extractor (now restored)",
                "CLASSIFICATION": row["classification"],
            }
        )
    for row in SECTION_37_TRUE_DUPLICATES:
        missing_or_different.append(
            {
                "ID": "N/A",
                "ORIGINAL_TEXT": row["text"],
                "SOURCE_SECTION": row["source_section"],
                "WHY_NOT_COUNTED_NOW": row["why_not_counted_now"],
                "CLASSIFICATION": row["classification"],
            }
        )

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "CURRENT_HEAD": head,
        "PREVIOUS_REQUIREMENT_COUNT": 153,
        "CURRENT_EXTRACTED_REQUIREMENT_COUNT": report.get("BASE_EXTRACTED_COUNT", len(extract_spec_requirements())),
        "MISSING_OR_DIFFERENT_REQUIREMENTS": missing_or_different,
        "FINAL_CANONICAL_REQUIREMENT_COUNT": report["TOTAL_SPEC_REQUIREMENTS"],
        "REQUIREMENT_COUNT_RECONCILED": report.get("REQUIREMENT_COUNT_RECONCILED", False),
        "traceability": report,
        "reconciliation": rec,
    }
    path = ROOT / "docs" / "ANONYMOUS_VISITOR_STRICT_EVIDENCE_RECONCILIATION.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"FINAL_CANONICAL_REQUIREMENT_COUNT": out["FINAL_CANONICAL_REQUIREMENT_COUNT"], "REQUIREMENT_COUNT_RECONCILED": out["REQUIREMENT_COUNT_RECONCILED"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
