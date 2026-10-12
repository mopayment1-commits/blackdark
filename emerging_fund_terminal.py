"""
BLACKDARK — Emerging Fund Terminal (Section Z #4).

Onboarding posture for crypto funds under ~$50M: DD-ready packaging of
Public Accuracy Ledger + Decision Certificate + Evidence Pack summary.
Pricing posture for 10–50M AUM — not Bloomberg-tier.
"""

from __future__ import annotations

import asyncio
import copy
import os
import time
from typing import Any

_FUND_PACK_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_FUND_PACK_CACHE_TTL_SEC = float(os.getenv("FUND_TERMINAL_CACHE_SEC", "60"))


async def build_fund_terminal_pack(*, fund_name: str = "Emerging Fund") -> dict[str, Any]:
    """Assemble export-oriented DD pack for small/emerging funds."""
    key = (fund_name or "Emerging Fund").strip() or "Emerging Fund"
    now = time.monotonic()
    cached = _FUND_PACK_CACHE.get(key)
    if cached and (now - cached[0]) < _FUND_PACK_CACHE_TTL_SEC:
        return copy.deepcopy(cached[1])

    from decision_certificate import build_decision_certificate, compliance_footer_block

    accuracy = {}
    locked = {}
    registry = {}
    net_edge = {}
    veto = {}
    d5 = {}
    async def _accuracy_block() -> dict[str, Any]:
        try:
            from ml.public_accuracy import build_public_accuracy_payload

            return await build_public_accuracy_payload(recent_limit=8)
        except Exception as exc:
            return {"error": str(exc)}

    def _locked_block() -> dict[str, Any]:
        try:
            from locked_predictions import glass_box_status

            return glass_box_status()
        except Exception:
            return {}

    def _registry_block() -> dict[str, Any]:
        try:
            from signal_registry import registry_stats

            return registry_stats()
        except Exception as exc:
            return {"error": str(exc)}

    def _net_edge_block() -> dict[str, Any]:
        try:
            from net_edge_truth import net_edge_truth_status

            return net_edge_truth_status()
        except Exception as exc:
            return {"error": str(exc)}

    def _veto_block() -> dict[str, Any]:
        try:
            from dimension_conflict_guard import dimension_conflict_status

            return dimension_conflict_status()
        except Exception as exc:
            return {"error": str(exc)}

    def _d5_block() -> dict[str, Any]:
        try:
            from ml.regime_models import regime_model_registry

            return regime_model_registry()
        except Exception as exc:
            return {"error": str(exc)}

    accuracy, locked, registry, net_edge, veto, d5 = await asyncio.gather(
        _accuracy_block(),
        asyncio.to_thread(_locked_block),
        asyncio.to_thread(_registry_block),
        asyncio.to_thread(_net_edge_block),
        asyncio.to_thread(_veto_block),
        asyncio.to_thread(_d5_block),
    )

    oracle = accuracy.get("oracle") or {}
    proof = accuracy.get("proof_chain") or {}

    sample_cert = build_decision_certificate(
        {
            "symbol": "BTC",
            "prediction_id": "fund_dd_sample",
            "decision_action": "WAIT",
            "decision_sentence": "Sample Decision Certificate for allocator DD packaging.",
            "opportunity_score": oracle.get("average_accuracy_percent"),
            "market_regime": (d5.get("regimes") or {}).get("neutral", {}).get("status"),
            "unified_engine": "unified_multimodal_v1",
            "chain_hash": proof.get("tip_hash"),
        }
    )

    evidence_public = {
        "product_thesis": (
            "Decision Intelligence + Proven Predictive Accuracy + "
            "Proprietary Labeled Market Corpus"
        ),
        "differentiators": {
            "D1": "live",
            "D2": "live",
            "D3": "live",
            "D4": "live",
            "D5": d5.get("status") or d5.get("evidence_status") or "weights_live",
            "D6": "live",
            "D7": "live",
            "D8": {
                "status": registry.get("status")
                or ("live" if (registry.get("labeled") or 0) > 0 else "pending_labels"),
                "labeled": registry.get("labeled"),
                "unlabeled": registry.get("unlabeled"),
                "linked_prediction_ids": registry.get("linked_prediction_ids"),
                "by_type_performance": registry.get("by_type_performance"),
            },
        },
        "full_pack": "/api/due-diligence/evidence-pack",
        "access": "whale_or_admin",
    }

    payload: dict[str, Any] = {
        "fund_name": fund_name,
        "segment": "emerging_crypto_fund_sub_50m",
        "pricing_posture": {
            "target_aum_usd": "10M–50M",
            "note": "Priced for the underserved 78% of crypto funds — not billion-dollar desks.",
            "tiers": ["pro", "whale"],
            "checkout_pro": "/create-checkout-session?tier=pro",
            "checkout_whale": "/create-checkout-session?tier=whale",
        },
        "dd_export": {
            "public_accuracy_percent": oracle.get("average_accuracy_percent"),
            "total_predictions": oracle.get("total_predictions"),
            "proof_chain_valid": (proof.get("verify") or {}).get("valid"),
            "tip_hash": proof.get("tip_hash"),
            "accuracy_page": "/oracle-accuracy",
            "sample_decision_certificate": sample_cert,
            "signal_registry": {
                "labeled": registry.get("labeled"),
                "unlabeled": registry.get("unlabeled"),
                "total": registry.get("total_in_memory"),
            },
            "net_edge_truth": net_edge,
            "contradiction_veto": veto,
            "regime_models_d5": {
                "status": d5.get("status"),
                "artifacts_ready": d5.get("artifacts_ready"),
                "artifacts_expected": d5.get("artifacts_expected"),
            },
            "evidence_public": evidence_public,
            "locked_predictions": locked,
        },
        "allocator_checklist": [
            "Verify public accuracy ledger sample size and hit-rate",
            "Inspect audit chain tip hash integrity",
            "Review Net-Edge reject posture (quality over quantity)",
            "Confirm Contradiction Veto is fail-closed",
            "Inspect Signal Registry labeled vs pending counts",
            "Confirm D5 regime artifact honesty flags",
            "Request full Evidence Pack (Whale/Admin)",
        ],
        "onboarding_steps": [
            "Open /b2b#fund-terminal",
            "Review Public Accuracy Ledger",
            "Export Decision Certificates from live Oracle calls",
            "Download DD JSON from this terminal",
            "Upgrade Whale for full Evidence Pack download",
        ],
        "compliance": compliance_footer_block(
            surface="emerging_fund_terminal",
            trust_basis="public_accuracy_ledger + evidence_pack",
        ),
        "hero_deepening": ["public_accuracy_ledger", "b2b_evidence"],
    }
    _FUND_PACK_CACHE[key] = (time.monotonic(), payload)
    return copy.deepcopy(payload)
