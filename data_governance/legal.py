"""Legal applicability register — GLBA and regulatory scope."""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class GLBAStatus(StrEnum):
    APPLICABLE = "DETERMINED_APPLICABLE"
    NOT_APPLICABLE = "DETERMINED_NOT_APPLICABLE"
    LEGAL_REVIEW_REQUIRED = "LEGAL_REVIEW_REQUIRED"


LEGAL_APPLICABILITY_REGISTER: dict[str, Any] = {
    "GLBA_APPLICABILITY_STATUS": GLBAStatus.LEGAL_REVIEW_REQUIRED.value,
    "GDPR_PERSONAL_DATA": "applies_when_personal_data_processed",
    "EU_AI_ACT_ARTICLE_10": "scope_determination_required_per_use_case",
    "BCBS_239": "best_practice_benchmark_not_regulatory_claim",
    "false_regulatory_scope_claims": [],
}


def legal_register_status() -> dict[str, Any]:
    return LEGAL_APPLICABILITY_REGISTER
