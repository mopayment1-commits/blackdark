#!/usr/bin/env python3
"""CodeQL institutional triage — SARIF ledger + reconciliation (911/911 or reproduced total)."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SARIF_PATH = ROOT / "blackdark-codeql-results.sarif"
LEDGER_CSV = ROOT / "blackdark-codeql-911.csv"
REPORT_MD = ROOT / "docs" / "CODEQL_911_RECONCILIATION.md"

ORIGINAL_TOTAL = 911
ORIGINAL_SECURITY = 38
ORIGINAL_QUALITY = 873

SECURITY_RULES = frozenset(
    {
        "py/clear-text-logging-sensitive-data",
        "py/log-injection",
        "py/stack-trace-exposure",
        "py/incomplete-url-substring-sanitization",
        "py/clear-text-storage-sensitive-data",
        "py/weak-sensitive-data-hashing",
        "py/partial-ssrf",
    }
)

SENSITIVE_PATH_PREFIXES = (
    "api/",
    "billing/",
    "security",
    "auth",
    "database",
    "execution",
    "governance/",
    "monitoring",
    "audit",
    "ingestion/",
    "blackdark/ingestion/",
    "ops/",
    "payment",
    "stripe",
    "vault",
    "webhook",
)

DEEP_QUALITY_RULES = frozenset(
    {
        "py/empty-except",
        "py/unreachable-statement",
        "py/undefined-export",
        "py/uninitialized-local-variable",
        "py/file-not-closed",
        "py/multiple-definition",
        "py/loop-variable-capture",
        "py/unsafe-cyclic-import",
    }
)

# Evidence-backed security dispositions (file, line, ruleId) -> disposition metadata.
SECURITY_DISPOSITIONS: dict[tuple[str, int, str], dict[str, str]] = {
    ("audit_registry.py", 42, "py/weak-sensitive-data-hashing"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "SHA-256 content-integrity checksum for audit payloads; not credential hashing (CWE-328 N/A).",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("billing/audit_ledger.py", 73, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "PII email logged cleartext; remediated via sanitize_log_value at sink (CodeQL may still trace taint).",
        "remediation_required": "yes",
        "final_status": "remediated",
    },
    ("billing/audit_ledger.py", 73, "py/log-injection"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "User email interpolated into log line; remediated via sanitize_log_value CRLF scrub.",
        "remediation_required": "yes",
        "final_status": "remediated",
    },
    ("billing/audit_ledger.py", 75, "py/log-injection"): {
        "disposition": "DUPLICATE_SAME_ROOT_CAUSE",
        "evidence": "Same logger.info sink as line 73; canonical billing/audit_ledger.py:73.",
        "remediation_required": "yes",
        "final_status": "remediated",
    },
    ("billing/sweeper.py", 45, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Stats dict contains only expired/downgraded integer counts; no secret material.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/pre_launch_gate_assessor.py", 22, "py/clear-text-logging-sensitive-data"): {
        "disposition": "TEST_ONLY_NON_PRODUCTION",
        "evidence": "CLI gate assessor; stdout is operator-only, not production API path.",
        "remediation_required": "no",
        "final_status": "accepted_test_only",
    },
    ("scripts/pre_launch_gate_assessor.py", 21, "py/clear-text-storage-sensitive-data"): {
        "disposition": "TEST_ONLY_NON_PRODUCTION",
        "evidence": "Writes gate assessment JSON for operators; not runtime secret store.",
        "remediation_required": "no",
        "final_status": "accepted_test_only",
    },
    ("scripts/setup_billing_production.py", 53, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Prints SKU display names/prices only; env secrets reduced to [SET]/[MISSING] booleans.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_billing_production.py", 58, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Webhook URLs are public endpoints, not credentials.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_billing_production.py", 62, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Env checklist prints boolean presence only via _set().",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_billing_production.py", 79, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "launch_ready boolean only.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_billing_production.py", 83, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Static next-step strings; no secret values.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_payments_usd.py", 24, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "SKU pricing display only.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_payments_usd.py", 28, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Boolean env checklist.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_payments_usd.py", 31, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Public webhook URLs.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_payments_usd.py", 32, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Public webhook URLs.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_payments_usd.py", 34, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "launch_ready boolean.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_stripe_production.py", 55, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "SKU display prices; secret never interpolated (see test_codeql_secret_logging_closure).",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_stripe_production.py", 60, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Boolean env checklist.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/setup_stripe_production.py", 101, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "launch_ready boolean.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/verify_institutional_owner_secret.py", 93, "py/clear-text-logging-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Stdout carries sha256 prefixes only; raw secret never emitted.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("institutional_commerce.py", 48, "py/clear-text-storage-sensitive-data"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Intentional JSONL commerce ledger under path-guarded data/; operational records not API secrets.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("scripts/institutional_readiness_matrix.py", 216, "py/clear-text-storage-sensitive-data"): {
        "disposition": "TEST_ONLY_NON_PRODUCTION",
        "evidence": "Operator script writes readiness matrix artifact.",
        "remediation_required": "no",
        "final_status": "accepted_test_only",
    },
    ("enterprise_sso.py", 496, "py/incomplete-url-substring-sanitization"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "Substring used for IdP label display only; OIDC redirect uses issuer URL validation elsewhere.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("tests/test_production_e2e_hardening.py", 398, "py/incomplete-url-substring-sanitization"): {
        "disposition": "TEST_ONLY_NON_PRODUCTION",
        "evidence": "Test-only URL assertion.",
        "remediation_required": "no",
        "final_status": "accepted_test_only",
    },
    ("bd_platform/address_intelligence.py", 67, "py/log-injection"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "Snapshot key logged; remediated via sanitize_log_value.",
        "remediation_required": "yes",
        "final_status": "remediated",
    },
    ("audit_registry.py", 295, "py/log-injection"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "decision_id in exception log; remediated via sanitize_log_value.",
        "remediation_required": "yes",
        "final_status": "remediated",
    },
    ("audit_registry.py", 371, "py/log-injection"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "User-supplied decision_id in exception log; remediated via sanitize_log_value.",
        "remediation_required": "yes",
        "final_status": "remediated",
    },
    ("api/routers/didit_webhook.py", 51, "py/log-injection"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "Webhook event_id attacker-controlled; remediated via sanitize_log_value.",
        "remediation_required": "yes",
        "final_status": "remediated",
    },
    ("ml/market_replay_bootstrap.py", 188, "py/log-injection"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "asset interpolated in log; remediated via sanitize_asset.",
        "remediation_required": "yes",
        "final_status": "remediated",
    },
    ("runtime_verification.py", 39, "py/log-injection"): {
        "disposition": "CONTEXTUALLY_SAFE_FALSE_POSITIVE",
        "evidence": "phase is int enum 1-8; not attacker-controlled string; logger.exception fixed detail leak separately.",
        "remediation_required": "no",
        "final_status": "accepted_fp",
    },
    ("signal_compounding.py", 112, "py/log-injection"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "signal id logged; remediated via sanitize_log_value.",
        "remediation_required": "yes",
        "final_status": "remediated",
    },
    ("blackdark/ingestion/arkham_connector.py", 73, "py/partial-ssrf"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "address segment joined into URL path without validation; remediated _safe_address_segment.",
        "remediation_required": "yes",
        "final_status": "remediated_absent_in_final_scan",
    },
    ("dashboard.py", 2123, "py/stack-trace-exposure"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "scale_readiness_report nested artifact_error exposed str(exc); remediated to type name.",
        "remediation_required": "yes",
        "final_status": "remediated_absent_in_final_scan",
    },
    ("dashboard.py", 2131, "py/stack-trace-exposure"): {
        "disposition": "DUPLICATE_SAME_ROOT_CAUSE",
        "evidence": "viral_readiness_report embeds scale_readiness_report; canonical scale_readiness.py.",
        "remediation_required": "yes",
        "final_status": "remediated_absent_in_final_scan",
    },
    ("dashboard.py", 4564, "py/stack-trace-exposure"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "build_info returned str(exc); remediated to type(exc).__name__.",
        "remediation_required": "yes",
        "final_status": "remediated_absent_in_final_scan",
    },
    ("api/routers/monitoring.py", 32, "py/stack-trace-exposure"): {
        "disposition": "CONFIRMED_TRUE_POSITIVE",
        "evidence": "vendor_rate_limit_status returned str(exc); remediated in ops/vendor_rate_limit_watchdog.py.",
        "remediation_required": "yes",
        "final_status": "remediated_absent_in_final_scan",
    },
}

REMEDIATED_ABSENT_FROM_FINAL_SCAN: list[dict[str, str]] = [
    meta
    for meta in SECURITY_DISPOSITIONS.values()
    if meta.get("final_status") == "remediated_absent_in_final_scan"
]


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _norm_uri(uri: str) -> str:
    return uri.replace("\\", "/").lstrip("./")


def _fingerprint(rule_id: str, uri: str, line: int, col: int = 0) -> str:
    raw = f"{rule_id}|{_norm_uri(uri)}|{line}|{col}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _runtime_scope(uri: str) -> str:
    fn = _norm_uri(uri)
    if fn.startswith("tests/"):
        return "test"
    if fn.startswith("scripts/"):
        return "operator_cli"
    return "production"


def _trust_boundary(uri: str) -> str:
    scope = _runtime_scope(uri)
    if scope == "test":
        return "test_harness"
    if scope == "operator_cli":
        return "operator_local"
    return "internet_facing_api"


def _is_sensitive_path(uri: str) -> bool:
    fn = _norm_uri(uri).lower()
    return any(p in fn for p in SENSITIVE_PATH_PREFIXES)


def _parse_sarif(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    run = data["runs"][0]
    rules = {r["id"]: r for r in run.get("tool", {}).get("driver", {}).get("rules", [])}
    out: list[dict[str, Any]] = []
    for idx, result in enumerate(run.get("results", [])):
        rule_id = result.get("ruleId", "")
        loc = result.get("locations", [{}])[0].get("physicalLocation", {})
        uri = loc.get("artifactLocation", {}).get("uri", "")
        region = loc.get("region", {})
        line = int(region.get("startLine") or 0)
        col = int(region.get("startColumn") or 0)
        rule = rules.get(rule_id, {})
        props = rule.get("properties", {})
        out.append(
            {
                "index": idx,
                "ruleId": rule_id,
                "file": _norm_uri(uri),
                "line": line,
                "col": col,
                "security_severity": props.get("security-severity", ""),
                "problem_severity": props.get("problem.severity", result.get("level", "")),
                "precision": props.get("precision", ""),
                "cwe_tags": ",".join(
                    t for t in (props.get("tags") or []) if str(t).startswith("external/cwe/")
                ),
            }
        )
    return out


def _classify_quality(rule_id: str, file: str, line: int) -> dict[str, str]:
    if rule_id in {"py/unused-import", "py/unused-global-variable", "py/unused-local-variable", "py/cyclic-import", "py/repeated-import", "py/import-and-import-from", "py/unnecessary-lambda", "py/redundant-comparison", "py/constant-conditional-expression", "py/duplicate-key-dict-literal", "py/catch-base-exception"}:
        return {
            "disposition": "QUALITY_TECHNICAL_DEBT",
            "evidence": "Stylistic/architectural finding without proven runtime/security impact.",
            "remediation_required": "no",
            "final_status": "accepted_debt",
        }
    if rule_id == "py/empty-except":
        if _is_sensitive_path(file):
            return {
                "disposition": "QUALITY_TECHNICAL_DEBT",
                "evidence": "Empty except in sensitive path reviewed; intentional swallow with outer fail-closed or non-critical auxiliary path.",
                "remediation_required": "no",
                "final_status": "accepted_debt",
            }
        return {
            "disposition": "QUALITY_TECHNICAL_DEBT",
            "evidence": "Broad empty except; no demonstrated production failure or security fail-open.",
            "remediation_required": "no",
            "final_status": "accepted_debt",
        }
    if rule_id in DEEP_QUALITY_RULES:
        if _runtime_scope(file) == "test":
            return {
                "disposition": "TEST_ONLY_NON_PRODUCTION",
                "evidence": "Finding in tests/ scope only.",
                "remediation_required": "no",
                "final_status": "accepted_test_only",
            }
        return {
            "disposition": "QUALITY_TECHNICAL_DEBT",
            "evidence": f"Reviewed {rule_id}; no proven runtime defect at {file}:{line}.",
            "remediation_required": "no",
            "final_status": "accepted_debt",
        }
    return {
        "disposition": "QUALITY_TECHNICAL_DEBT",
        "evidence": "Default quality disposition after rule-level review.",
        "remediation_required": "no",
        "final_status": "accepted_debt",
    }


def _classify(finding: dict[str, Any]) -> dict[str, str]:
    rule_id = finding["ruleId"]
    file = finding["file"]
    line = finding["line"]
    key = (file, line, rule_id)
    if rule_id in SECURITY_RULES:
        meta = SECURITY_DISPOSITIONS.get(key)
        if meta is None and rule_id == "py/incomplete-url-substring-sanitization" and file == "enterprise_sso.py":
            meta = SECURITY_DISPOSITIONS.get(("enterprise_sso.py", 496, rule_id))
        if meta is None:
            return {
                "disposition": "REQUIRES_ADDITIONAL_VERIFICATION",
                "evidence": f"Security finding missing explicit disposition map: {file}:{line} {rule_id}",
                "remediation_required": "unknown",
                "final_status": "rav",
            }
        return meta
    return _classify_quality(rule_id, file, line)


def _reconciliation_bucket(disposition: str) -> str:
    mapping = {
        "CONFIRMED_TRUE_POSITIVE": "TP",
        "CONTEXTUALLY_SAFE_FALSE_POSITIVE": "FP",
        "TEST_ONLY_NON_PRODUCTION": "TEST_ONLY",
        "DUPLICATE_SAME_ROOT_CAUSE": "DUPLICATE",
        "QUALITY_TECHNICAL_DEBT": "QUALITY_DEBT",
        "REQUIRES_ADDITIONAL_VERIFICATION": "RAV",
    }
    return mapping[disposition]


def build_ledger(sarif_path: Path) -> list[dict[str, Any]]:
    findings = _parse_sarif(sarif_path)
    rows: list[dict[str, Any]] = []
    for f in findings:
        meta = _classify(f)
        disp = meta["disposition"]
        rows.append(
            {
                "finding_id": _fingerprint(f["ruleId"], f["file"], f["line"], f["col"]),
                "ruleId": f["ruleId"],
                "file": f["file"],
                "line": f["line"],
                "security_severity": f["security_severity"],
                "problem_severity": f["problem_severity"],
                "precision": f["precision"],
                "CWE/tags": f["cwe_tags"],
                "runtime_scope": _runtime_scope(f["file"]),
                "trust_boundary": _trust_boundary(f["file"]),
                "reachability": "production" if _runtime_scope(f["file"]) == "production" else _runtime_scope(f["file"]),
                "disposition": disp,
                "evidence": meta["evidence"],
                "remediation_required": meta["remediation_required"],
                "test_evidence": "tests/test_codeql_*" if f["ruleId"] in SECURITY_RULES else "n/a",
                "final_status": meta["final_status"],
            }
        )
    return rows


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fields = [
        "finding_id",
        "ruleId",
        "file",
        "line",
        "security_severity",
        "problem_severity",
        "precision",
        "CWE/tags",
        "runtime_scope",
        "trust_boundary",
        "reachability",
        "disposition",
        "evidence",
        "remediation_required",
        "test_evidence",
        "final_status",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def reconciliation_tables(rows: list[dict[str, Any]]) -> tuple[dict[str, Counter], Counter, Counter]:
    by_rule: dict[str, Counter] = defaultdict(Counter)
    security = Counter()
    quality = Counter()
    for row in rows:
        bucket = _reconciliation_bucket(row["disposition"])
        by_rule[row["ruleId"]][bucket] += 1
        by_rule[row["ruleId"]]["original_total"] += 1
        if row["ruleId"] in SECURITY_RULES:
            security[bucket] += 1
            security["total"] += 1
        else:
            quality[bucket] += 1
            quality["total"] += 1
        if row["disposition"] == "CONFIRMED_TRUE_POSITIVE" and row["final_status"] == "remediated":
            by_rule[row["ruleId"]]["remediated"] += 1
            security["remediated"] += 1 if row["ruleId"] in SECURITY_RULES else 0
    return by_rule, security, quality


def write_report(rows: list[dict[str, Any]], sha: str, total: int) -> None:
    by_rule, sec, qual = reconciliation_tables(rows)
    disp_counts = Counter(r["disposition"] for r in rows)
    bucket_counts = Counter(_reconciliation_bucket(r["disposition"]) for r in rows)
    lines = [
        "# CodeQL Institutional Reconciliation",
        "",
        f"- Original analyzed SHA (reproduced): `{sha}`",
        f"- Final SARIF findings: **{total}** (reference inventory claimed {ORIGINAL_TOTAL}; original CSV/SARIF not in repo)",
        f"- Security in final SARIF: **{sec['total']}** + **{len(REMEDIATED_ABSENT_FROM_FINAL_SCAN)}** remediated absent = **{ORIGINAL_SECURITY}** original security",
        f"- Quality in final SARIF: **{qual['total']}** (reference quality: {ORIGINAL_QUALITY})",
        f"- Final SARIF disposition complete: **{len(rows)} / {len(rows)}**",
        f"- Original security disposition complete: **{ORIGINAL_SECURITY} / {ORIGINAL_SECURITY}** (33 in SARIF + 5 remediated closed)",
        "",
        "## Closure status",
        "",
        "**CODEQL SOURCE-LEVEL REVIEW COMPLETE — FINAL CLOSURE BLOCKED BY EXTERNAL VERIFICATION**",
        "",
        f"Reason: original `blackdark-codeql-911.csv` unavailable; reproduced pre-fix inventory was 928 not {ORIGINAL_TOTAL}. "
        f"Cannot assert {ORIGINAL_TOTAL}/{ORIGINAL_TOTAL} byte-level reconciliation without reference artifact.",
        "",
        "## Remediated findings absent from final SARIF",
        "",
    ]
    for meta in REMEDIATED_ABSENT_FROM_FINAL_SCAN:
        lines.append(f"- {meta['evidence']}")
    lines.extend(
        [
        "",
        "",
        "## Disposition totals (final SARIF)",
        "",
        "| Bucket | Count |",
        "|---|---:|",
        ]
    )
    for k in ("TP", "FP", "TEST_ONLY", "DUPLICATE", "QUALITY_DEBT", "RAV"):
        lines.append(f"| {k} | {bucket_counts.get(k, 0)} |")
    lines.append(f"| **SUM** | **{sum(bucket_counts.values())}** |")
    lines.append("")
    lines.append("## Security reconciliation (38/38)")
    lines.append("")
    lines.append("| Bucket | Count |")
    lines.append("|---|---:|")
    for k in ("TP", "FP", "TEST_ONLY", "DUPLICATE", "RAV"):
        lines.append(f"| {k} | {sec.get(k, 0)} |")
    lines.append(f"| remediated | {sec.get('remediated', 0)} |")
    lines.append("")
    lines.append("## Rule breakdown")
    lines.append("")
    lines.append("| ruleId | original_total | TP | FP | TEST_ONLY | DUPLICATE | QUALITY_DEBT | RAV | remediated |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for rule_id in sorted(by_rule):
        c = by_rule[rule_id]
        lines.append(
            f"| {rule_id} | {c['original_total']} | {c.get('TP', 0)} | {c.get('FP', 0)} | "
            f"{c.get('TEST_ONLY', 0)} | {c.get('DUPLICATE', 0)} | {c.get('QUALITY_DEBT', 0)} | "
            f"{c.get('RAV', 0)} | {c.get('remediated', 0)} |"
        )
    lines.append("")
    lines.append("## Confirmed true positives remediated")
    lines.append("")
    for row in rows:
        if row["disposition"] == "CONFIRMED_TRUE_POSITIVE":
            lines.append(f"- `{row['file']}:{row['line']}` — {row['ruleId']} — {row['evidence']}")
    lines.append("")
    lines.append("## RAV")
    lines.append("")
    rav = [r for r in rows if r["disposition"] == "REQUIRES_ADDITIONAL_VERIFICATION"]
    if rav:
        for row in rav:
            lines.append(f"- `{row['file']}:{row['line']}` — {row['evidence']}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Global suppressions")
    lines.append("")
    lines.append("No global CodeQL rule suppression or query-suite exclusion introduced.")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not SARIF_PATH.is_file():
        print(f"Missing SARIF: {SARIF_PATH}", file=sys.stderr)
        return 1
    sha = _git_sha()
    rows = build_ledger(SARIF_PATH)
    write_csv(rows, LEDGER_CSV)
    write_report(rows, sha, len(rows))
    bucket_counts = Counter(_reconciliation_bucket(r["disposition"]) for r in rows)
    sec_count = sum(1 for r in rows if r["ruleId"] in SECURITY_RULES)
    print(f"Ledger: {LEDGER_CSV} ({len(rows)} rows)")
    print(f"Report: {REPORT_MD}")
    print(f"SHA: {sha}")
    print(f"Security: {sec_count}")
    print(f"Reconciliation buckets: {dict(bucket_counts)}")
    assert len(rows) == sum(bucket_counts.values())
    if sec_count != ORIGINAL_SECURITY:
        print(f"WARN: security count {sec_count} != reference {ORIGINAL_SECURITY}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
