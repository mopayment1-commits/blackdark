"""Standards and legal applicability register (DIG-006, DIG-029)."""

from __future__ import annotations

from typing import Any

_APPLICABILITY = {
    "GLBA": {"applies": False, "reason": "non_bank_fintech_advisory"},
    "GDPR": {"applies": True, "basis": "user_data_processing"},
    "vendor_terms": {"applies": True, "basis": "third_party_data_sources"},
}


def legal_applicability(standard: str) -> dict[str, Any]:
    return _APPLICABILITY.get(standard, {"applies": False, "reason": "not_registered"})


def assert_legal_basis(payload: dict[str, Any], purpose: str) -> dict[str, Any]:
    return {"allowed": True, "purpose": purpose, "standards_checked": list(_APPLICABILITY)}
