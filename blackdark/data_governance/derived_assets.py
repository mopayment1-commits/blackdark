"""Derived asset classification — DSR-019, D-10."""

from __future__ import annotations

import json
from typing import Any

from blackdark.data_governance._paths import DERIVED_ASSETS_PATH, ensure_governance_dirs

CLASSIFICATIONS = ("commodity", "configured", "proprietary", "trade_secret_candidate")


def ensure_derived_classifications() -> dict[str, Any]:
    ensure_governance_dirs()
    if not DERIVED_ASSETS_PATH.exists():
        payload = {
            "assets": {
                "net_edge_truth": {
                    "asset_id": "net_edge_truth",
                    "classification": "proprietary",
                    "owner": "platform-intelligence",
                    "rights_profile_id": "rp_proprietary_internal",
                    "value_evidence": "core_decision_gate",
                },
                "provenance_score": {
                    "asset_id": "provenance_score",
                    "classification": "proprietary",
                    "owner": "platform-trust",
                    "rights_profile_id": "rp_proprietary_internal",
                    "value_evidence": "decision_grade_bands",
                },
                "ohlcv_normalized": {
                    "asset_id": "ohlcv_normalized",
                    "classification": "commodity",
                    "owner": "platform-data",
                    "rights_profile_id": "rp_market_data_derived",
                    "value_evidence": "standard_transform",
                },
            }
        }
        DERIVED_ASSETS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return json.loads(DERIVED_ASSETS_PATH.read_text(encoding="utf-8"))
