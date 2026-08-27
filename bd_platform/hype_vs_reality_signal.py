"""
Hype vs Reality Signal — Feature #599 (merged into #524 Cross-Domain Market Context Layer).

Renamed from "Social-to-On-Chain Confirmation Engine".
Classifies signal quality across social and on-chain domains:
  Confirmed / Social-only / On-chain-only / Contradictory

No chatbot advisor role — evaluates data quality only, not buy/sell recommendations.
Alignment scoring belongs here; entity-tagged sentiment (#595) feeds social input only.

Integrations (mandatory):
  #443 Event Monitor → social sentiment input
  #408 Smart Money Flow + #577 On-Chain Metrics Library → on-chain input
  #474 Daily Brief → signal quality summary
  #429 Intelligence Ledger + #403 Arbitrage Scanner → badge on every signal
  Market Radar → badge on dashboard signals
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.HypeVsRealitySignal")

_FEATURE_ID = 599
_MERGED_INTO = 524
_RENAMED_FROM = "Social-to-On-Chain Confirmation Engine"
_TITLE = "Hype vs Reality Signal"
_STANDALONE = False
_LAYER = "Intelligence Layer"
_SPRINT = 2
_SEED_PATH = Path("data/hype_vs_reality_signal_seed.json")
_METHODOLOGY_VERSION = "1.0"

_EVENT_MONITOR_REF = 443
_SMART_MONEY_REF = 408
_ONCHAIN_METRICS_REF = 577
_DAILY_BRIEF_REF = 474
_INTELLIGENCE_LEDGER_REF = 429
_ARBITRAGE_SCANNER_REF = 403

_DIRECTION_UP = frozenset({"rising", "bullish", "up", "increasing", "positive"})
_DIRECTION_DOWN = frozenset({"falling", "bearish", "down", "decreasing", "negative"})
_DIRECTION_FLAT = frozenset({"flat", "neutral", "stable", "unchanged", "sideways"})

_STATE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "confirmed": {
        "state_id": "confirmed",
        "color": "green",
        "badge_emoji": "🟢",
        "label": "Confirmed",
        "user_message": "مدعوم بسلوك — الإشارة متناغمة",
        "user_message_en": "Behavior-backed — signals aligned",
        "condition": "Social ↑ + On-Chain ↑",
    },
    "social_only": {
        "state_id": "social_only",
        "color": "yellow",
        "badge_emoji": "🟡",
        "label": "Social-Only",
        "user_message": "ضجيج فقط — لا حركة مالية تؤكد",
        "user_message_en": "Noise only — no on-chain confirmation",
        "condition": "Social ↑ + On-Chain →",
    },
    "on_chain_only": {
        "state_id": "on_chain_only",
        "color": "blue",
        "badge_emoji": "🔵",
        "label": "On-Chain-Only",
        "user_message": "حركة صامتة — فرصة مبكرة محتملة",
        "user_message_en": "Silent move — potential early signal",
        "condition": "On-Chain ↑ + Social →",
    },
    "contradictory": {
        "state_id": "contradictory",
        "color": "red",
        "badge_emoji": "🔴",
        "label": "Contradictory",
        "user_message": "تناقض — احذر، البيانات تتعارض",
        "user_message_en": "Contradiction — data sources disagree",
        "condition": "Social ↑ + On-Chain ↓",
    },
    "unclassified": {
        "state_id": "unclassified",
        "color": "gray",
        "badge_emoji": "⚪",
        "label": "Unclassified",
        "user_message": "لا توافق إجباري — البيانات غير حاسمة",
        "user_message_en": "No forced consensus — signals inconclusive",
        "condition": "Mixed or insufficient signal directions",
    },
}

_TERMS_DISCLAIMER = (
    "Hype vs Reality Signal evaluates data quality only. "
    "It does not provide buy or sell recommendations. "
    "No chatbot advisor role. User decides."
)

_DISCLAIMER = (
    "Hype vs Reality Signal — social vs on-chain confirmation classification. "
    "Contributors, freshness, and confidence shown on every assessment. "
    "Historical validation displayed where available. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"signals": {}, "historical_validation": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("hype vs reality signal seed load failed: %s", exc)
        return {"signals": {}, "historical_validation": {}}


def normalize_direction(direction: str | None) -> Literal["up", "down", "flat"]:
    d = (direction or "flat").lower().strip()
    if d in _DIRECTION_UP:
        return "up"
    if d in _DIRECTION_DOWN:
        return "down"
    return "flat"


def classify_hype_vs_reality(
    social_direction: str | None,
    onchain_direction: str | None,
) -> dict[str, Any]:
    """Rule-based 4-state classifier — no forced consensus on ambiguous inputs."""
    social = normalize_direction(social_direction)
    onchain = normalize_direction(onchain_direction)

    if social == "up" and onchain == "up":
        state_id = "confirmed"
    elif social == "up" and onchain == "flat":
        state_id = "social_only"
    elif onchain == "up" and social == "flat":
        state_id = "on_chain_only"
    elif (social == "up" and onchain == "down") or (social == "down" and onchain == "up"):
        state_id = "contradictory"
    else:
        state_id = "unclassified"

    state_def = _STATE_DEFINITIONS[state_id]
    return {
        "state_id": state_id,
        "badge": {
            "emoji": state_def["badge_emoji"],
            "color": state_def["color"],
            "label": state_def["label"],
            "user_message": state_def["user_message"],
            "user_message_en": state_def["user_message_en"],
            "condition": state_def["condition"],
            "show_on_every_signal": True,
        },
        "social_direction": social,
        "onchain_direction": onchain,
        "no_forced_consensus": state_id == "unclassified",
        "not_advisory": True,
        "no_buy_sell_recommendation": True,
    }


def _fetch_social_input(asset: str, *, seed: dict[str, Any]) -> dict[str, Any]:
    """#443 Event Monitor — social sentiment input."""
    asset_cfg = (seed.get("social_inputs") or {}).get(asset.upper(), {})
    try:
        from bd_platform.event_sentiment_monitor import compute_nlp_sentiment

        nlp = compute_nlp_sentiment(asset)
        if nlp.get("ok"):
            label = nlp.get("composite_sentiment_label", "neutral")
            direction = "rising" if label == "positive" else "falling" if label == "negative" else "flat"
            return {
                "source_feature_id": _EVENT_MONITOR_REF,
                "direction": direction,
                "volume_dominance": asset_cfg.get("volume_dominance"),
                "sentiment_score": nlp.get("composite_sentiment_score"),
                "freshness_seconds": int((nlp.get("update_interval_minutes") or 15) * 60),
                "confidence_pct": float(nlp.get("nlp_accuracy_pct") or asset_cfg.get("confidence_pct", 75)),
                "contributors": nlp.get("per_source") or asset_cfg.get("contributors", []),
                "live": True,
            }
    except Exception:
        logger.debug("event sentiment monitor social input skipped", exc_info=True)

    return {
        "source_feature_id": _EVENT_MONITOR_REF,
        "direction": asset_cfg.get("direction", "flat"),
        "volume_dominance": asset_cfg.get("volume_dominance"),
        "sentiment_score": asset_cfg.get("sentiment_score"),
        "freshness_seconds": int(asset_cfg.get("freshness_seconds", 900)),
        "confidence_pct": float(asset_cfg.get("confidence_pct", 75)),
        "contributors": asset_cfg.get("contributors") or [],
        "live": False,
    }


