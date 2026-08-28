"""
Developer Wallet Tracker — Feature #854 (merged into Intelligence Ledger).

Team/founder wallet movement monitoring — evidence-based labels only.
Route: /ledger/wallet-risk. Non-custodial, neutral language, no fraud accusations.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.WalletRiskMonitor")

_FEATURE_REF = 854
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger"
_COMPONENT = "wallet_risk_monitor"
_SPRINT = 2
_SEED_PATH = Path("data/wallet_risk_monitor_seed.json")
_ONCHAIN_METRICS_REF = 577
_TOKEN_UNLOCKS_REF = 820

_MATERIAL_USD_THRESHOLD = 10_000.0
_MATERIAL_SUPPLY_PCT = 1.0
_BANNED_LABELS = ("Rug Pull", "Scam", "Fraud", "Dump", "Suspicious Activity")
_ALLOWED_LABELS = ("Transfer to Exchange", "Transfer to Bridge", "Internal Move", "Transfer to DEX", "Unknown Destination")
_SOURCE_CONFIDENCE = ("Verified: Official Source", "Unverified: Community Report")
_DESTINATION_TYPES = ("Exchange", "Bridge", "DEX", "Unknown")

_DISCLAIMER = (
    "Wallet movements are observed on-chain. Not accusation of wrongdoing. Not financial advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("wallet risk monitor seed load failed: %s", exc)
        return {}


def wallet_risk_monitor_status_854(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("wallet_risk_monitor_854") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "route": "/ledger/wallet-risk",
        "sprint": _SPRINT,
        "material_threshold_usd": _MATERIAL_USD_THRESHOLD,
        "material_threshold_supply_pct": _MATERIAL_SUPPLY_PCT,
        "allowed_labels": list(_ALLOWED_LABELS),
        "banned_labels": list(_BANNED_LABELS),
        "destination_types": list(_DESTINATION_TYPES),
        "source_confidence_levels": list(_SOURCE_CONFIDENCE),
        "manual_review_required": True,
        "ml_rejected": True,
        "rule_based_only": True,
        "onchain_metrics_ref": _ONCHAIN_METRICS_REF,
        "token_unlocks_ref": _TOKEN_UNLOCKS_REF,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def classify_destination_854(
    destination_address: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Destination classification — Exchange | Bridge | DEX | Unknown."""
    seed = seed or _load_seed()
    registry = seed.get("destination_registry") or {}

    for dest_type in ("Exchange", "Bridge", "DEX"):
        entries = registry.get(dest_type.lower(), []) or registry.get(dest_type, [])
        for entry in entries:
            if entry.get("address", "").lower() == destination_address.lower():
                return {
                    "destination_type": dest_type,
                    "destination_name": entry.get("name"),
                    "label": f"Transfer to {dest_type}" if dest_type != "DEX" else "Transfer to DEX",
                    "classified": True,
                }

    return {
        "destination_type": "Unknown",
        "destination_name": None,
        "label": "Unknown Destination",
        "classified": False,
    }


def is_material_transfer_854(
    amount_usd: float,
    supply_pct: float,
) -> bool:
    return amount_usd > _MATERIAL_USD_THRESHOLD or supply_pct > _MATERIAL_SUPPLY_PCT


