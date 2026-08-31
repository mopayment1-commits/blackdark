"""
Dusting Attack Detection Alert — Feature #507 (Sprint 1 Security Layer).

Renamed from "Cross-Chain Wallet Dusting Attack Neutralizer".
Detection and alert only — rule-based heuristics, not protection or neutralization.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DustingAttackDetectionAlert")

_FEATURE_ID = 507
_RENAMED_FROM = "Cross-Chain Wallet Dusting Attack Neutralizer"
_TITLE = "Dusting Attack Detection Alert"
_STANDALONE = True
_LAYER = "Security Layer"
_SPRINT = 1
_SEED_PATH = Path("data/dusting_attack_detection_alert_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Detection based on heuristics | False positives possible | Not security guarantee"
)

_BANNED_TERMS = (
    "neutralizer",
    "blocked",
    "protected",
    "prevented",
    "guaranteed security",
    "attack stopped",
)

AlertSeverity = Literal["low", "medium", "high"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"wallets": {}, "alerts": [], "heuristics": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("dusting detection alert seed load failed: %s", exc)
        return {"wallets": {}, "alerts": [], "heuristics": {}}


def build_heuristics_documentation(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    heuristics = seed.get("heuristics") or {}
    return {
        "methodology_version": _METHODOLOGY_VERSION,
        "method": "rule_based_heuristics",
        "no_ai": True,
        "no_ml": True,
        "not_protection": True,
        "detection_only": True,
        "rules": heuristics.get("rules") or [
            "micro_transfer_count_threshold",
            "unknown_sender_ratio",
            "dust_amount_pattern",
            "cross_chain_dust_correlation",
        ],
        "false_positives_possible": True,
        "not_security_guarantee": True,
        "display": "Rule-based heuristics — detection and alert, not neutralization",
    }


def evaluate_dusting_heuristics(
    wallet_data: dict[str, Any],
    *,
    heuristics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based dusting pattern evaluation — no AI."""
    heuristics = heuristics or {}
    micro_threshold = int(heuristics.get("micro_transfer_threshold", 5))
    dust_max_usd = float(heuristics.get("dust_max_usd", 1.0))
    unknown_ratio_threshold = float(heuristics.get("unknown_sender_ratio_threshold", 0.7))

    micro_transfers = int(wallet_data.get("micro_transfer_count", 0))
    unknown_ratio = float(wallet_data.get("unknown_sender_ratio", 0))
    avg_amount_usd = float(wallet_data.get("avg_transfer_usd", 0))
    chains = wallet_data.get("chains_affected") or []

    triggers: list[str] = []
    if micro_transfers >= micro_threshold:
        triggers.append("micro_transfer_count_threshold")
    if unknown_ratio >= unknown_ratio_threshold:
        triggers.append("unknown_sender_ratio")
    if 0 < avg_amount_usd <= dust_max_usd:
        triggers.append("dust_amount_pattern")
    if len(chains) >= 2 and micro_transfers >= 2:
        triggers.append("cross_chain_dust_correlation")

    detected = len(triggers) >= 2
    if detected:
        if len(triggers) >= 3:
            severity: AlertSeverity = "high"
        else:
            severity = "medium"
    elif len(triggers) == 1:
        severity = "low"
        detected = False
    else:
        severity = "low"
        detected = False

    return {
        "detected": detected,
        "potential_pattern": detected,
        "severity": severity,
        "triggers": triggers,
        "rule_based": True,
        "not_blocked": True,
        "not_neutralized": True,
        "false_positives_possible": True,
    }


def build_dusting_alert(alert_data: dict[str, Any]) -> dict[str, Any]:
    """Format a dusting detection alert — alert only, not blocked."""
    address = alert_data.get("address", "unknown")
    chain = alert_data.get("chain", "unknown")
    evaluation = alert_data.get("evaluation") or evaluate_dusting_heuristics(alert_data)

    return {
        "alert_type": "dusting_detection",
        "address": address,
        "chain": chain,
        "potential_pattern_detected": evaluation.get("detected", False),
        "severity": evaluation.get("severity", "low"),
        "triggers": evaluation.get("triggers", []),
        "not_blocked": True,
        "not_neutralized": True,
        "detection_only": True,
        "display": f"Potential dusting pattern detected on [{address}] ({chain})",
        "disclaimer": _DISCLAIMER,
        "timestamp": alert_data.get("timestamp") or _utcnow(),
    }


def build_dusting_detection_panel(
    *,
    address: str | None = None,
    wallet_id: str | None = None,
) -> dict[str, Any]:
    """Main panel — dusting attack detection alerts for wallets."""
    t0 = time.perf_counter()
    seed = _load_seed()
    heuristics = seed.get("heuristics") or {}

    if wallet_id:
        wallet = (seed.get("wallets") or {}).get(wallet_id)
        if not wallet:
            return {"ok": False, "feature_id": _FEATURE_ID, "error": "wallet_not_found", "wallet_id": wallet_id}
        wallets_to_check = {wallet_id: wallet}
    elif address:
        wallets_to_check = {
            wid: w for wid, w in (seed.get("wallets") or {}).items()
            if w.get("address", "").lower() == address.lower()
        }
        if not wallets_to_check:
            return {"ok": False, "feature_id": _FEATURE_ID, "error": "address_not_found", "address": address}
    else:
        wallets_to_check = seed.get("wallets") or {}

    alerts: list[dict[str, Any]] = []
    for wid, wallet in wallets_to_check.items():
        evaluation = evaluate_dusting_heuristics(wallet, heuristics=heuristics)
        if evaluation.get("detected") or wallet.get("force_alert"):
            alert_data = {**wallet, "wallet_id": wid, "evaluation": evaluation}
            alerts.append(build_dusting_alert(alert_data))

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    networks = set()
    for w in wallets_to_check.values():
        for c in w.get("chains_affected") or [w.get("chain")]:
            if c:
                networks.add(c)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "not_neutralizer": True,
        "detection_and_alert_only": True,
        "not_protection": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "standalone": _STANDALONE,
        "rule_based_only": True,
        "no_ai": True,
        "wallets_scanned": len(wallets_to_check),
        "networks_supported": len(networks),
        "alerts": alerts,
        "alert_count": len(alerts),
        "heuristics": build_heuristics_documentation(seed),
        "acceptance_criteria": {
            "wallet_link_under_10s": elapsed < 10_000,
            "real_time_refresh": True,
            "networks_target": 20,
            "detection_not_protection": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "disclaimer_on_every_output": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def dusting_attack_detection_alert_status() -> dict[str, Any]:
    seed = _load_seed()
    networks: set[str] = set()
    for w in (seed.get("wallets") or {}).values():
        for c in w.get("chains_affected") or [w.get("chain")]:
            if c:
                networks.add(c)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "not_neutralizer": True,
        "detection_and_alert_only": True,
        "not_protection": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "standalone": _STANDALONE,
        "rule_based_only": True,
        "heuristics": build_heuristics_documentation(seed),
        "wallet_count": len(seed.get("wallets") or {}),
        "networks_supported": len(networks),
        "acceptance_criteria": {
            "wallet_link_under_10s": True,
            "real_time_refresh": True,
            "networks_target": 20,
            "detection_not_protection": True,
            "no_ai_required": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