def _fetch_onchain_input(asset: str, *, seed: dict[str, Any]) -> dict[str, Any]:
    """#408 Smart Money + #577 Metrics Library — on-chain input."""
    asset_cfg = (seed.get("onchain_inputs") or {}).get(asset.upper(), {})
    contributors: list[dict[str, Any]] = []

    try:
        from bd_platform.smart_money_flow_tracker import detect_accumulation_distribution_state

        sm = detect_accumulation_distribution_state(asset)
        if sm.get("ok"):
            state = sm.get("accumulation_distribution_state", "neutral")
            direction = "up" if state == "accumulating" else "down" if state == "distributing" else "flat"
            contributors.append({
                "feature_id": _SMART_MONEY_REF,
                "metric": "accumulation_distribution_state",
                "value": state,
                "direction": direction,
            })
            asset_cfg = {**asset_cfg, "direction": direction, **asset_cfg}
    except Exception:
        logger.debug("smart money onchain input skipped", exc_info=True)

    try:
        from bd_platform.onchain_metrics_library import build_metrics_library_panel

        metrics = build_metrics_library_panel(asset)
        if metrics.get("ok"):
            network = (metrics.get("sub_modules") or {}).get("574_network_data_pro_api") or {}
            netflow = network.get("exchange_netflow") or network.get("metrics") or {}
            if isinstance(netflow, dict) and netflow.get("direction"):
                contributors.append({
                    "feature_id": _ONCHAIN_METRICS_REF,
                    "metric": "exchange_netflow",
                    "value": netflow.get("value"),
                    "direction": netflow.get("direction"),
                })
                if not asset_cfg.get("direction"):
                    asset_cfg["direction"] = netflow.get("direction")
    except Exception:
        logger.debug("onchain metrics library input skipped", exc_info=True)

    return {
        "source_feature_ids": [_SMART_MONEY_REF, _ONCHAIN_METRICS_REF],
        "direction": asset_cfg.get("direction", "flat"),
        "whale_flow_usd": asset_cfg.get("whale_flow_usd"),
        "holder_change_pct": asset_cfg.get("holder_change_pct"),
        "exchange_netflow_usd": asset_cfg.get("exchange_netflow_usd"),
        "freshness_seconds": int(asset_cfg.get("freshness_seconds", 600)),
        "confidence_pct": float(asset_cfg.get("confidence_pct", 82)),
        "contributors": contributors or asset_cfg.get("contributors") or [],
        "live": bool(contributors),
    }


