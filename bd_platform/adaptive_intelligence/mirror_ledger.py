"""Mirror Ledger foundations — spec §28 (consent/privacy; not financial ground truth)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_LEDGER = Path("data/mirror_ledger.jsonl")


def record_user_decision(
    *,
    user_id: str,
    decision_ref: str,
    user_stance: str,
    blackdark_stance: str | None = None,
    consent: bool = True,
) -> dict[str, Any]:
    if not consent:
        raise ValueError("mirror_ledger_requires_consent")
    row = {
        "user_id": user_id,
        "decision_ref": decision_ref,
        "user_stance": user_stance,
        "blackdark_stance": blackdark_stance,
        "consent": True,
        "financial_ground_truth": False,
        "recorded_at": time.time(),
    }
    _LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with _LEDGER.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return row
