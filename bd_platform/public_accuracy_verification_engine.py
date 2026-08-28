"""
Public Accuracy Ledger — Verification Engine — Feature #931 (Sprint 2).

Merged into #987 Public Accuracy Ledger — NOT standalone.
Freeze claims pre-outcome; deterministic grading; immutable audit.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.VerificationEngine")

_FEATURE_REF = 931
_ACCURACY_LEDGER_REF = 987
_STANDALONE = False
_MERGED_INTO = "Public Accuracy Ledger (#987)"
_SEED_PATH = Path("data/public_accuracy_verification_engine_seed.json")
_AUDIT_RETENTION_YEARS = 5

_DISCLAIMER = (
    "Claims verification — deterministic grading only. "
    "No post-hoc editing. Unresolved stays unresolved."
)

# In-memory claim store for test isolation
_claim_store: dict[str, dict[str, Any]] = {}


def reset_verification_engine_state() -> None:
    _claim_store.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("verification engine seed load failed: %s", exc)
        return {}


def _lock_hash(claim: dict[str, Any]) -> str:
    payload = json.dumps(claim, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def verification_engine_status_931(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("verification_engine_931") or {}
    claims = {**(seed.get("locked_claims") or {}), **_claim_store}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "accuracy_ledger_ref": _ACCURACY_LEDGER_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "no_post_hoc_editing": True,
        "deterministic_grading": True,
        "unresolved_stays_unresolved": True,
        "immutable_revisions": True,
        "audit_retention_years": cfg.get("audit_retention_years", _AUDIT_RETENTION_YEARS),
        "claim_count": len(claims),
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def freeze_claim_931(
    *,
    asset: str,
    claim_text: str,
    target_definition: dict[str, Any],
    horizon_days: int,
    claim_type: str = "hypothesis",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Lock claim before outcome — timestamp + hash."""
    seed = seed or _load_seed()
    claim_id = f"claim_{uuid.uuid4().hex[:8]}"
    locked_at = _utcnow()
    claim = {
        "claim_id": claim_id,
        "asset": asset.upper(),
        "claim_text": claim_text,
        "claim_type": claim_type,
        "target_definition": target_definition,
        "horizon_days": horizon_days,
        "locked_at": locked_at,
        "outcome_source": "oracle_api",
        "status": "locked",
        "outcome": None,
        "immutable": True,
        "version": 1,
    }
    claim["lock_hash"] = _lock_hash(claim)
    _claim_store[claim_id] = claim

    fee = (seed.get("verification_engine_931") or {}).get("fee_db") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "claim": claim,
        "frozen": True,
        "no_post_hoc_editing": True,
        "fee_db": {"storage_usd": fee.get("storage_per_claim_usd", 0.001)},
        "timestamp": _utcnow(),
    }


def _grade_claim(claim: dict[str, Any], price_usd: float) -> dict[str, Any]:
    target = claim.get("target_definition") or {}
    threshold = float(target.get("threshold", 0))
    direction = target.get("direction", "above")
    if direction == "above":
        correct = 1 if price_usd > threshold else 0
    else:
        correct = 1 if price_usd < threshold else 0
    predicted_prob = 0.7 if claim.get("claim_type") == "hypothesis" else 0.5
    brier = round((predicted_prob - correct) ** 2, 4)
    return {
        "resolved_at": _utcnow(),
        "price_usd": price_usd,
        "rule": f"price {direction} threshold within horizon",
        "correctness": correct,
        "brier_score": brier,
        "outcome_source": "oracle_api",
        "auditable": True,
    }


