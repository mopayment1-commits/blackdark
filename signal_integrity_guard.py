"""
Signal Integrity Guard — spoof/manipulation detection pre-filter (#1053).

Merged into Signal Engine (#11) + Data Engine. Rule-based only — no ML Sprint 2.
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.SignalIntegrity")

_FEATURE = "signal_integrity_guard"
_SEED_PATH = Path("data/signal_integrity_seed.json")
_AUDIT_PATH = Path("data/signal_integrity_audit.jsonl")

_OUTLIER_REF = 1026
_FRAUD_REF = 960
_INCIDENT_REF = 1017
_ACCURACY_REF = 987

_source_flags: dict[str, deque] = defaultdict(lambda: deque(maxlen=200))


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("signal_integrity_guard") or {}


def _record_audit(entry: dict[str, Any]) -> None:
    entry.setdefault("ts", time.time())
    entry.setdefault("iso", _utcnow())
    entry.setdefault("feature", _FEATURE)
    _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("signal integrity audit failed", exc_info=True)


def _pattern_wash_trading(features: dict[str, Any]) -> dict[str, Any] | None:
    buyer = str(features.get("buyer_address") or features.get("buyer") or "")
    seller = str(features.get("seller_address") or features.get("seller") or "")
    if buyer and seller and buyer.lower() == seller.lower():
        return {"pattern": "wash_trading", "evidence": {"buyer": buyer, "seller": seller}}
    return None


def _pattern_volume_spike_no_price(features: dict[str, Any]) -> dict[str, Any] | None:
    vol_chg = float(features.get("volume_change_pct") or 0)
    price_chg = abs(float(features.get("price_change_pct") or 0))
    if vol_chg > 200 and price_chg < 1.0:
        return {
            "pattern": "volume_spike_no_price",
            "evidence": {"volume_change_pct": vol_chg, "price_change_pct": price_chg},
        }
    return None


def _pattern_social_burst(features: dict[str, Any]) -> dict[str, Any] | None:
    mentions = int(features.get("mention_count") or 0)
    new_accounts = int(features.get("new_account_mentions") or 0)
    if mentions >= 50 and new_accounts / max(mentions, 1) > 0.7:
        return {
            "pattern": "social_mention_burst",
            "evidence": {"mentions": mentions, "new_account_ratio": round(new_accounts / mentions, 2)},
        }
    return None


def _pattern_order_book_spoofing(features: dict[str, Any]) -> dict[str, Any] | None:
    if features.get("order_cancelled_after_signal") is True or features.get("spoof_cancel") is True:
        return {"pattern": "order_book_spoofing", "evidence": {"cancel_after_signal": True}}
    return None


def _pattern_timestamp_manipulation(features: dict[str, Any], *, asof: str | None) -> dict[str, Any] | None:
    ts = features.get("event_timestamp") or asof
    if not ts:
        return None
    try:
        event = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        now = datetime.now(UTC)
        if event > now:
            return {"pattern": "timestamp_manipulation", "evidence": {"reason": "future_timestamp", "ts": str(ts)}}
        if (now - event).total_seconds() > 86400 * 30 and features.get("claimed_live") is True:
            return {"pattern": "timestamp_manipulation", "evidence": {"reason": "stale_claimed_live", "ts": str(ts)}}
    except ValueError:
        return {"pattern": "timestamp_manipulation", "evidence": {"reason": "invalid_timestamp", "ts": str(ts)}}
    return None


def _single_source_flag(provenance: dict[str, Any] | None) -> dict[str, Any] | None:
    sources = (provenance or {}).get("sources") or (provenance or {}).get("source_ids") or []
    if isinstance(sources, str):
        sources = [sources]
    if len(sources) <= 1:
        return {"pattern": "single_source_spoof_risk", "evidence": {"sources": sources}}
    return None


def detect_spoof_patterns(
    *,
    features: dict[str, Any] | None,
    provenance: dict[str, Any] | None = None,
    asof: str | None = None,
) -> list[dict[str, Any]]:
    """Run 5 mandatory rule-based spoof patterns."""
    features = features or {}
    flags: list[dict[str, Any]] = []
    for detector in (
        lambda: _pattern_wash_trading(features),
        lambda: _pattern_volume_spike_no_price(features),
        lambda: _pattern_social_burst(features),
        lambda: _pattern_order_book_spoofing(features),
        lambda: _pattern_timestamp_manipulation(features, asof=asof),
    ):
        hit = detector()
        if hit:
            flags.append(hit)
    single = _single_source_flag(provenance)
    if single and _cfg().get("single_source_spoof_risk_flag", True):
        flags.append(single)
    return flags


def validate_signal_integrity(
    *,
    signal_type: str,
    asset: str,
    features: dict[str, Any] | None = None,
    provenance: dict[str, Any] | None = None,
    asof: str | None = None,
    source_id: str = "",
) -> dict[str, Any]:
    """
    Pre-filter before Signal Engine scoring.
    Returns accept/reject with manipulation flags and evidence.
    """
    flags = detect_spoof_patterns(features=features, provenance=provenance, asof=asof)
    manipulation = len(flags) > 0
    reject = manipulation and len(flags) >= 1 and _cfg().get("rejection_requires_manipulation_flag", True)

    result = {
        "ok": not reject,
        "accepted": not reject,
        "rejected": reject,
        "manipulation_flag": manipulation,
        "flags": flags,
        "signal_type": signal_type,
        "asset": asset,
        "disclaimer": _cfg().get("disclaimer", "Suspected spoofing — not confirmed crime."),
        "accuracy_ledger_ref": _ACCURACY_REF,
    }

    _record_audit(
        {
            "event": "signal_integrity_check",
            "signal_type": signal_type,
            "asset": asset,
            "accepted": not reject,
            "flags": flags,
            "source_id": source_id,
        }
    )

    if source_id:
        _source_flags[source_id].append(time.time())
        _maybe_coordinated_attack(source_id)

    if reject:
        _record_audit({"event": "signal_rejected", "signal_type": signal_type, "asset": asset, "flags": flags})

    return result


def _maybe_coordinated_attack(source_id: str) -> None:
    now = time.time()
    recent = [t for t in _source_flags[source_id] if now - t <= 3600]
    threshold = int(_cfg().get("coordinated_attack_threshold_per_hour", 10))
    if len(recent) < threshold:
        return
    try:
        from security_events import record_security_event

        record_security_event(
            "coordinated_spoofing_attack",
            severity="high",
            actor="signal_integrity_guard",
            detail={
                "source_id": source_id,
                "flagged_signals_hour": len(recent),
                "action": "source_blacklist_review",
                "integration_ref": _INCIDENT_REF,
            },
        )
    except ImportError:
        pass


def signal_integrity_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "patterns": policy.get("patterns") or [],
        "rule_based_only": policy.get("rule_based_only", True),
        "integrations": policy.get("integrations") or {},
        "audit_path": str(_AUDIT_PATH),
        "timestamp": _utcnow(),
    }


def run_signal_integrity_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = signal_integrity_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "five_patterns", "passed": len(status["patterns"]) >= 5})

    wash = validate_signal_integrity(
        signal_type="test",
        asset="BTC",
        features={"buyer_address": "0xabc", "seller_address": "0xabc"},
    )
    checks.append({"id": "wash_rejected", "passed": wash["rejected"] is True})

    clean = validate_signal_integrity(
        signal_type="oracle_direction",
        asset="ETH",
        features={"price_change_pct": 2.0, "volume_change_pct": 10},
        provenance={"sources": ["binance", "coingecko"]},
    )
    checks.append({"id": "clean_accepted", "passed": clean["accepted"] is True})

    single = validate_signal_integrity(
        signal_type="test",
        asset="SOL",
        features={},
        provenance={"sources": ["only_one"]},
    )
    checks.append({"id": "single_source_flag", "passed": single["manipulation_flag"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature": _FEATURE, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
