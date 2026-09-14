"""Repository PAN / restricted-financial scanning (FDS-05 / FDS-18)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from financial_data.classification import luhn_valid
from financial_data.dlp import scan_text_for_prohibited_patterns

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "financial_data" / "scan_allowlist.json"

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "keys",
    "docs/evidence",
    "bandit_handoff",
}
SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".joblib",
    ".parquet",
    ".db",
    ".sqlite",
    ".woff",
    ".woff2",
    ".pyc",
}
TEXT_SUFFIXES = {".py", ".json", ".jsonl", ".md", ".yml", ".yaml", ".toml", ".env", ".example", ".html", ".js", ".txt", ".sh"}

_PAN_CANDIDATE_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def load_allowlist() -> list[dict[str, str]]:
    if not ALLOWLIST_PATH.is_file():
        return []
    data = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    return list(data.get("entries") or [])


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _allowlisted(rel: str, kind: str, allowlist: list[dict[str, str]]) -> bool:
    for entry in allowlist:
        if entry.get("kind") != kind and entry.get("kind") != "*":
            continue
        pattern = entry.get("path", "")
        if pattern and (rel == pattern or rel.startswith(pattern.rstrip("/") + "/") or pattern in rel):
            return True
    return False


_HARDCODED_SECRET_RE = re.compile(
    r"(?i)(sk_live_[a-zA-Z0-9]{20,}|sk_test_[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|whsec_[a-zA-Z0-9]{10,})"
)


def scan_text_content(text: str, *, rel_path: str, allowlist: list[dict[str, str]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for item in scan_text_for_prohibited_patterns(text):
        kind = item["kind"]
        if kind == "financial_secret":
            continue
        if _allowlisted(rel_path, kind, allowlist):
            continue
        findings.append({"file": rel_path, "kind": kind, **{k: v for k, v in item.items() if k != "kind"}})
    if rel_path.endswith(".example") or "/fixtures/" in rel_path:
        return findings
    for match in _HARDCODED_SECRET_RE.finditer(text):
        kind = "financial_secret"
        if _allowlisted(rel_path, kind, allowlist):
            continue
        findings.append(
            {
                "file": rel_path,
                "kind": kind,
                "offset": str(match.start()),
                "line": str(text.count("\n", 0, match.start()) + 1),
            }
        )
    for match in _PAN_CANDIDATE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group())
        if not luhn_valid(digits):
            continue
        if digits.startswith("411111") or digits.startswith("424242"):
            if _allowlisted(rel_path, "synthetic_test_pan", allowlist):
                continue
        kind = "luhn_pan"
        if _allowlisted(rel_path, kind, allowlist):
            continue
        findings.append(
            {
                "file": rel_path,
                "kind": kind,
                "offset": str(match.start()),
                "length": str(len(digits)),
                "line": str(text.count("\n", 0, match.start()) + 1),
            }
        )
    return findings


def iter_scan_paths(extra_roots: list[Path] | None = None) -> list[Path]:
    paths: list[Path] = []
    roots = [ROOT, *(extra_roots or [])]
    seen: set[str] = set()
    for base in roots:
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = _rel(path)
            if rel in seen:
                continue
            seen.add(rel)
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() in SKIP_SUFFIXES:
                continue
            if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {".env", ".env.production", ".env.staging"}:
                continue
            paths.append(path)
    return sorted(paths)


def scan_repository(extra_roots: list[Path] | None = None) -> dict[str, Any]:
    allowlist = load_allowlist()
    findings: list[dict[str, Any]] = []
    files_scanned = 0
    for path in iter_scan_paths(extra_roots):
        rel = _rel(path)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        files_scanned += 1
        findings.extend(scan_text_content(text, rel_path=rel, allowlist=allowlist))
    secret_report: dict[str, Any] = {"clean": True, "finding_count": 0}
    try:
        from scripts.secrets_hygiene_scan import scan as secret_scan

        secret_findings = secret_scan()
        secret_report = {
            "clean": len(secret_findings) == 0,
            "finding_count": len(secret_findings),
            "findings": [
                {"file": f.get("file"), "line": f.get("line"), "kind": f.get("kind")}
                for f in secret_findings[:50]
            ],
        }
    except Exception as exc:
        secret_report = {"clean": False, "finding_count": -1, "error": str(exc)[:120]}
    clean = len(findings) == 0 and bool(secret_report.get("clean"))
    return {
        "clean": clean,
        "files_scanned": files_scanned,
        "pan_finding_count": len(findings),
        "secret_finding_count": secret_report.get("finding_count", 0),
        "findings": findings[:100],
        "secret_scan": secret_report,
        "allowlist_entries": len(allowlist),
    }