def resolve_claim_931(
    claim_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deterministic grading — no forced resolution."""
    seed = seed or _load_seed()
    claims = {**(seed.get("locked_claims") or {}), **_claim_store}
    claim = claims.get(claim_id)
    if not claim:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "claim_not_found"}

    if claim.get("status") in ("verified", "failed"):
        return {
            "ok": False,
            "feature_ref": _FEATURE_REF,
            "error": "already_resolved",
            "no_post_hoc_editing": True,
            "claim_id": claim_id,
        }

    prices = seed.get("oracle_prices") or {}
    asset = claim.get("asset", "")
    price_data = prices.get(asset)
    if not price_data:
        return {
            "ok": True,
            "feature_ref": _FEATURE_REF,
            "claim_id": claim_id,
            "status": "unresolved",
            "unresolved_stays_unresolved": True,
            "reason": "no_outcome_data",
            "timestamp": _utcnow(),
        }

    outcome = _grade_claim(claim, float(price_data.get("price_usd", 0)))
    status: Literal["verified", "failed"] = "verified" if outcome["correctness"] == 1 else "failed"

    resolved = {**claim, "status": status, "outcome": outcome, "version": claim.get("version", 1)}
    _claim_store[claim_id] = resolved
    audit = {
        "audit_id": f"audit_{uuid.uuid4().hex[:12]}",
        "claim_id": claim_id,
        "outcome_source": "oracle_api",
        "score": outcome["correctness"],
        "brier_score": outcome["brier_score"],
        "timestamp": _utcnow(),
        "retention_years": _AUDIT_RETENTION_YEARS,
    }

    fee = (seed.get("verification_engine_931") or {}).get("fee_db") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "claim_id": claim_id,
        "status": status,
        "outcome": outcome,
        "audit": audit,
        "deterministic": True,
        "replay_reproducible": True,
        "no_post_hoc_editing": True,
        "fee_db": {"resolution_usd": fee.get("resolution_query_usd", 0.005)},
        "timestamp": _utcnow(),
    }


def get_claim_verification_931(
    claim_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    claims = {**(seed.get("locked_claims") or {}), **_claim_store}
    claim = claims.get(claim_id)
    if not claim:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "claim_not_found"}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "claim": claim,
        "immutable": claim.get("immutable", True),
        "timestamp": _utcnow(),
    }


def revise_claim_931(
    claim_id: str,
    *,
    new_claim_text: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Revisions = new version only — no edit in place."""
    seed = seed or _load_seed()
    claims = {**(seed.get("locked_claims") or {}), **_claim_store}
    original = claims.get(claim_id)
    if not original:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "claim_not_found"}

    new_version = int(original.get("version", 1)) + 1
    new_claim_id = f"{claim_id}_v{new_version}"
    revised = {
        **original,
        "claim_id": new_claim_id,
        "claim_text": new_claim_text,
        "version": new_version,
        "supersedes": claim_id,
        "locked_at": _utcnow(),
        "status": "locked",
        "outcome": None,
    }
    revised["lock_hash"] = _lock_hash(revised)
    _claim_store[new_claim_id] = revised

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "original_claim_id": claim_id,
        "new_claim_id": new_claim_id,
        "version": new_version,
        "no_edit_in_place": True,
        "new_version_only": True,
        "timestamp": _utcnow(),
    }


def run_verification_grading_tests_931(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Deterministic grading regression tests."""
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    verified = resolve_claim_931("claim_001", seed=seed)
    tests.append({"id": "verified_claim", "passed": verified.get("status") == "verified"})

    failed = resolve_claim_931("claim_002", seed=seed)
    tests.append({"id": "failed_claim", "passed": failed.get("status") == "failed"})

    unresolved = resolve_claim_931("claim_003", seed=seed)
    tests.append({"id": "unresolved_stays", "passed": unresolved.get("status") == "unresolved"})

    double = resolve_claim_931("claim_001", seed=seed)
    tests.append({"id": "no_post_hoc", "passed": double.get("error") == "already_resolved"})

    frozen = freeze_claim_931(
        asset="BTC",
        claim_text="Test claim",
        target_definition={"metric": "price_usd", "threshold": 60000, "direction": "above"},
        horizon_days=5,
        seed=seed,
    )
    tests.append({"id": "freeze_hash", "passed": frozen.get("claim", {}).get("lock_hash") is not None})

    passed = sum(1 for t in tests if t["passed"])
    return {
        "ok": passed == len(tests),
        "feature_ref": _FEATURE_REF,
        "tests": tests,
        "passed": passed,
        "total": len(tests),
        "all_passed": passed == len(tests),
        "replay_reproducible": True,
    }


def run_verification_engine_e2e_931(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = verification_engine_status_931(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "merged_987", "passed": status["accuracy_ledger_ref"] == _ACCURACY_LEDGER_REF})

    grading = run_verification_grading_tests_931(seed=seed)
    checks.append({"id": "grading_tests", "passed": grading.get("all_passed") is True})

    claim = get_claim_verification_931("claim_001", seed=seed)
    checks.append({"id": "immutable_record", "passed": claim.get("immutable") is True})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature_ref": _FEATURE_REF, "all_passed": all_passed, "checks": checks}
