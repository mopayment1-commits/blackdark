"""
BLACKDARK — Decision Certificate (Hero #6).

Exportable, shareable proof for a single Oracle decision:
prediction_id + chain_hash + sentence + timestamp.

Viral wedge for Proof Pass (free): public shareable card with removable
"Free Proof" watermark. Competitors sell data/scores; Trust OS sells a
reviewable decision + certificate.
"""

from __future__ import annotations

LEGAL_SHIELD_PREFIX = (
    "BLACKDARK Trust OS — decision evidence only. "
    "Not financial advice. Not a regulated investment service. "
    "Four-layer legal shield applies. "
)

import hashlib
import json
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def build_decision_certificate(payload: dict[str, Any]) -> dict[str, Any]:
    """Build a public-safe Decision Certificate from an Oracle response.

    Proof Pass (free) cards carry a removable "Free Proof" watermark.
    Decision Pro / Decision Desk strip it — that is a primary Free→Pro lever.
    """
    tier = str(payload.get("tier") or "free").strip().lower()
    is_free = tier in ("", "free")
    watermark = "Free Proof" if is_free else None

    body = {
        "asset": str(payload.get("symbol") or payload.get("asset") or "").upper(),
        "prediction_id": payload.get("prediction_id"),
        "chain_hash": payload.get("chain_hash") or (payload.get("proof") or {}).get("chain_hash"),
        "decision_action": payload.get("decision_action") or payload.get("verdict"),
        "decision_sentence": payload.get("decision_sentence") or payload.get("oracle"),
        "opportunity_score": payload.get("opportunity_score"),
        "truth_score": (payload.get("net_edge_truth") or {}).get("truth_score"),
        "half_life_seconds": (payload.get("opportunity_half_life") or {}).get(
            "expected_half_life_seconds"
        ),
        "market_regime": payload.get("market_regime"),
        "ux_mode": payload.get("ux_mode"),
        "tier": "free" if is_free else tier,
        "watermark": watermark,
        "upgrade_cta": (
            "Open Decision Pro — remove Free watermark, unlock daily habit depth."
            if is_free
            else None
        ),
        "issued_at": _utcnow(),
        "public_accuracy": "/oracle-accuracy",
        "engine": payload.get("unified_engine") or "unified_multimodal_v1",
    }
    # Hash excludes watermark/CTA so upgrade does not rewrite proof identity.
    hash_body = {
        k: v
        for k, v in body.items()
        if k not in {"watermark", "upgrade_cta", "tier"}
    }
    raw = json.dumps(hash_body, sort_keys=True, default=str).encode("utf-8")
    body["certificate_hash"] = hashlib.sha256(raw).hexdigest()
    verify_url = f"https://blackdark.app{body['public_accuracy']}#audit-challenge"
    body["verify_url"] = verify_url
    body["permalink"] = (
        f"https://blackdark.app/oracle-accuracy"
        f"?cert={body['certificate_hash'][:16]}"
        f"&pid={body['prediction_id'] or ''}"
    )
    wm_suffix = " · Free Proof" if is_free else ""
    body["share_text"] = (
        f"BLACKDARK Decision Certificate · {body['asset']} · "
        f"{body['decision_action']} · score {body['opportunity_score']} · "
        f"id={body['prediction_id']} · hash={str(body['certificate_hash'])[:16]}… · "
        f"verify {body['public_accuracy']}{wm_suffix}"
    )
    share_q = (
        f"BLACKDARK Decision Certificate · {body['asset']} · "
        f"{body['decision_action']} · verify {verify_url}{wm_suffix}"
    )
    from urllib.parse import quote

    body["share_urls"] = {
        "x": f"https://twitter.com/intent/tweet?text={quote(share_q)}",
        "telegram": (
            f"https://t.me/share/url?url={quote(verify_url)}&text={quote(share_q)}"
        ),
        "whatsapp": f"https://wa.me/?text={quote(share_q)}",
    }
    wm_line = f"Watermark: {watermark}\n" if watermark else ""
    body["export_text"] = (
        "BLACKDARK Decision Certificate\n"
        f"Asset: {body['asset']}\n"
        f"Action: {body['decision_action']}\n"
        f"Sentence: {body['decision_sentence']}\n"
        f"Opportunity score: {body['opportunity_score']}\n"
        f"Truth score: {body['truth_score']}\n"
        f"Half-life (s): {body['half_life_seconds']}\n"
        f"Regime: {body['market_regime']}\n"
        f"Tier: {body['tier']}\n"
        f"{wm_line}"
        f"Prediction id: {body['prediction_id']}\n"
        f"Chain hash: {body['chain_hash']}\n"
        f"Certificate hash: {body['certificate_hash']}\n"
        f"Issued at (UTC): {body['issued_at']}\n"
        f"Verify: {verify_url}\n"
        "Not financial advice. Four-layer legal shield applies. Labels are not proof — verify the Public Accuracy Ledger.\n"
    )
    body["compliance"] = compliance_footer_block(
        surface="decision_certificate",
        trust_basis="public_accuracy_ledger + audit_hash_chain",
    )
    return body


def compliance_footer_block(
    *,
    surface: str,
    trust_basis: str,
    data_sources: str = "live market + institutional context + labeled flywheel",
) -> dict[str, str]:
    """Anti-Hype Compliance Footer (Section Z #5) — shared under AI outputs."""
    return {
        "surface": surface,
        "data_source": data_sources,
        "trust_basis": trust_basis,
        "disclaimer": (
            "Not financial advice. AI cannot guarantee future returns. "
            "Verify claims on the Public Accuracy Ledger. No secret alpha promises."
        ),
        "regulator_note": "Built for auditability against AI-washing enforcement patterns (prove-it, not trust-me).",
    }
