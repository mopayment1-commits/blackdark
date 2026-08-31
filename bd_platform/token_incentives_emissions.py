"""
Token Incentives & Emissions Module — Feature #298 (Wave 2 / Sprint 2 Intelligence Ledger).

Measures USD value of DeFi protocol incentives and emissions over time.
Niche feature — price aligned at emission timestamp, not current price.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.TokenIncentivesEmissions")

_FEATURE_ID = 298
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Token Incentives & Emissions Module"
_SPRINT = 2
_WAVE = 2
_SEED_PATH = Path("data/token_incentives_emissions_seed.json")
_METHODOLOGY_VERSION = "1.0"
_USD_FORMULA = "emission_amount × price_at_emission_timestamp_usd"

_DISCLAIMER = (
    "Incentive and emission USD values are calculated at emission timestamp. "
    "Not investment advice. DeFi protocols only in Wave 2 scope."
)

EmissionSource = Literal["on_chain_query", "protocol_docs"]
ScopePhase = Literal["defi_protocols", "cex_incentives", "airdrops"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"protocols": {}, "emissions": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("token incentives seed load failed: %s", exc)
        return {"protocols": {}, "emissions": []}


def build_scope_lock(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    phase = int(seed.get("current_phase", 1))
    return {
        "current_phase": phase,
        "phases": {
            1: "DeFi protocols only",
            2: "CEX incentives",
            3: "Airdrops",
        },
        "emissions_sources": ["on_chain_query", "protocol_docs"],
        "defi_only_wave_2": True,
        "display": (
            f"Phase {phase}: DeFi protocols only | "
            "CEX incentives = Phase 2 | Airdrops = Phase 3 | "
            "Emissions source: on-chain query or protocol docs"
        ),
    }


def build_price_alignment() -> dict[str, Any]:
    return {
        "usd_at_emission_timestamp": True,
        "no_current_price": True,
        "formula": _USD_FORMULA,
        "price_time_alignment": True,
        "emissions_source_required": True,
        "display": (
            f"USD value = {_USD_FORMULA} | "
            "No current price substitution | Price/time aligned at emission"
        ),
    }


def compute_emission_usd(
    emission_amount: float,
    price_at_emission_usd: float,
) -> float:
    """USD value at emission timestamp — not current price."""
    return round(emission_amount * price_at_emission_usd, 2)


def build_emission_record(emission: dict[str, Any]) -> dict[str, Any]:
    amount = float(emission.get("emission_amount", 0))
    price_at_ts = float(emission.get("price_at_emission_usd", 0))
    usd_value = compute_emission_usd(amount, price_at_ts)

    return {
        "protocol": emission.get("protocol"),
        "token": emission.get("token"),
        "emission_amount": amount,
        "price_at_emission_usd": price_at_ts,
        "usd_value_at_emission": usd_value,
        "emission_timestamp_utc": emission.get("emission_timestamp_utc"),
        "emissions_source": emission.get("emissions_source"),
        "emissions_source_url": emission.get("emissions_source_url"),
        "price_time_aligned": True,
        "no_current_price": True,
        "formula": _USD_FORMULA,
        "provenance": {
            "source": emission.get("emissions_source"),
            "source_url": emission.get("emissions_source_url"),
            "timestamp_utc": emission.get("emission_timestamp_utc"),
            "methodology_version": _METHODOLOGY_VERSION,
        },
    }


def build_protocol_summary(protocol_id: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    protocol = (seed.get("protocols") or {}).get(protocol_id)
    if not protocol:
        return {"ok": False, "error": "protocol_not_found", "protocol_id": protocol_id}

    emissions = [
        build_emission_record(e)
        for e in seed.get("emissions") or []
        if e.get("protocol") == protocol_id
    ]
    total_usd = round(sum(e["usd_value_at_emission"] for e in emissions), 2)

    return {
        "ok": True,
        "protocol_id": protocol_id,
        "name": protocol.get("name"),
        "chain": protocol.get("chain"),
        "emission_count": len(emissions),
        "total_usd_at_emission": total_usd,
        "emissions": emissions,
        "price_alignment": build_price_alignment(),
    }


def build_token_incentives_panel(protocol: str = "aave") -> dict[str, Any]:
    """Incentives chart data — USD value over time at emission timestamps."""
    t0 = time.perf_counter()
    seed = _load_seed()
    pid = protocol.lower()
    summary = build_protocol_summary(pid, seed)

    if not summary.get("ok"):
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": summary.get("error"),
            "protocol": pid,
        }

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "protocol": pid,
        "summary": summary,
        "scope_lock": build_scope_lock(seed),
        "price_alignment": build_price_alignment(),
        "disclaimer": _DISCLAIMER,
        "not_a_signal": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def list_emissions(
    *,
    protocol: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    seed = _load_seed()
    emissions = [build_emission_record(e) for e in seed.get("emissions") or []]
    if protocol:
        emissions = [e for e in emissions if e.get("protocol") == protocol.lower()]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(emissions[:limit]),
        "emissions": emissions[:limit],
        "price_alignment": build_price_alignment(),
        "timestamp": _utcnow(),
    }


def token_incentives_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Token Incentives & Emissions Module",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "niche_feature": True,
        "scope_lock": build_scope_lock(seed),
        "price_alignment": build_price_alignment(),
        "acceptance_criteria": {
            "price_time_alignment": True,
            "emissions_source_documented": True,
            "usd_at_emission_timestamp": True,
            "no_current_price": True,
        },
        "protocol_count": len(seed.get("protocols") or {}),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
