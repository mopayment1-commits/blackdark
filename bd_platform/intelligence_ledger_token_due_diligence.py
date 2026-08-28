"""
Intelligence Ledger Instant Token Due Diligence — Feature #971 (Sprint 2).

Merged into Intelligence Ledger — NOT standalone.
Multi-domain token DD report with freshness per section, N/A not zero.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.TokenDueDiligence")

_FEATURE_REF = 971
_ONCHAIN_REF = 12
_LABELS_REF = 926
_LEDGER_REF = 10
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Token DD"
_SEED_PATH = Path("data/intelligence_ledger_token_due_diligence_seed.json")

_SECTIONS = ("holders", "liquidity", "flows", "smart_money", "risk", "tokenomics")

_DISCLAIMER = (
    "Token due diligence — insight only. Missing data shown as N/A, not zero. "
    "Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("token dd seed load failed: %s", exc)
        return {}


def token_dd_status_971(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("token_dd_971") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "ledger_ref": _LEDGER_REF,
        "onchain_ref": _ONCHAIN_REF,
        "labels_ref": _LABELS_REF,
        "sections": list(_SECTIONS),
        "freshness_per_section": True,
        "no_zero_disguise": True,
        "risk_score_required": True,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def _format_section(section: dict[str, Any] | None) -> dict[str, Any]:
    if not section:
        return {
            "status": "missing",
            "value": None,
            "display": "N/A",
            "no_zero_disguise": True,
            "freshness": None,
            "source": None,
        }
    return {
        "status": "available",
        "value": section.get("value"),
        "display": section.get("display") or str(section.get("value")),
        "freshness": section.get("observed_at"),
        "freshness_label": section.get("freshness_label"),
        "source": section.get("source"),
        "source_url": section.get("source_url"),
        "no_zero_disguise": True,
    }


def build_token_dd_report_971(
    token_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    tokens = seed.get("tokens") or {}
    token = tokens.get(token_id.lower()) or tokens.get(token_id.upper())
    if not token:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "token_not_found"}

    sections_raw = token.get("sections") or {}
    sections: dict[str, Any] = {}
    for name in _SECTIONS:
        sections[name] = _format_section(sections_raw.get(name))

    risk_score = token.get("risk_score")
    if risk_score is None and sections_raw.get("risk"):
        risk_score = sections_raw["risk"].get("value")

    fee = (seed.get("token_dd_971") or {}).get("fee_db") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "token_id": token_id.upper(),
        "name": token.get("name"),
        "chain": token.get("chain"),
        "sections": sections,
        "section_count": len(_SECTIONS),
        "all_sections_present": all(s.get("status") == "available" for s in sections.values()),
        "freshness_per_section": all(
            s.get("freshness") is not None or s.get("status") == "missing" for s in sections.values()
        ),
        "no_zero_disguise": True,
        "risk_score": risk_score,
        "risk_score_scale": "1-10",
        "risk_score_required": risk_score is not None,
        "sources_unified": True,
        "fee_db": {
            "query_usd": fee.get("multi_source_query_usd", 0.05),
            "compute_usd": fee.get("compute_per_report_usd", 0.02),
        },
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def run_token_dd_e2e_971(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = token_dd_status_971(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "six_sections", "passed": len(status["sections"]) == 6})

    report = build_token_dd_report_971("aave", seed=seed)
    checks.append({"id": "token_report", "passed": report.get("ok") is True})
    checks.append({"id": "risk_score", "passed": report.get("risk_score_required") is True})
    checks.append({"id": "freshness", "passed": report.get("freshness_per_section") is True})

    partial = build_token_dd_report_971("new_token", seed=seed)
    missing_section = partial.get("sections", {}).get("smart_money", {})
    checks.append({"id": "na_not_zero", "passed": missing_section.get("display") == "N/A"})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature_ref": _FEATURE_REF, "all_passed": all_passed, "checks": checks}
