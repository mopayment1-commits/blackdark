"""Commercial Oracle adapter — no dashboard import (avoids circular deps / agent conflicts)."""

from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException

from api.v1.contract import DISCLAIMER


def licensed_universe() -> set[str] | None:
    raw = os.getenv("DECISION_API_UNIVERSE", "").strip()
    if not raw:
        return None
    return {part.strip().upper() for part in raw.split(",") if part.strip()}


def assert_symbol_licensed(asset: str) -> None:
    universe = licensed_universe()
    if universe is None:
        return
    if asset.upper() not in universe:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "universe_not_licensed",
                "message": f"{asset.upper()} is not in this key's licensed universe.",
                "licensed_universe": sorted(universe),
            },
        )


def _verdict_sentence(asset: str, verdict: str | None, score: float) -> str:
    label = (verdict or "HOLD").upper()
    return f"{asset} Decision API: {label} (opportunity score {score:.0f}/100). Verify on /oracle-accuracy."


async def build_v1_oracle_decision(symbol: str, *, principal: dict[str, Any]) -> dict[str, Any]:
    from market_context import fetch_binance_ticker, normalize_oracle_symbol
    from oracle_unified import compute_unified_oracle
    from security_sanitize import sanitize_oracle_payload

    asset, pair = normalize_oracle_symbol(symbol)
    assert_symbol_licensed(asset)
    market = await fetch_binance_ticker(pair)
    if market is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "symbol_not_found", "message": f"No live market data for {asset}."},
        )
    price = float(market["price"])
    quote_volume = float(market.get("quote_volume") or (float(market.get("volume") or 0) * price))
    change = float(market.get("change_24h") or 0)
    unified = await compute_unified_oracle(asset, price, quote_volume, change)
    score = float(unified.get("opportunity_score") or 0)
    verdict = unified.get("verdict")
    payload: dict[str, Any] = {
        "api_version": "v1",
        "asset": asset,
        "pair": pair,
        "price": price,
        "change_24h": change,
        "opportunity_score": score,
        "verdict": verdict,
        "confidence": unified.get("confidence"),
        "engine": unified.get("engine") or "unified_multimodal_v1",
        "market_regime": unified.get("market_regime") or unified.get("regime"),
        "decision_sentence": _verdict_sentence(asset, str(verdict) if verdict else None, score),
        "licensed_use": "internal_decision_support",
        "disclaimer": DISCLAIMER,
        "org_id": principal.get("org_id"),
        "environment": principal.get("environment"),
    }
    try:
        from data_trust_engine import attach_data_trust

        payload = attach_data_trust(payload)
    except Exception:
        payload.setdefault("canonical_market_state", {"action": "not_applied"})
    try:
        from decision_certificate import build_decision_certificate, compliance_footer_block

        payload["tier"] = "whale"
        payload["decision_certificate"] = build_decision_certificate(payload)
        payload["compliance_footer"] = compliance_footer_block(
            surface="decision_api_v1",
            trust_basis="public_accuracy_ledger + decision_certificate + canonical_market_state",
        )
    except Exception:
        payload["decision_certificate"] = None
    clean = sanitize_oracle_payload(payload)
    clean["disclaimer"] = DISCLAIMER
    clean["licensed_use"] = "internal_decision_support"
    return clean


async def build_v1_accuracy(*, recent_limit: int = 20) -> dict[str, Any]:
    from ml.public_accuracy import build_public_accuracy_payload
    from oracle_audit_chain import chain_summary, verify_chain

    payload = await build_public_accuracy_payload(recent_limit=recent_limit)
    payload["api_version"] = "v1"
    payload["audit_chain"] = chain_summary(limit=min(20, recent_limit))
    payload["audit_chain_verify"] = verify_chain()
    payload["disclaimer"] = DISCLAIMER
    payload["licensed_use"] = "internal_decision_support"
    return payload


async def build_v1_feed(*, principal: dict[str, Any], limit: int | None = None) -> dict[str, Any]:
    import hashlib
    import hmac
    import json

    from api.v1.contract import DISCLAIMER, PLAN_LIMITS
    from database import fetch_institutional_feed_rows
    from secrets_vault import decrypt_secret

    plan = str(principal.get("plan") or "institutional")
    env = str(principal.get("environment") or "live")
    defaults = PLAN_LIMITS["sandbox"] if env == "test" or plan == "sandbox" else PLAN_LIMITS["institutional"]
    export_limit = int(defaults["export_limit"])
    take = min(int(limit or export_limit), export_limit)
    rows = await fetch_institutional_feed_rows(limit=take)
    body: dict[str, Any] = {
        "api_version": "v1",
        "product": "BLACKDARK Decision API Institutional Feed",
        "org_id": principal.get("org_id"),
        "environment": env,
        "key_id": principal.get("public_id"),
        "record_count": len(rows),
        "licensed_use": "internal_decision_support",
        "disclaimer": DISCLAIMER,
        "methodology": {
            "cvvd": "Cross-Venue Volume Discrepancy",
            "sii": "Sector Inflow Index",
        },
        "records": rows,
    }
    from data_trust_engine import stamp_license

    body = stamp_license(body)
    canonical = json.dumps({k: v for k, v in body.items() if k != "signature"}, sort_keys=True, separators=(",", ":"), default=str)
    try:
        signing = decrypt_secret(str(principal.get("signing_secret_encrypted") or ""))
    except Exception:
        signing = ""
    if signing:
        body["signature"] = hmac.new(signing.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        body["signature_alg"] = "HMAC-SHA256"
    else:
        body["signature"] = None
        body["signature_alg"] = None
    return body
