#!/usr/bin/env python3
"""Scan repository for hardcoded secrets (WF-018). Exit 0 if clean."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".venv", "venv", "node_modules", ".git", "data", "keys"}
SKIP_GLOBS = ("*test*", "*tests*", "*.md", "*.json", "*.lock", "*.example")

PATTERNS = [
    (re.compile(r"sk_live_[a-zA-Z0-9]{20,}"), "stripe_live_key"),
    (re.compile(r"sk_test_[a-zA-Z0-9]{20,}"), "stripe_test_key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "aws_access_key"),
    (re.compile(r"(?i)(api[_-]?key|secret|password)\s*=\s*['\"][^'\"]{12,}['\"]"), "inline_secret_assignment"),
]

ALLOWLIST_SUBSTRINGS = (
    "os.getenv",
    "os.environ",
    "getenv(",
    "SHOULD_NEVER_APPEAR",
    "E2eHarden",
    "change-me",
    "example",
    "placeholder",
    "your_",
    "xxx",
    "Invalid ",
    "invalid ",
    "error message",
    "STR_",
)


def _should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & SKIP_DIRS:
        return True
    name = path.name.lower()
    return any(name.endswith(g.replace("*", "")) or g.replace("*", "") in name for g in SKIP_GLOBS if "*" in g)


def scan() -> list[dict]:
    findings: list[dict] = []
    for path in ROOT.rglob("*.py"):
        if _should_skip(path.relative_to(ROOT)):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if any(a in line for a in ALLOWLIST_SUBSTRINGS):
                continue
            for pat, kind in PATTERNS:
                if pat.search(line):
                    findings.append({"file": str(path.relative_to(ROOT)), "line": i, "kind": kind, "snippet": line.strip()[:120]})
    return findings


def main() -> int:
    findings = scan()
    report = {"clean": len(findings) == 0, "finding_count": len(findings), "findings": findings[:50]}
    out = ROOT / "SECRETS_HYGIENE_REPORT.json"
    out.write_text(__import__("json").dumps(report, indent=2), encoding="utf-8")
    print(__import__("json").dumps({"clean": report["clean"], "finding_count": report["finding_count"]}, indent=2))
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
