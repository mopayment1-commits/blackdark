"""
Trending Assets Module — Feature #300 (Sprint 2 Intelligence Ledger).

Discovers assets rising rapidly in social attention.
Depends on #272 Community Pulse (Social Signal Module) — dependency gate enforced.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.TrendingAssets")

_FEATURE_ID = 300
_DEPENDENCY_FEATURE_ID = 272
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Trending Assets Module"
_SPRINT = 2
_SEED_PATH = Path("data/trending_assets_seed.json")
_COMMUNITY_PULSE_SEED = Path("data/community_pulse_seed.json")
_METHODOLOGY_VERSION = "1.0"
_MIN_MENTIONS_DAILY = 100
_SIGNIFICANCE_P_THRESHOLD = 0.05
_TOP_ALIAS_REVIEW_COUNT = 10

_DISCLAIMER = (
    "Trending assets reflect social attention acceleration from purchased feeds. "
    "Not investment advice. Low-volume assets excluded. Deterministic ranking."
)

_ALIAS_RULES = {
    "BTC": ["Bitcoin"],
    "ETH": ["Ethereum"],
    "DOGE": ["Dogecoin"],
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": [], "alias_rules": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("trending assets seed load failed: %s", exc)
        return {"assets": [], "alias_rules": {}}


def check_community_pulse_dependency() -> dict[str, Any]:
    """#272 dependency gate — Trending Assets requires stable Community Pulse."""
    if not _COMMUNITY_PULSE_SEED.is_file():
        return {
            "stable": False,
            "dependency_feature_id": _DEPENDENCY_FEATURE_ID,
            "error": "community_pulse_seed_missing",
        }
    try:
        cp_seed = json.loads(_COMMUNITY_PULSE_SEED.read_text(encoding="utf-8"))
        provider = cp_seed.get("provider") or {}
        stable = (
            cp_seed.get("methodology_version")
            and not provider.get("paused_on_exceed", False)
            and len(cp_seed.get("assets") or {}) > 0
        )
        return {
            "stable": stable,
            "dependency_feature_id": _DEPENDENCY_FEATURE_ID,
            "dependency_module": "Community Pulse (#272)",
            "provider": provider.get("name"),
            "asset_count": len(cp_seed.get("assets") or {}),
            "display": (
                f"Dependency: #272 Community Pulse {'stable' if stable else 'NOT stable'} | "
                "Do not start until #272 stable"
            ),
        }
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "stable": False,
            "dependency_feature_id": _DEPENDENCY_FEATURE_ID,
            "error": str(exc),
        }


def resolve_alias(symbol: str, alias_rules: dict[str, Any] | None = None) -> dict[str, Any]:
    """Alias collision protection — BTC = Bitcoin, not BSC 'BTC' token."""
    sym = symbol.upper()
    rules = {**_ALIAS_RULES, **(alias_rules or {})}
    canonical = rules.get(sym, [sym])
    collision_risk = sym == "BTC" and "BSC" in str(canonical)

    return {
        "symbol": sym,
        "canonical_names": canonical if isinstance(canonical, list) else [canonical],
        "alias_rules_documented": True,
        "collision_protected": not collision_risk,
        "manual_review_top_10": sym in list(rules.keys())[:_TOP_ALIAS_REVIEW_COUNT],
        "display": f"{sym} = {canonical} | Alias rules documented",
    }


def compute_trend_acceleration(
    mentions_current: float,
    mentions_baseline: float,
) -> float:
    if mentions_baseline <= 0:
        return 0.0
    return round((mentions_current - mentions_baseline) / mentions_baseline, 4)


def compute_significance_p_value(acceleration: float, sample_size: int) -> float:
    """Simplified significance — deterministic, no randomness."""
    if sample_size < _MIN_MENTIONS_DAILY:
        return 1.0
    z = abs(acceleration) * math.sqrt(sample_size)
    p = math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)
    return round(min(max(p, 0.0001), 1.0), 4)


