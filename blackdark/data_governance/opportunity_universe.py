"""Opportunity Universe Contracts — DSR-010, D-08."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from blackdark.data_governance._paths import OPPORTUNITY_UNIVERSE_PATH, ensure_governance_dirs

DEFAULT_UNIVERSES = {
    "squeeze_detection_v1": {
        "universe_id": "squeeze_detection_v1",
        "event_type": "squeeze",
        "eligibility_window": "24h",
        "detection_rule": "funding_oi_volatility_composite",
        "ground_truth": "market_event_library.squeeze_confirmed",
        "exclusions": ["low_liquidity_symbols"],
        "denominator_required": True,
    },
    "oracle_direction_v1": {
        "universe_id": "oracle_direction_v1",
        "event_type": "directional_move",
        "eligibility_window": "4h",
        "detection_rule": "oracle_emitted_predictions",
        "ground_truth": "forward_price_move_at_horizon",
        "exclusions": ["historical_seed", "simulated"],
        "denominator_required": True,
        "includes_abstentions": True,
        "includes_misses": True,
    },
}


def ensure_opportunity_universes() -> dict[str, Any]:
    ensure_governance_dirs()
    if not OPPORTUNITY_UNIVERSE_PATH.exists():
        payload = {
            "registry_version": "1.0.0",
            "universes": DEFAULT_UNIVERSES,
            "registered_at": datetime.now(UTC).isoformat(),
        }
        OPPORTUNITY_UNIVERSE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return json.loads(OPPORTUNITY_UNIVERSE_PATH.read_text(encoding="utf-8"))
