"""PAN/CVV/secret pattern detection and payload rejection."""

from __future__ import annotations

import re
from typing import Any

from financial_data_security.classification import FORBIDDEN_STORAGE_FIELDS

# Luhn-valid PAN candidates (13-19 digits, optional separators)
_PAN_CANDIDATE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_CVV_CANDIDATE = re.compile(r"\b(?<!\d)(\d{3,4})(?!\d)\b")
_SECRET_PATTERNS = (
    re.compile(r"sk_(live|test)_[A-Za-z0-9]{16,}"),
    re.compile(r"rk_(live|test)_[A-Za-z0-9]{16,}"),
    re.compile(r"whsec_[A-Za-z0-9]{16,}"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
)


def luhn_check(number: str) -> bool:
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def find_pan_candidates(text: str) -> list[str]:
    hits: list[str] = []
    for match in _PAN_CANDIDATE.finditer(text or ""):
        raw = match.group(0)
        digits = re.sub(r"\D", "", raw)
        if luhn_check(digits):
            hits.append(digits[-4:].rjust(len(digits), "*"))
    return hits


def scan_text_for_restricted_data(text: str) -> dict[str, Any]:
    pans = find_pan_candidates(text or "")
    secrets = [p.pattern[:20] for p in _SECRET_PATTERNS if p.search(text or "")]
    return {
        "pan_detected": bool(pans),
        "pan_masked_samples": pans[:3],
        "secret_pattern_detected": bool(secrets),
        "blocked": bool(pans) or bool(secrets),
    }


def scan_mapping_for_forbidden_fields(data: dict[str, Any], *, prefix: str = "") -> list[str]:
    violations: list[str] = []
    for key, value in (data or {}).items():
        k = str(key).lower().strip()
        path = f"{prefix}.{k}" if prefix else k
        if k in FORBIDDEN_STORAGE_FIELDS:
            violations.append(path)
        if isinstance(value, dict):
            violations.extend(scan_mapping_for_forbidden_fields(value, prefix=path))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    violations.extend(scan_mapping_for_forbidden_fields(item, prefix=f"{path}[{i}]"))
                elif isinstance(item, str):
                    sub = scan_text_for_restricted_data(item)
                    if sub["blocked"]:
                        violations.append(f"{path}[{i}]")
    return violations


def reject_forbidden_financial_payload(data: dict[str, Any]) -> None:
    violations = scan_mapping_for_forbidden_fields(data)
    if violations:
        raise ValueError(f"Forbidden financial fields rejected: {', '.join(violations[:5])}")
    blob = str(data)
    scan = scan_text_for_restricted_data(blob)
    if scan["pan_detected"]:
        raise ValueError("Forbidden PAN-like data rejected at ingress")


def scan_repository_paths(paths: list[str] | None = None) -> dict[str, Any]:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    scan_dirs = paths or ["financial_data_security", "api/routers/billing.py", "billing"]
    hits: list[str] = []
    for rel in scan_dirs:
        p = root / rel
        targets = [p] if p.is_file() else list(p.rglob("*.py")) if p.is_dir() else []
        for fp in targets:
            if "test" in fp.name:
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if scan_text_for_restricted_data(text)["pan_detected"]:
                hits.append(str(fp.relative_to(root)))
    return {"paths_scanned": scan_dirs, "pan_hits": hits, "pass": not hits}
