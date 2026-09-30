#!/usr/bin/env python3
"""Generate Launch-57 remediation completion status (FINDING-01..19 rollup)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
OUT_MD = ROOT / "governance" / "launch57" / "LAUNCH57_REMEDIATION_COMPLETION_STATUS.md"
OUT_JSON = ROOT / "governance" / "launch57" / "LAUNCH57_COMPLETION_STATUS.json"

CLOSED_STATUSES = frozenset({"CLOSED", "CLOSED_REPO", "CLOSED_PARTIAL"})


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def _rollup(findings: dict) -> dict:
    counts: dict[str, int] = {}
    for meta in findings.values():
        st = str(meta.get("status", "UNKNOWN"))
        counts[st] = counts.get(st, 0) + 1
    open_ids = [
        fid
        for fid, meta in sorted(findings.items())
        if not str(meta.get("status", "")).startswith("CLOSED")
        and meta.get("status") not in CLOSED_STATUSES
    ]
    partial_ids = [fid for fid, meta in findings.items() if meta.get("status") == "CLOSED_PARTIAL"]
    repo_only = [fid for fid, meta in findings.items() if meta.get("status") == "CLOSED_REPO"]
    engineering_closed = all(
        meta.get("status") in CLOSED_STATUSES or str(meta.get("status", "")).startswith("CLOSED")
        for fid, meta in findings.items()
        if fid not in {"FINDING-01", "FINDING-18", "FINDING-19"}
    )
    return {
        "counts_by_status": counts,
        "open_finding_ids": open_ids,
        "partial_finding_ids": partial_ids,
        "repo_only_finding_ids": repo_only,
        "engineering_track_complete": engineering_closed,
        "program_complete": len(open_ids) == 0 and not partial_ids and not repo_only,
    }


def _md_table(findings: dict) -> str:
    lines = [
        "| Finding | Status | Primary evidence | Remaining closure |",
        "|---------|--------|------------------|-------------------|",
    ]
    for fid in sorted(findings.keys()):
        meta = findings[fid]
        st = meta.get("status", "")
        ev = meta.get("evidence") or []
        paths = [e for e in ev if isinstance(e, str) and not e.startswith(("GET ", "POST "))]
        primary = ", ".join(f"`{p}`" for p in paths[:2])
        if len(paths) > 2:
            primary += f" (+{len(paths) - 2})"
        rem = meta.get("closure_requires") or meta.get("note") or "—"
        lines.append(f"| {fid} | {st} | {primary or '—'} | {rem} |")
    return "\n".join(lines)


def main() -> int:
    if not INDEX.is_file():
        print(f"missing {INDEX}", file=sys.stderr)
        return 1
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    findings = index.get("findings") or {}
    if len(findings) != 19:
        print(f"WARN: expected 19 findings, got {len(findings)}", file=sys.stderr)
    rollup = _rollup(findings)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": _git_head(),
        "baseline_sha": index.get("baseline_sha"),
        "remediation_sha": index.get("remediation_sha"),
        "phase": index.get("phase"),
        "cisa_certification_claimed": False,
        "rollup": rollup,
        "findings": findings,
        "navigation": {
            "evidence_index": str(INDEX.relative_to(ROOT)),
            "open_register": index.get("open_findings_register"),
            "ops_playbook": index.get("ops_playbook"),
            "program": "docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    md = f"""# Launch-57 — CISA remediation completion status

**Generated:** {payload["generated_at"]}  
**Baseline SHA:** `{index.get("baseline_sha")}`  
**Remediation SHA:** `{index.get("remediation_sha")}`  
**Phase:** `{index.get("phase")}`

> **Honesty:** This is an engineering/ops status rollup. It does **not** claim CISA certification, pledge completion, or independent pentest unless each finding row shows full closure with verified ops evidence.

## Rollup

| Metric | Value |
|--------|-------|
| Findings in inventory | {len(findings)} |
| Engineering track (excl. 01/18/19 ops) | {"PASS" if rollup["engineering_track_complete"] else "INCOMPLETE"} |
| Open / executive / ops IDs | {", ".join(rollup["open_finding_ids"]) or "none"} |
| Partial (SBOM container gap) | {", ".join(rollup["partial_finding_ids"]) or "none"} |
| Repo-only (prod verify pending) | {", ".join(rollup["repo_only_finding_ids"]) or "none"} |
| Whole program closed | {"no" if not rollup["program_complete"] else "yes"} |

## Finding matrix

{_md_table(findings)}

## Verification commands

```bash
python scripts/verify_launch57_repo_evidence.py
python scripts/launch57_closure_report.py
python scripts/launch57_ops_closure_gate.py   # production
```

## Regenerate

```bash
python scripts/generate_launch57_completion_status.py
```
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
