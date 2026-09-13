#!/usr/bin/env python3
"""Export institutional CodeQL 911/911 reconciliation artifacts (immutable f038bc33 corpus)."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Reuse proven disposition logic from triage script.
from codeql_disposition_audit import (  # type: ignore
    ORIGINAL_QUALITY,
    ORIGINAL_SECURITY,
    ORIGINAL_SHA,
    ORIGINAL_TOTAL,
    SECURITY_RULES,
    _classify,
    _fingerprint,
    _final_sarif_match,
    _load_original_inventory,
    _norm_uri,
    _parse_sarif,
    _reconciliation_bucket,
    _runtime_scope,
    _sarif_index,
    build_ledger,
)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "evidence" / "codeql-reconciliation"
CURRENT_SARIF = OUT_DIR / "CODEQL_CURRENT_HEAD.sarif"

REMEDIATION_COMMIT = "c71580dce3171b1e5040f17b5f033f8979daadd6"

INSTITUTIONAL_DISPOSITIONS = frozenset(
    {
        "TRUE_POSITIVE_FIXED",
        "FALSE_POSITIVE_PROVEN",
        "TEST_ONLY_PROVEN",
        "DUPLICATE_PROVEN",
        "QUALITY_REMEDIATED",
        "QUALITY_ACCEPTED_WITH_PROOF",
        "NO_LONGER_PRESENT_WITH_PROVENANCE",
        "OWNER_DECISION_REQUIRED",
    }
)


def _git_sha(ref: str = "HEAD") -> str:
    return subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip()


def _git_show_lines(sha: str, file: str) -> list[str] | None:
    try:
        text = subprocess.check_output(
            ["git", "show", f"{sha}:{file}"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return None
    return text.splitlines()


def _context_block(lines: list[str] | None, line: int, radius: int = 5) -> str:
    if not lines:
        return ""
    start = max(0, line - 1 - radius)
    end = min(len(lines), line + radius)
    return "\n".join(f"{i + 1:5d}| {lines[i]}" for i in range(start, end))


def _map_institutional_disposition(row: dict[str, Any]) -> str:
    legacy = row["disposition"]
    sarif = row["final_sarif_presence"]
    rule = row["ruleId"]

    if legacy == "CONFIRMED_TRUE_POSITIVE":
        if row["final_status"].startswith("remediated"):
            return "TRUE_POSITIVE_FIXED"
        return "OWNER_DECISION_REQUIRED"
    if legacy == "CONTEXTUALLY_SAFE_FALSE_POSITIVE":
        return "FALSE_POSITIVE_PROVEN"
    if legacy == "TEST_ONLY_NON_PRODUCTION":
        return "TEST_ONLY_PROVEN"
    if legacy == "DUPLICATE_SAME_ROOT_CAUSE":
        return "DUPLICATE_PROVEN"
    if legacy == "REQUIRES_ADDITIONAL_VERIFICATION":
        return "OWNER_DECISION_REQUIRED"
    if legacy == "QUALITY_TECHNICAL_DEBT":
        if sarif == "absent_from_final_sarif":
            return "NO_LONGER_PRESENT_WITH_PROVENANCE"
        return "QUALITY_ACCEPTED_WITH_PROOF"
    return "OWNER_DECISION_REQUIRED"


def _remediation_commit(row: dict[str, Any]) -> str | None:
    if row["disposition"] == "CONFIRMED_TRUE_POSITIVE" and row["final_status"].startswith("remediated"):
        return REMEDIATION_COMMIT
    return None


def _is_security(row: dict[str, Any]) -> bool:
    return row["ruleId"] in SECURITY_RULES


def _enrich_record(
    row: dict[str, Any],
    original: dict[str, Any],
    baseline_lines: list[str] | None,
    current_lines: list[str] | None,
    current_sha: str,
) -> dict[str, Any]:
    final_disp = _map_institutional_disposition(row)
    return {
        "finding_id": row["finding_id"],
        "original_finding_id": f"{original['file']}|{original['line']}|{original['ruleId']}|{original['finding_id']}",
        "original_rule_id": original["ruleId"],
        "original_file": original["file"],
        "original_line": original["line"],
        "original_message": original["message"],
        "original_security_severity": original["security_severity"],
        "original_problem_severity": original["problem_severity"],
        "original_precision": original["precision"],
        "original_cwe_tags": original["cwe_tags"],
        "original_baseline_sha": ORIGINAL_SHA,
        "original_source_context": _context_block(baseline_lines, original["line"]),
        "current_head_sha": current_sha,
        "current_file": original["file"],
        "current_line": original["line"],
        "current_semantic_binding": f"{original['file']}|{original['line']}|{original['ruleId']}",
        "current_source_context": _context_block(current_lines, original["line"]),
        "current_file_exists": current_lines is not None,
        "security_classification": "security" if _is_security(row) else "quality",
        "runtime_scope": row["runtime_scope"],
        "final_disposition": final_disp,
        "legacy_disposition": row["disposition"],
        "justification": row["evidence"],
        "remediation_commit": _remediation_commit(row),
        "verification_test_evidence": row["test_evidence"],
        "final_sarif_presence": row["final_sarif_presence"],
        "remediation_required": row["remediation_required"],
        "final_status": row["final_status"],
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return _sha256(path)


def _summarize(records: list[dict[str, Any]], current_sha: str, sarif_path: Path, sarif_count: int) -> dict[str, Any]:
    disp = Counter(r["final_disposition"] for r in records)
    sec = [r for r in records if r["security_classification"] == "security"]
    qual = [r for r in records if r["security_classification"] == "quality"]
    sec_disp = Counter(r["final_disposition"] for r in sec)
    qual_disp = Counter(r["final_disposition"] for r in qual)

    open_security = sum(
        1
        for r in sec
        if r["final_disposition"] in {"OWNER_DECISION_REQUIRED"}
        or (
            r["final_disposition"] == "TRUE_POSITIVE_FIXED"
            and r["final_sarif_presence"].startswith("still_present")
        )
    )
    open_quality = sum(
        1 for r in qual if r["final_disposition"] == "OWNER_DECISION_REQUIRED"
    )
    duplicate_accounted = disp.get("DUPLICATE_PROVEN", 0)

    unaccounted = ORIGINAL_TOTAL - len(records)
    status = "REMEDIATION_COMPLETE_PENDING_INDEPENDENT_AUDIT"
    if unaccounted != 0 or disp.get("OWNER_DECISION_REQUIRED", 0) > 0:
        status = "BLOCKED_WITH_OPEN_ITEMS"

    return {
        "ORIGINAL_BASELINE_SHA": ORIGINAL_SHA,
        "CURRENT_HEAD_SHA": current_sha,
        "CODEQL_CLI_VERSION": "2.27.0",
        "CODEQL_PACK_VERSION": "codeql/python-queries@1.8.10",
        "EXACT_ANALYZE_COMMAND": (
            "codeql database create /tmp/codeql-db --language=python --source-root=. && "
            "codeql database analyze /tmp/codeql-db "
            "/tmp/codeql/qlpacks/codeql/python-queries/1.8.10/codeql-suites/python-security-and-quality.qls "
            "--format=sarif-latest --output=docs/evidence/codeql-reconciliation/CODEQL_CURRENT_HEAD.sarif"
        ),
        "ORIGINAL_TOTAL": ORIGINAL_TOTAL,
        "RECONCILED_TOTAL": len(records),
        "UNACCOUNTED": unaccounted,
        "DUPLICATE_ACCOUNTED": duplicate_accounted,
        "SECURITY_ORIGINAL": ORIGINAL_SECURITY,
        "SECURITY_RECONCILED": len(sec),
        "SECURITY_OPEN": open_security,
        "QUALITY_ORIGINAL": ORIGINAL_QUALITY,
        "QUALITY_RECONCILED": len(qual),
        "QUALITY_OPEN": open_quality,
        "disposition_totals": dict(sorted(disp.items())),
        "security_disposition_totals": dict(sorted(sec_disp.items())),
        "quality_disposition_totals": dict(sorted(qual_disp.items())),
        "current_sarif_path": str(sarif_path.resolve().relative_to(ROOT.resolve())),
        "current_sarif_total": sarif_count,
        "current_sarif_note": (
            "Post-remediation scan at CURRENT_HEAD; does not replace immutable 911 original corpus."
        ),
        "FINAL_STATUS": status,
        "CODEQL_CLOSED": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export CodeQL 911 institutional reconciliation JSON")
    parser.add_argument("--original-csv", type=Path, default=ROOT / "docs/evidence/blackdark-codeql-original-911.csv")
    parser.add_argument("--final-sarif", type=Path, default=ROOT / "blackdark-codeql-results.sarif")
    parser.add_argument("--current-sarif", type=Path, default=CURRENT_SARIF)
    args = parser.parse_args()

    if not args.original_csv.is_file():
        print(f"Missing original CSV: {args.original_csv}", file=sys.stderr)
        return 1

    current_sha = _git_sha()
    original_rows = _load_original_inventory(args.original_csv)
    sec_count = sum(1 for r in original_rows if float(r.get("security_severity") or 0) > 0)
    qual_count = len(original_rows) - sec_count
    print(f"ORIGINAL_CORPUS_TOTAL={len(original_rows)}")
    print(f"ORIGINAL_SECURITY_TOTAL={sec_count}")
    print(f"ORIGINAL_QUALITY_TOTAL={qual_count}")
    assert len(original_rows) == ORIGINAL_TOTAL == 911
    assert sec_count == ORIGINAL_SECURITY == 38
    assert qual_count == ORIGINAL_QUALITY == 873

    sarif_path = args.current_sarif if args.current_sarif.is_file() else args.final_sarif
    final_sarif = _parse_sarif(sarif_path)
    ledger = build_ledger(original_rows, final_sarif)

    baseline_cache: dict[str, list[str] | None] = {}
    current_cache: dict[str, list[str] | None] = {}

    records: list[dict[str, Any]] = []
    for original, row in zip(original_rows, ledger):
        if original["file"] not in baseline_cache:
            baseline_cache[original["file"]] = _git_show_lines(ORIGINAL_SHA, original["file"])
        if original["file"] not in current_cache:
            current_cache[original["file"]] = _git_show_lines(current_sha, original["file"])
        records.append(
            _enrich_record(
                row,
                original,
                baseline_cache[original["file"]],
                current_cache[original["file"]],
                current_sha,
            )
        )

    disp = Counter(r["final_disposition"] for r in records)
    if sum(disp.values()) != ORIGINAL_TOTAL:
        print("Disposition sum mismatch", file=sys.stderr)
        return 1
    if any(d not in INSTITUTIONAL_DISPOSITIONS for d in disp):
        bad = [d for d in disp if d not in INSTITUTIONAL_DISPOSITIONS]
        print(f"Invalid dispositions: {bad}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_path = OUT_DIR / "CODEQL_911_FINDING_RECONCILIATION.json"
    sec_path = OUT_DIR / "CODEQL_38_SECURITY_RECONCILIATION.json"
    qual_path = OUT_DIR / "CODEQL_873_QUALITY_RECONCILIATION.json"
    summary_path = OUT_DIR / "CODEQL_RECONCILIATION_SUMMARY.json"

    all_payload = {
        "corpus_baseline_sha": ORIGINAL_SHA,
        "current_head_sha": current_sha,
        "original_total": ORIGINAL_TOTAL,
        "reconciled_total": len(records),
        "records": records,
    }
    sec_records = [r for r in records if r["security_classification"] == "security"]
    qual_records = [r for r in records if r["security_classification"] == "quality"]

    hashes = {
        "CODEQL_911_FINDING_RECONCILIATION.json": _write_json(all_path, all_payload),
        "CODEQL_38_SECURITY_RECONCILIATION.json": _write_json(
            sec_path,
            {
                "security_original": ORIGINAL_SECURITY,
                "security_reconciled": len(sec_records),
                "records": sec_records,
            },
        ),
        "CODEQL_873_QUALITY_RECONCILIATION.json": _write_json(
            qual_path,
            {
                "quality_original": ORIGINAL_QUALITY,
                "quality_reconciled": len(qual_records),
                "records": qual_records,
            },
        ),
    }
    summary = _summarize(records, current_sha, sarif_path, len(final_sarif))
    summary["artifact_sha256"] = hashes
    if sarif_path.is_file():
        summary["artifact_sha256"][sarif_path.name] = _sha256(sarif_path)
    hashes["CODEQL_RECONCILIATION_SUMMARY.json"] = _write_json(summary_path, summary)

    print(json.dumps(summary, indent=2))
    print("Artifact SHA256:")
    for name, digest in hashes.items():
        print(f"  {name}: {digest}")
    return 0 if summary["UNACCOUNTED"] == 0 and summary["FINAL_STATUS"] != "BLOCKED_WITH_OPEN_ITEMS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