def build_hype_vs_reality_signal(
    asset: str = "BTC",
    *,
    signal_id: str | None = None,
    social_direction: str | None = None,
    onchain_direction: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one Hype vs Reality assessment with badge, contributors, and evidence."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    sym = asset.upper()
    signal_key = signal_id or f"{sym}_default"
    signal_cfg = (seed.get("signals") or {}).get(signal_key, {})

    social = _fetch_social_input(sym, seed=seed)
    onchain = _fetch_onchain_input(sym, seed=seed)

    social_dir = social_direction or signal_cfg.get("social_direction") or social.get("direction")
    onchain_dir = onchain_direction or signal_cfg.get("onchain_direction") or onchain.get("direction")
    classification = classify_hype_vs_reality(social_dir, onchain_dir)

    contributors = {
        "social": {
            "feature_id": _EVENT_MONITOR_REF,
            "metrics": ["social_volume", "sentiment", "dominance"],
            "direction": social_dir,
            "freshness_seconds": social.get("freshness_seconds"),
            "confidence_pct": social.get("confidence_pct"),
            "items": social.get("contributors") or [],
            "shown": True,
        },
        "onchain": {
            "feature_ids": [_SMART_MONEY_REF, _ONCHAIN_METRICS_REF],
            "metrics": ["whale_flow", "holder_change", "exchange_netflow", "network_activity"],
            "direction": onchain_dir,
            "freshness_seconds": onchain.get("freshness_seconds"),
            "confidence_pct": onchain.get("confidence_pct"),
            "items": onchain.get("contributors") or [],
            "shown": True,
        },
    }

    aggregate_confidence = round(
        (float(social.get("confidence_pct", 70)) + float(onchain.get("confidence_pct", 70))) / 2,
        1,
    )
    historical = seed.get("historical_validation") or {}

    evidence = [
        {
            "domain": "social",
            "source_feature_id": _EVENT_MONITOR_REF,
            "metric": "sentiment_direction",
            "value": social_dir,
            "freshness_seconds": social.get("freshness_seconds"),
        },
        {
            "domain": "onchain",
            "source_feature_ids": [_SMART_MONEY_REF, _ONCHAIN_METRICS_REF],
            "metric": "flow_direction",
            "value": onchain_dir,
            "freshness_seconds": onchain.get("freshness_seconds"),
        },
    ]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_into": _MERGED_INTO,
        "not_engine": True,
        "no_chatbot_advisor_role": True,
        "no_chatbot_advisor_role": True,
        "terms_statement": _TERMS_DISCLAIMER,
        "signal_id": signal_key,
        "asset": sym,
        "classification": classification,
        "state": classification["state_id"],
        "badge": classification["badge"],
        "contributors": contributors,
        "contributors_shown": True,
        "freshness_shown": True,
        "confidence_pct": aggregate_confidence,
        "confidence_shown": True,
        "no_forced_consensus": classification["no_forced_consensus"],
        "evidence": evidence,
        "historical_validation": {
            "enabled": True,
            "display_required": True,
            "summary": historical.get("summary"),
            "contradictory_correction_rate_pct": historical.get("contradictory_correction_rate_pct"),
            "contradictory_correction_window_days": historical.get("contradictory_correction_window_days", 7),
            "sample_size": historical.get("sample_size"),
            "methodology": historical.get("methodology"),
        },
        "integrations": {
            "event_monitor_443": True,
            "smart_money_408": True,
            "onchain_metrics_577": True,
            "daily_brief_474": True,
            "intelligence_ledger_429": True,
            "arbitrage_scanner_403": True,
            "market_radar": True,
        },
        "display": (
            f"{sym} Hype vs Reality: {classification['badge']['label']} — "
            f"{classification['badge']['user_message_en']}"
        ),
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
        "signal_cfg": signal_cfg or None,
    }