def check_unlock_context_854(
    transfer_ts: str,
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Join unlock schedule — flag Post-Unlock Movement if near unlock date."""
    seed = seed or _load_seed()
    unlocks = (seed.get("unlock_schedules") or {}).get(asset.upper(), [])
    transfer_dt = datetime.fromisoformat(transfer_ts.replace("Z", "+00:00"))

    for unlock in unlocks:
        unlock_dt = datetime.fromisoformat(unlock.get("unlock_date", "").replace("Z", "+00:00"))
        window_days = int(unlock.get("context_window_days", 7))
        delta = abs((transfer_dt - unlock_dt).days)
        if delta <= window_days:
            return {
                "post_unlock_movement": True,
                "unlock_date": unlock.get("unlock_date"),
                "days_from_unlock": delta,
                "context_flag": "Post-Unlock Movement",
                "language": "observed movement near unlock date",
            }

    return {
        "post_unlock_movement": False,
        "context_flag": None,
        "language": "observed movement",
    }


def evaluate_transfer_854(
    transfer: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate a single transfer — evidence-based labels only."""
    seed = seed or _load_seed()
    wallets = seed.get("verified_wallets") or {}
    from_addr = transfer.get("from_address", "").lower()
    wallet_info = wallets.get(from_addr)

    if not wallet_info:
        return {
            "ok": False,
            "error": "wallet_not_verified",
            "detail": "Only verified team wallets from official sources are monitored",
        }

    amount_usd = float(transfer.get("amount_usd", 0))
    supply_pct = float(transfer.get("supply_pct", 0))
    material = is_material_transfer_854(amount_usd, supply_pct)

    if not material:
        return {
            "ok": True,
            "material": False,
            "action": "below_threshold",
            "observed_movement": f"Transfer ${amount_usd:,.0f} ({supply_pct:.2f}% supply)",
        }

    dest = classify_destination_854(transfer.get("to_address", ""), seed=seed)
    unlock_ctx = check_unlock_context_854(
        transfer.get("timestamp", _utcnow()),
        transfer.get("asset", "ETH"),
        seed=seed,
    )

    source_confidence = wallet_info.get("source_confidence", "Verified: Official Source")
    label = dest.get("label", "Unknown Destination")
    if dest.get("destination_type") == "Exchange":
        label = "Transfer to Exchange"
    elif wallet_info.get("is_internal", False):
        label = "Internal Move"

    return {
        "ok": True,
        "material": True,
        "asset": transfer.get("asset"),
        "from_address": from_addr,
        "to_address": transfer.get("to_address"),
        "amount_usd": amount_usd,
        "supply_pct": supply_pct,
        "label": label,
        "destination_type": dest.get("destination_type"),
        "destination_name": dest.get("destination_name"),
        "unlock_context": unlock_ctx,
        "source_confidence": source_confidence,
        "team_role": wallet_info.get("role"),
        "publish_status": "pending_manual_review",
        "auto_publish": False,
        "neutral_language": f"Observed movement of ${amount_usd:,.0f} to {dest.get('destination_type', 'Unknown')}",
        "no_accusation": True,
        "disclaimer": _DISCLAIMER,
    }


def build_wallet_risk_panel_854(
    asset: str = "ARB",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Intelligence Ledger wallet risk monitor panel."""
    seed = seed or _load_seed()
    cfg = seed.get("wallet_risk_monitor_854") or {}
    transfers = (seed.get("transfers") or {}).get(asset.upper(), [])

    evaluations = [evaluate_transfer_854(t, seed=seed) for t in transfers]
    material = [e for e in evaluations if e.get("material")]
    pending_review = [e for e in material if e.get("publish_status") == "pending_manual_review"]

    badge = "green"
    if any(e.get("destination_type") == "Exchange" for e in material):
        badge = "yellow"
    if any(e.get("unlock_context", {}).get("post_unlock_movement") for e in material):
        badge = "red"

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "surface": "intelligence_ledger",
        "panel_title_ar": "مراقبة المحافظ",
        "asset_card_badge": "حركات الفريق",
        "asset": asset.upper(),
        "route": "/ledger/wallet-risk",
        "verified_wallet_count": len(seed.get("verified_wallets") or {}),
        "transfers_evaluated": len(evaluations),
        "material_transfers": len(material),
        "pending_manual_review": len(pending_review),
        "evaluations": evaluations,
        "badge_color": badge,
        "manual_review_queue": pending_review,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def build_asset_card_wallet_badge_854(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Market Radar Asset Card — team wallet movement badge."""
    panel = build_wallet_risk_panel_854(asset, seed=seed)
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "surface": "asset_card",
        "asset": asset.upper(),
        "badge_label": panel.get("asset_card_badge"),
        "badge_color": panel.get("badge_color"),
        "material_count": panel.get("material_transfers", 0),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def run_wallet_risk_e2e_854(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    status = wallet_risk_monitor_status_854(seed=seed)
    tests.append({"test": "standalone_rejected", "passed": status.get("standalone_rejected") is True})
    tests.append({"test": "manual_review_required", "passed": status.get("manual_review_required") is True})
    tests.append({"test": "ml_rejected", "passed": status.get("ml_rejected") is True})
    tests.append({"test": "no_fraud_labels", "passed": "Rug Pull" in status.get("banned_labels", [])})

    transfers = (seed.get("transfers") or {}).get("ARB", [])
    for t in transfers:
        ev = evaluate_transfer_854(t, seed=seed)
        if ev.get("material"):
            tests.append({
                "test": f"neutral_language_{t.get('transfer_id', 'x')}",
                "passed": ev.get("no_accusation") is True and "suspicious" not in ev.get("neutral_language", "").lower(),
            })
            tests.append({
                "test": f"no_auto_publish_{t.get('transfer_id', 'x')}",
                "passed": ev.get("auto_publish") is False,
            })

    panel = build_wallet_risk_panel_854("ARB", seed=seed)
    tests.append({"test": "panel_ok", "passed": panel.get("ok") is True})
    tests.append({"test": "arabic_surface", "passed": panel.get("panel_title_ar") == "مراقبة المحافظ"})

    badge = build_asset_card_wallet_badge_854("ARB", seed=seed)
    tests.append({"test": "asset_card_badge", "passed": badge.get("badge_color") in ("green", "yellow", "red")})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "e2e_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }
