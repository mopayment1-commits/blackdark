"""Load and expose the authoritative capability provenance contract."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "capability" / "CAPABILITY_PROVENANCE_CONTRACT.json"
LEGACY_AMBIGUOUS_CLASS = "LEGACY_AMBIGUOUS_PRE_B1_R"
VERIFICATION_BOUND_CLASS = "VERIFICATION_BOUND"
ARTIFACT_GENERATION_STAMP_CLASS = "ARTIFACT_GENERATION_STAMP"

INCOMPLETE_VERDICTS = frozenset({"UNKNOWN", "FUNCTIONALLY_INCOMPLETE"})


@lru_cache(maxsize=1)
def load_contract() -> dict[str, Any]:
    data = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if data.get("artifact") != "CAPABILITY_PROVENANCE_CONTRACT":
        raise ValueError("invalid capability provenance contract artifact")
    return data


def contract_version() -> str:
    return str(load_contract()["contract_version"])


CONTRACT_VERSION = contract_version()
