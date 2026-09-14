"""SDG-12 — synthetic/tokenized test-data policy enforcement."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from financial_data.classification import luhn_valid

ROOT = Path(__file__).resolve().parents[1]

# Visa test PANs permitted in tests only (Stripe/Luhn documentation fixtures).
ALLOWED_SYNTHETIC_PANS = frozenset(
    {
        "4242424242424242",
        "4111111111111111",
        "4000000000000002",
        "4000000000009995",
    }
)

_PAN_CANDIDATE_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")


def is_allowed_synthetic_pan(value: str) -> bool:
    digits = re.sub(r"\D", "", value or "")
    return digits in ALLOWED_SYNTHETIC_PANS


def validate_test_fixture_text(text: str, *, rel_path: str) -> list[dict[str, str]]:
    """Fail closed on non-allowlisted Luhn-valid PANs inside test fixtures."""
    violations: list[dict[str, str]] = []
    if not rel_path.startswith("tests/"):
        return violations
    for match in _PAN_CANDIDATE_RE.finditer(text or ""):
        digits = re.sub(r"\D", "", match.group())
        if not luhn_valid(digits):
            continue
        if is_allowed_synthetic_pan(digits):
            continue
        violations.append(
            {
                "file": rel_path,
                "kind": "non_allowlisted_test_pan",
                "line": str(text.count("\n", 0, match.start()) + 1),
                "length": str(len(digits)),
            }
        )
    return violations


def test_data_policy_status() -> dict[str, Any]:
    return {
        "policy": "SDG-12",
        "allowed_synthetic_pans_count": len(ALLOWED_SYNTHETIC_PANS),
        "enforcement": "tests_only_luhn_pan_allowlist",
    }