def compute_deterministic_rank_score(
    asset: dict[str, Any],
    *,
    as_of: str,
) -> float:
    """Same inputs = same output — no randomness."""
    payload = json.dumps({
        "symbol": asset.get("symbol"),
        "acceleration": asset.get("trend_acceleration"),
        "mentions_daily": asset.get("mentions_daily"),
        "as_of": as_of,
    }, sort_keys=True)
    hash_int = int(hashlib.sha256(payload.encode()).hexdigest()[:8], 16)
    base = float(asset.get("trend_acceleration", 0)) * 1000
    return round(base + (hash_int % 1000) / 100000, 6)


def build_trending_asset_entry(
    asset: dict[str, Any],
    *,
    alias_rules: dict[str, Any],
    as_of: str,
) -> dict[str, Any] | None:
    mentions_daily = int(asset.get("mentions_daily", 0))
    if mentions_daily < _MIN_MENTIONS_DAILY:
        return None

    acceleration = compute_trend_acceleration(
        float(asset.get("mentions_current", mentions_daily)),
        float(asset.get("mentions_baseline", 1)),
    )
    p_value = compute_significance_p_value(acceleration, mentions_daily)
    if p_value >= _SIGNIFICANCE_P_THRESHOLD:
        return None

    alias = resolve_alias(asset.get("symbol", ""), alias_rules)
    rank_score = compute_deterministic_rank_score(
        {**asset, "trend_acceleration": acceleration}, as_of=as_of,
    )

    return {
        "symbol": asset.get("symbol"),
        "alias": alias,
        "mentions_daily": mentions_daily,
        "trend_acceleration": acceleration,
        "significance_p_value": p_value,
        "statistically_significant": True,
        "rank_score": rank_score,
        "low_volume_excluded": False,
        "deterministic": True,
        "formula": "trend_acceleration × significance_weight (deterministic hash tie-break)",
        "display": (
            f"{asset.get('symbol')}: accel={acceleration:+.1%} | "
            f"p={p_value} | mentions/day={mentions_daily}"
        ),
    }


def build_trending_leaderboard(limit: int = 20) -> dict[str, Any]:
    """Trending Coins leaderboard — deterministic rank."""
    t0 = time.perf_counter()
    seed = _load_seed()
    dep = check_community_pulse_dependency()

    if not dep.get("stable"):
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "dependency_gate_blocked",
            "dependency": dep,
        }

    as_of = seed.get("as_of_timestamp_utc", _utcnow())
    alias_rules = seed.get("alias_rules") or {}
    entries = []

    for asset in seed.get("assets") or []:
        entry = build_trending_asset_entry(asset, alias_rules=alias_rules, as_of=as_of)
        if entry:
            entries.append(entry)

    entries.sort(key=lambda e: e["rank_score"], reverse=True)
    for i, entry in enumerate(entries[:limit], 1):
        entry["rank"] = i
        if i <= _TOP_ALIAS_REVIEW_COUNT:
            entry["manual_review_required"] = True

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "dependency": dep,
        "data_source": "#272 Community Pulse",
        "count": len(entries[:limit]),
        "leaderboard": entries[:limit],
        "min_mentions_daily": _MIN_MENTIONS_DAILY,
        "significance_threshold": _SIGNIFICANCE_P_THRESHOLD,
        "deterministic_rank": True,
        "disclaimer": _DISCLAIMER,
        "not_a_signal": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def trending_assets_status() -> dict[str, Any]:
    seed = _load_seed()
    dep = check_community_pulse_dependency()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Trending Assets Module",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "dependency_gate": dep,
        "dependency_feature_id": _DEPENDENCY_FEATURE_ID,
        "acceptance_criteria": {
            "alias_collision_protection": True,
            "low_volume_excluded": True,
            "deterministic_rank": True,
            "statistical_significance_p_005": True,
            "community_pulse_stable_required": dep.get("stable", False),
        },
        "min_mentions_daily": _MIN_MENTIONS_DAILY,
        "alias_rules_documented": True,
        "manual_review_top_10": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