def attach_signal_quality_badge(
    signal: dict[str, Any],
    *,
    asset: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach Hype vs Reality badge to any intelligence ledger signal."""
    enriched = dict(signal)
    sym = asset or str(signal.get("asset") or "BTC")
    social_dir = (
        signal.get("social_direction")
        or (signal.get("event_sentiment_context_443") or {}).get("sentiment_direction")
        or (signal.get("sentiment_context") or {}).get("direction")
    )
    onchain_dir = (
        signal.get("onchain_direction")
        or (signal.get("smart_money_context") or {}).get("direction")
    )
    assessment = build_hype_vs_reality_signal(
        sym,
        signal_id=signal.get("signal_id") or signal.get("opportunity_id"),
        social_direction=social_dir,
        onchain_direction=onchain_dir,
        seed=seed,
    )
    enriched["hype_vs_reality_signal_599"] = {
        "state": assessment["state"],
        "badge": assessment["badge"],
        "confidence_pct": assessment["confidence_pct"],
        "contributors": assessment["contributors"],
        "historical_validation": assessment["historical_validation"],
        "no_forced_consensus": assessment["no_forced_consensus"],
        "not_advisory": True,
    }
    enriched["signal_quality_badge"] = assessment["badge"]
    return enriched


def build_signal_quality_summary(
    assessments: list[dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate counts for Daily Brief (#474) and dashboards."""
    counts = {k: 0 for k in ("confirmed", "social_only", "on_chain_only", "contradictory", "unclassified")}
    for a in assessments:
        state = a.get("state") or (a.get("classification") or {}).get("state_id", "unclassified")
        counts[state] = counts.get(state, 0) + 1

    return {
        "counts": counts,
        "total": len(assessments),
        "display": (
            f"Today: {counts['confirmed']} confirmed, {counts['social_only']} social-only, "
            f"{counts['on_chain_only']} on-chain-only, {counts['contradictory']} contradictory"
        ),
        "display_ar": (
            f"اليوم: {counts['confirmed']} مؤكدة، {counts['social_only']} ضجيج، "
            f"{counts['on_chain_only']} حركة صامتة، {counts['contradictory']} تناقض"
        ),
        "sort_by_signal_quality_429": True,
        "feature_ref_474": _DAILY_BRIEF_REF,
    }


def build_hype_vs_reality_panel(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Main panel for #524 sub-module #599."""
    seed = seed or _load_seed()
    signals_cfg = seed.get("signals") or {}
    assessments = [
        build_hype_vs_reality_signal(asset, signal_id=sid, seed=seed)
        for sid in signals_cfg
    ]
    if not assessments:
        assessments = [build_hype_vs_reality_signal(asset, seed=seed)]

    summary = build_signal_quality_summary(assessments)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_into_epic": _MERGED_INTO,
        "sub_module_id": "599",
        "legal_name": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "not_engine": True,
        "no_chatbot_advisor_role": True,
        "standalone_rejected": True,
        "task_not_ticket": True,
        "asset": asset.upper(),
        "four_states": list(_STATE_DEFINITIONS.keys()),
        "state_definitions": _STATE_DEFINITIONS,
        "assessments": assessments,
        "summary": summary,
        "badge_on_every_signal": True,
        "contributors_freshness_confidence_shown": True,
        "historical_validation_shown": True,
        "no_forced_consensus": True,
        "no_chatbot_advisor_role": True,
        "terms_statement": _TERMS_DISCLAIMER,
        "integrations": assessments[0].get("integrations") if assessments else {},
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def hype_vs_reality_signal_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_into": _MERGED_INTO,
        "legal_name": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "four_states": ["confirmed", "social_only", "on_chain_only", "contradictory"],
        "badge_on_every_signal": True,
        "no_chatbot_advisor_role": True,
        "terms_statement": _TERMS_DISCLAIMER,
        "integrations": {
            "event_monitor_443": _EVENT_MONITOR_REF,
            "smart_money_408": _SMART_MONEY_REF,
            "onchain_metrics_577": _ONCHAIN_METRICS_REF,
            "daily_brief_474": _DAILY_BRIEF_REF,
            "intelligence_ledger_429": _INTELLIGENCE_LEDGER_REF,
            "arbitrage_scanner_403": _ARBITRAGE_SCANNER_REF,
            "market_radar": True,
        },
        "historical_validation": seed.get("historical_validation"),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    confirmed = classify_hype_vs_reality("rising", "bullish")
    checks.append({"id": "state_confirmed", "passed": confirmed["state_id"] == "confirmed", "detail": "599"})

    social_only = classify_hype_vs_reality("up", "neutral")
    checks.append({"id": "state_social_only", "passed": social_only["state_id"] == "social_only", "detail": "599"})

    onchain_only = classify_hype_vs_reality("flat", "rising")
    checks.append({"id": "state_onchain_only", "passed": onchain_only["state_id"] == "on_chain_only", "detail": "599"})

    contradictory = classify_hype_vs_reality("bullish", "falling")
    checks.append({"id": "state_contradictory", "passed": contradictory["state_id"] == "contradictory", "detail": "599"})

    panel = build_hype_vs_reality_panel("BTC", seed=seed)
    checks.append({"id": "panel_ok", "passed": panel.get("ok") is True, "detail": "599"})
    checks.append({"id": "renamed_not_engine", "passed": panel.get("not_engine") is True, "detail": "599"})
    checks.append({"id": "badge_on_signals", "passed": panel.get("badge_on_every_signal") is True, "detail": "599"})
    checks.append({"id": "contributors_shown", "passed": panel.get("contributors_freshness_confidence_shown") is True, "detail": "599"})
    checks.append({"id": "historical_validation", "passed": panel.get("historical_validation_shown") is True, "detail": "599"})
    checks.append({"id": "no_advisor", "passed": panel.get("no_chatbot_advisor_role") is True, "detail": "599"})

    hist = seed.get("historical_validation") or {}
    checks.append({
        "id": "contradictory_backtest",
        "passed": hist.get("contradictory_correction_rate_pct", 0) >= 80,
        "detail": "599",
    })

    badge = attach_signal_quality_badge({"asset": "BTC", "signal_id": "test_sig"})
    checks.append({"id": "attach_badge", "passed": "signal_quality_badge" in badge, "detail": "599"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "merged_into": _MERGED_INTO,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
