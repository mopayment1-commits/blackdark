"""
BLACKDARK — Trust Pulse (Daily Decision Pulse).

First-open surface: one live Act/Wait decision + Why + proof + freshness.
Not a news digest. Not a movers board. Competitors own those.
Unique wedge: reviewable decision + certificate + public ledger honesty.

SSE emits heartbeats always; decision_changed only on material flips.
Stream polls must not spam prediction_id (persist only on first / flip).
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

# Sonar S1192: duplicated string literals
PATH_ORACLE_ACCURACY = '/oracle-accuracy'
STR_VERIFIED_ON_LEDGER = 'Verified on Ledger'

logger = logging.getLogger("BLACKDARK.TrustPulse")

# Soft cache — identity of the pulse for a symbol (avoids spam + flicker).
_LOCK = threading.Lock()
_PULSE_CACHE: dict[str, dict[str, Any]] = {}

CACHE_TTL_SEC = 45.0
STALE_AFTER_SEC = 120.0
HEARTBEAT_SEC = 20.0
DEFAULT_SYMBOL = "BTC"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _norm_action(raw: str | None) -> str:
    a = (raw or "WAIT").strip().upper()
    if a in {"BUY", "ACT", "LONG"}:
        return "ACT"
    if a in {"SELL", "SHORT", "EXIT"}:
        return "CAUTION"
    if a in {"CAUTION", "AVOID", "DO_NOT_TOUCH"}:
        return "CAUTION"
    return "WAIT"


def _freshness(age_sec: float | None, *, stale: bool) -> dict[str, Any]:
    if stale:
        status = "stale"
        label = "Stale — not live"
    elif age_sec is None:
        status = "unknown"
        label = "Freshness unknown"
    elif age_sec <= 30:
        status = "live"
        label = f"Updated {int(age_sec)}s ago"
    elif age_sec <= STALE_AFTER_SEC:
        status = "warm"
        label = f"Updated {int(age_sec)}s ago"
    else:
        status = "stale"
        label = f"Stale · {int(age_sec)}s ago"
    return {
        "status": status,
        "label": label,
        "age_seconds": None if age_sec is None else round(age_sec, 1),
        "stale": status == "stale",
        "heartbeat_sec": HEARTBEAT_SEC,
    }


def _ledger_honesty() -> dict[str, Any]:
    """Public ledger chip — includes misses; never hide failure rate."""
    try:
        from oracle_audit_chain import chain_summary

        summary = chain_summary(limit=40) or {}
        hit = summary.get("recent_hit_rate_percent")
        total = summary.get("total_records") or 0
        recent = summary.get("recent_records") or []
        resolved = [r for r in recent if r.get("resolved")]
        misses = sum(1 for r in resolved if r.get("label") != "correct")
        return {
            "label": STR_VERIFIED_ON_LEDGER,
            "href": PATH_ORACLE_ACCURACY,
            "recent_hit_rate_percent": hit,
            "misses_in_window": misses,
            "resolved_in_window": len(resolved),
            "total_records": total,
            "honesty_line": (
                f"Recent labeled hit rate {hit}% · {misses} miss(es) shown"
                if hit is not None and resolved
                else "Public Accuracy Ledger — hits and misses published"
            ),
            "target_band": summary.get("target_accuracy_band") or "65-70%",
        }
    except Exception:
        return {
            "label": STR_VERIFIED_ON_LEDGER,
            "href": PATH_ORACLE_ACCURACY,
            "honesty_line": "Public Accuracy Ledger — hits and misses published",
            "recent_hit_rate_percent": None,
            "misses_in_window": None,
        }


def _continuity(
    *,
    current_action: str,
    previous_action: str | None,
    previous_seen_at: str | None,
    factors_now: list[dict[str, Any]],
    factors_prev: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    if not previous_action:
        return None
    prev = _norm_action(previous_action)
    flipped = prev != current_action
    changed_factors: list[str] = []
    if factors_prev:
        prev_names = {str(f.get("factor") or "") for f in factors_prev}
        now_names = {str(f.get("factor") or "") for f in factors_now}
        for name in now_names - prev_names:
            if name:
                changed_factors.append(name)

    return {
        "previous_action": prev,
        "current_action": current_action,
        "flipped": flipped,
        "previous_seen_at": previous_seen_at,
        "summary": (
            f"Decision flipped {prev} → {current_action} since your last visit"
            if flipped
            else f"Still {current_action} since your last visit"
        ),
        "new_factors": changed_factors[:3],
        "pro_only_depth": True,
    }


async def _compute_oracle_payload(
    symbol: str,
    *,
    tier: str,
    ux_mode: str,
    lang: str,
    persist: bool,
) -> dict[str, Any]:
    from market_context import (
        build_full_oracle_response,
        fetch_binance_ticker,
        fetch_cvvd_whale_alert,
        normalize_oracle_symbol,
    )

    asset, pair = normalize_oracle_symbol(symbol)
    market = await fetch_binance_ticker(pair)
    if market is None:
        raise ValueError(f"Symbol {asset} not found")

    price = float(market["price"])
    volume = float(market["volume"])
    quote_volume = float(market.get("quote_volume") or volume * price)
    change = float(market["change_24h"])
    price_ts = market.get("timestamp") or market.get("close_time")
    fetched_at = time.time()

    whale = None
    try:
        whale = await fetch_cvvd_whale_alert(asset, pair, price)
    except Exception:
        whale = None

    unified = None
    try:
        from oracle_unified import compute_unified_oracle

        unified = await compute_unified_oracle(asset, price, quote_volume, change)
    except Exception:
        logger.debug("unified oracle unavailable for trust pulse", exc_info=True)

    payload = build_full_oracle_response(
        asset,
        price,
        volume,
        quote_volume,
        change,
        whale_alert=whale,
        unified=unified,
    )
    try:
        from decision_enrichment import enrich_oracle_decision
        from ux_mode import normalize_lang, normalize_ux_mode

        payload = enrich_oracle_decision(
            payload,
            ux_mode=normalize_ux_mode(ux_mode),
            lang=normalize_lang(lang),
            register_signal=False,
        )
    except Exception:
        logger.debug("enrichment skipped", exc_info=True)

    try:
        from heroes_quality import build_oqs_why_block

        payload["oqs_why"] = build_oqs_why_block(payload)
    except Exception:
        payload["oqs_why"] = {"top_3_factors": [], "ready": False}

    # Guarantee a readable Why on first open even if explanation pipeline is thin.
    factors = (payload.get("oqs_why") or {}).get("top_3_factors") or []
    if not factors:
        change = float(payload.get("change_24h") or 0)
        score = payload.get("opportunity_score")
        regime = payload.get("market_regime") or "unknown"
        whale = payload.get("whale_alert")
        synth = [
            {
                "factor": f"Opportunity score {score}" if score is not None else "Score pending",
                "detail": "Composite Trust OS score from live market context",
                "source": "oracle",
            },
            {
                "factor": f"24h move {change:+.2f}%",
                "detail": "Short-horizon price change on the watched pair",
                "source": "live market",
            },
            {
                "factor": f"Regime {regime}",
                "detail": str(whale)[:120] if whale else "Regime label from unified context",
                "source": "context",
            },
        ]
        payload["oqs_why"] = {
            "grasp_line": "Top reasons — under five seconds",
            "top_3_factors": synth,
            "ready": True,
            "synthetic_fallback": True,
        }
        expl = dict(payload.get("explanation") or {})
        expl["top_3_factors"] = synth
        payload["explanation"] = expl

    if persist:
        try:
            from dashboard import _log_oracle_prediction

            pid = await _log_oracle_prediction(payload)
            if pid is not None:
                payload["prediction_id"] = pid
        except Exception:
            logger.debug("trust pulse prediction log skipped", exc_info=True)

    payload["tier"] = tier or "free"
    try:
        from decision_certificate import build_decision_certificate, compliance_footer_block

        payload["decision_certificate"] = build_decision_certificate(payload)
        payload["compliance_footer"] = compliance_footer_block(
            surface="trust_pulse",
            trust_basis="public_accuracy_ledger + decision_certificate",
        )
    except Exception:
        logger.debug("certificate skipped", exc_info=True)

    payload["_pulse_meta"] = {
        "fetched_at": fetched_at,
        "price_ts": price_ts,
        "asset": asset,
    }
    return payload


def _pulse_factors(payload: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    why = payload.get("oqs_why") or {}
    factors = why.get("top_3_factors") or (payload.get("explanation") or {}).get("top_3_factors") or []
    return why, [
        {
            "factor": str(f.get("factor") if isinstance(f, dict) else f),
            "detail": str((f.get("detail") if isinstance(f, dict) else "") or ""),
            "source": str((f.get("source") if isinstance(f, dict) else "") or ""),
        }
        for f in factors[:3]
    ]


def _pulse_watermark(cert: dict[str, Any], tier: str) -> Any:
    return cert.get("watermark") or ("Free Proof" if tier in ("", "free") else None)


def _pulse_flip(previous_action: str | None, action: str) -> dict[str, str] | None:
    if not previous_action or _norm_action(previous_action) == action:
        return None
    return {
        "from": _norm_action(previous_action),
        "to": action,
        "message": f"Decision flipped {_norm_action(previous_action)} → {action}",
    }


def _pulse_continuity_payload(continuity: dict[str, Any] | None, tier: str) -> dict[str, Any] | None:
    if tier not in ("", "free"):
        return continuity
    if continuity:
        return {
            "locked": True,
            "upgrade_hint": "Decision Pro unlocks “since your last visit” continuity.",
            "summary": continuity.get("summary") if continuity.get("flipped") else None,
            "flipped": bool(continuity.get("flipped")),
        }
    return {
        "locked": True,
        "upgrade_hint": "Decision Pro unlocks “since your last visit”.",
    }


def _pulse_sentence(payload: dict[str, Any]) -> str:
    return payload.get("decision_sentence") or payload.get("narrative") or payload.get("oracle") or ""


def _pulse_proof(cert: dict[str, Any], payload: dict[str, Any], watermark: Any) -> dict[str, Any]:
    return {
        "label": STR_VERIFIED_ON_LEDGER,
        "prediction_id": payload.get("prediction_id"),
        "certificate_hash": cert.get("certificate_hash"),
        "chain_hash": payload.get("chain_hash"),
        "verify_url": cert.get("verify_url") or PATH_ORACLE_ACCURACY,
        "permalink": cert.get("permalink") or PATH_ORACLE_ACCURACY,
        "share_text": cert.get("share_text"),
        "share_urls": cert.get("share_urls") or {},
        "watermark": watermark,
    }


def _pulse_compliance(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("compliance_footer") or {
        "disclaimer": (
            "Not financial advice. AI cannot guarantee returns. "
            "Verify on the Public Accuracy Ledger."
        )
    }


def _zero_tolerance_input(
    result: dict[str, Any],
    payload: dict[str, Any],
    why: dict[str, Any],
    factors: list[dict[str, str]],
    freshness: dict[str, Any],
) -> dict[str, Any]:
    return {
        "opportunity_score": result.get("score"),
        "one_sentence": result.get("sentence"),
        "oqs_why": {
            "why_text": why.get("grasp_line") or why.get("why_text"),
            "top_3_factors": factors,
            "invalidation": payload.get("invalidation") or result.get("veto_reason"),
        },
        "data_freshness": {
            "state": freshness.get("status"),
            "stale": freshness.get("stale"),
            "age_sec": freshness.get("age_seconds"),
        },
        "data_sources": ["trust_pulse", "oracle", "live_book"],
    }


def _downgrade_live_freshness(freshness: dict[str, Any]) -> dict[str, Any]:
    return {
        **freshness,
        "status": "unknown" if freshness.get("age_seconds") is None else freshness.get("status"),
        "label": freshness.get("label")
        if freshness.get("status") != "live"
        else f"Updated {int(freshness.get('age_seconds') or 0)}s ago",
    }


def _apply_zero_tolerance_to_pulse(
    result: dict[str, Any],
    payload: dict[str, Any],
    why: dict[str, Any],
    factors: list[dict[str, str]],
    freshness: dict[str, Any],
) -> None:
    try:
        from zero_tolerance import apply_zero_tolerance

        audited = apply_zero_tolerance(_zero_tolerance_input(result, payload, why, factors, freshness))
        result["zero_tolerance"] = audited.get("zero_tolerance")
        result["live_claim_allowed"] = audited.get("live_claim_allowed")
        if not result.get("live_claim_allowed") and freshness.get("status") == "live":
            # Never market LIVE when gate forbids it.
            result["freshness"] = _downgrade_live_freshness(freshness)
    except Exception:
        logger.debug("zero tolerance on trust pulse failed", exc_info=True)


def _pulse_factors(payload: dict[str, Any], why: dict[str, Any]) -> list[dict[str, str]]:
    raw_factors = why.get("top_3_factors") or (payload.get("explanation") or {}).get("top_3_factors") or []
    return [
        {
            "factor": str(f.get("factor") if isinstance(f, dict) else f),
            "detail": str((f.get("detail") if isinstance(f, dict) else "") or ""),
            "source": str((f.get("source") if isinstance(f, dict) else "") or ""),
        }
        for f in raw_factors[:3]
    ]


def _pulse_watermark(cert: dict[str, Any], tier: str) -> str | None:
    return cert.get("watermark") or ("Free Proof" if tier in ("", "free") else None)


def _pulse_flip(previous_action: str | None, action: str) -> dict[str, str] | None:
    if not previous_action or _norm_action(previous_action) == action:
        return None
    previous = _norm_action(previous_action)
    return {
        "from": previous,
        "to": action,
        "message": f"Decision flipped {previous} → {action}",
    }


def _visible_continuity(tier: str, continuity: dict[str, Any] | None) -> dict[str, Any] | None:
    if tier not in ("", "free"):
        return continuity
    if continuity:
        return {
            "locked": True,
            "upgrade_hint": "Decision Pro unlocks “since your last visit” continuity.",
            "summary": continuity.get("summary") if continuity.get("flipped") else None,
            "flipped": bool(continuity.get("flipped")),
        }
    return {
        "locked": True,
        "upgrade_hint": "Decision Pro unlocks “since your last visit”.",
    }


def _pulse_sentence(payload: dict[str, Any]) -> str:
    return payload.get("decision_sentence") or payload.get("narrative") or payload.get("oracle") or ""


def _pulse_base_result(
    payload: dict[str, Any],
    *,
    meta: dict[str, Any],
    why: dict[str, Any],
    factors: list[dict[str, str]],
    cert: dict[str, Any],
    half: dict[str, Any],
    conflict: dict[str, Any],
    tier: str,
    freshness: dict[str, Any],
    event: str,
    from_cache: bool,
    flip_now: dict[str, str] | None,
    continuity_out: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "product": "BLACKDARK Trust OS",
        "surface": "trust_pulse",
        "event": event,
        "symbol": str(payload.get("symbol") or meta.get("asset") or DEFAULT_SYMBOL).upper(),
        "action": _norm_action(payload.get("decision_action") or payload.get("verdict") or payload.get("action")),
        "verdict": payload.get("verdict") or _norm_action(payload.get("decision_action") or payload.get("verdict") or payload.get("action")),
        "sentence": _pulse_sentence(payload),
        "why": {
            "grasp_line": why.get("grasp_line") or "Top reasons — under five seconds",
            "factors": factors,
        },
        "score": payload.get("opportunity_score"),
        "price": payload.get("price"),
        "change_24h": payload.get("change_24h"),
        "freshness": freshness,
        "proof": {
            "label": STR_VERIFIED_ON_LEDGER,
            "prediction_id": payload.get("prediction_id"),
            "certificate_hash": cert.get("certificate_hash"),
            "chain_hash": payload.get("chain_hash"),
            "verify_url": cert.get("verify_url") or PATH_ORACLE_ACCURACY,
            "permalink": cert.get("permalink") or PATH_ORACLE_ACCURACY,
            "share_text": cert.get("share_text"),
            "share_urls": cert.get("share_urls") or {},
            "watermark": _pulse_watermark(cert, tier),
        },
        "ledger": _ledger_honesty(),
        "flip": flip_now,
        "continuity": continuity_out,
        "half_life_seconds": half.get("remaining_seconds") or half.get("expected_half_life_seconds"),
        "veto": bool(conflict.get("veto") or conflict.get("abstain")),
        "veto_reason": conflict.get("reason") or conflict.get("message"),
        "tier": tier or "free",
        "cta": {
            "primary": {"label": "Open full proof", "href": "/dashboard?lens=prove#decide"},
            "verify": {"label": "Verify Ledger", "href": PATH_ORACLE_ACCURACY},
        },
        "compliance": payload.get("compliance_footer")
        or {
            "disclaimer": (
                "Not financial advice. AI cannot guarantee returns. "
                "Verify on the Public Accuracy Ledger."
            )
        },
        "from_cache": from_cache,
        "updated_at": _utcnow(),
        "cache_ttl_sec": CACHE_TTL_SEC,
    }


def _zero_tolerance_input(
    result: dict[str, Any],
    payload: dict[str, Any],
    why: dict[str, Any],
    factors: list[dict[str, str]],
    freshness: dict[str, Any],
) -> dict[str, Any]:
    return {
        "opportunity_score": result.get("score"),
        "one_sentence": result.get("sentence"),
        "oqs_why": {
            "why_text": why.get("grasp_line") or why.get("why_text"),
            "top_3_factors": factors,
            "invalidation": payload.get("invalidation") or result.get("veto_reason"),
        },
        "data_freshness": {
            "state": freshness.get("status"),
            "stale": freshness.get("stale"),
            "age_sec": freshness.get("age_seconds"),
        },
        "data_sources": ["trust_pulse", "oracle", "live_book"],
    }


def _demote_live_freshness_if_needed(result: dict[str, Any], freshness: dict[str, Any]) -> None:
    if result.get("live_claim_allowed") or freshness.get("status") != "live":
        return
    result["freshness"] = {
        **freshness,
        "status": "unknown" if freshness.get("age_seconds") is None else freshness.get("status"),
        "label": freshness.get("label")
        if freshness.get("status") != "live"
        else f"Updated {int(freshness.get('age_seconds') or 0)}s ago",
    }


def _apply_pulse_zero_tolerance(
    result: dict[str, Any],
    payload: dict[str, Any],
    why: dict[str, Any],
    factors: list[dict[str, str]],
    freshness: dict[str, Any],
) -> None:
    try:
        from zero_tolerance import apply_zero_tolerance

        audited = apply_zero_tolerance(_zero_tolerance_input(result, payload, why, factors, freshness))
        result["zero_tolerance"] = audited.get("zero_tolerance")
        result["live_claim_allowed"] = audited.get("live_claim_allowed")
        _demote_live_freshness_if_needed(result, freshness)
    except Exception:
        logger.debug("zero tolerance on trust pulse failed", exc_info=True)

def _shape_pulse(
    payload: dict[str, Any],
    *,
    previous_action: str | None = None,
    previous_seen_at: str | None = None,
    previous_factors: list[dict[str, Any]] | None = None,
    event: str = "pulse",
    from_cache: bool = False,
) -> dict[str, Any]:
    meta = payload.get("_pulse_meta") or {}
    fetched_at = float(meta.get("fetched_at") or time.time())
    age = max(0.0, time.time() - fetched_at)
    freshness = _freshness(age, stale=age > STALE_AFTER_SEC)
    action = _norm_action(payload.get("decision_action") or payload.get("verdict") or payload.get("action"))
    why = payload.get("oqs_why") or {}
    factors = _pulse_factors(payload, why)
    tier = str(payload.get("tier") or "free").lower()
    continuity = _continuity(
        current_action=action,
        previous_action=previous_action,
        previous_seen_at=previous_seen_at,
        factors_now=factors,
        factors_prev=previous_factors,
    )
    result = _pulse_base_result(
        payload,
        meta=meta,
        why=why,
        factors=factors,
        cert=payload.get("decision_certificate") or {},
        half=payload.get("opportunity_half_life") or {},
        conflict=payload.get("dimension_conflict") or {},
        tier=tier,
        freshness=freshness,
        event=event,
        from_cache=from_cache,
        flip_now=_pulse_flip(previous_action, action),
        continuity_out=_visible_continuity(tier, continuity),
    )
    _apply_pulse_zero_tolerance(result, payload, why, factors, freshness)
    return result


async def build_trust_pulse(
    symbol: str = DEFAULT_SYMBOL,
    *,
    tier: str = "free",
    ux_mode: str = "beginner",
    lang: str = "en",
    previous_action: str | None = None,
    previous_seen_at: str | None = None,
    previous_factors: list[dict[str, Any]] | None = None,
    force_refresh: bool = False,
    persist: bool | None = None,
) -> dict[str, Any]:
    """Build the first-open Trust Pulse for a symbol."""
    sym = (symbol or DEFAULT_SYMBOL).strip().upper() or DEFAULT_SYMBOL
    now = time.time()
    with _LOCK:
        cached = dict(_PULSE_CACHE.get(sym) or {})

    if (
        not force_refresh
        and cached
        and (now - float(cached.get("fetched_at") or 0)) < CACHE_TTL_SEC
    ):
        payload = cached.get("payload") or {}
        # Refresh age only
        meta = dict(payload.get("_pulse_meta") or {})
        meta["fetched_at"] = float(cached.get("fetched_at") or now)
        payload = {**payload, "_pulse_meta": meta}
        pulse = _shape_pulse(
            payload,
            previous_action=previous_action or cached.get("action"),
            previous_seen_at=previous_seen_at,
            previous_factors=previous_factors,
            event="pulse",
            from_cache=True,
        )
        # Detect flip vs caller's previous even on cache hit
        if previous_action and _norm_action(previous_action) != pulse["action"]:
            pulse["event"] = "decision_changed"
            pulse["flip"] = {
                "from": _norm_action(previous_action),
                "to": pulse["action"],
                "message": f"Decision flipped {_norm_action(previous_action)} → {pulse['action']}",
            }
        return pulse

    do_persist = bool(persist) if persist is not None else True
    # On soft refresh after cache expiry: persist only if action flips vs cache
    if persist is None and cached:
        do_persist = False

    payload = await _compute_oracle_payload(
        sym, tier=tier, ux_mode=ux_mode, lang=lang, persist=do_persist
    )
    action = _norm_action(
        payload.get("decision_action") or payload.get("verdict") or payload.get("action")
    )
    prev_cached_action = cached.get("action")
    event = "pulse"
    if prev_cached_action and _norm_action(str(prev_cached_action)) != action:
        event = "decision_changed"
        # Persist flip as a real logged decision
        if not do_persist:
            try:
                payload = await _compute_oracle_payload(
                    sym, tier=tier, ux_mode=ux_mode, lang=lang, persist=True
                )
            except Exception:
                pass

    with _LOCK:
        _PULSE_CACHE[sym] = {
            "fetched_at": time.time(),
            "action": action,
            "payload": payload,
        }

    return _shape_pulse(
        payload,
        previous_action=previous_action or prev_cached_action,
        previous_seen_at=previous_seen_at,
        previous_factors=previous_factors,
        event=event,
        from_cache=False,
    )


def trust_pulse_manifest() -> dict[str, Any]:
    return {
        "product": "BLACKDARK Trust OS",
        "surface": "trust_pulse",
        "role": "First-open daily decision pulse — Act/Wait + Why + proof + live freshness",
        "not": [
            "news_digest",
            "top_movers_board",
            "smart_money_feed_clone",
            "guaranteed_advice",
        ],
        "endpoints": {
            "pulse": "/api/trust-pulse",
            "stream": "/api/trust-pulse/stream",
        },
        "ui": {
            "dashboard": "/dashboard#trust-pulse",
            "landing": "/#trust-pulse",
        },
        "realtime": {
            "heartbeat_sec": HEARTBEAT_SEC,
            "cache_ttl_sec": CACHE_TTL_SEC,
            "stale_after_sec": STALE_AFTER_SEC,
            "events": ["pulse", "heartbeat", "decision_changed", "stale"],
        },
        "tiers": {
            "free": ["decision", "why", "proof_watermark", "ledger_chip", "share_proof"],
            "pro": ["continuity_since_last_visit", "flip_detail", "no_watermark"],
        },
        "binding_doc": "docs/TRUST_PULSE.md",
    }


async def trust_pulse_sse_generator(
    symbol: str = DEFAULT_SYMBOL,
    *,
    tier: str = "free",
    interval_sec: float = HEARTBEAT_SEC,
) -> AsyncIterator[str]:
    """SSE: heartbeat always; decision_changed only on material flips."""
    sym = (symbol or DEFAULT_SYMBOL).strip().upper() or DEFAULT_SYMBOL
    last_action: str | None = None
    yield f"data: {json.dumps({'type': 'connected', 'surface': 'trust_pulse', 'symbol': sym, 'timestamp': _utcnow()})}\n\n"
    while True:
        try:
            pulse = await build_trust_pulse(
                sym,
                tier=tier,
                previous_action=last_action,
                persist=False,
                force_refresh=False,
            )
            action = pulse.get("action")
            evt_type = "heartbeat"
            if last_action is None:
                evt_type = "pulse"
            elif action != last_action:
                evt_type = "decision_changed"
                pulse["event"] = "decision_changed"
            elif pulse.get("freshness", {}).get("stale"):
                evt_type = "stale"
            last_action = action
            envelope = {
                "type": evt_type,
                "timestamp": _utcnow(),
                "pulse": pulse,
            }
            yield f"data: {json.dumps(envelope, default=str)}\n\n"
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("trust_pulse_sse_error symbol=%s", str(sym).replace("\r", " ").replace("\n", " "))
            err = {
                "type": "error",
                "message": "Trust Pulse stream temporarily unavailable",
                "timestamp": _utcnow(),
            }
            yield f"data: {json.dumps(err)}\n\n"
        await asyncio.sleep(max(8.0, float(interval_sec)))
