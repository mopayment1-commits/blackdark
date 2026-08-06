"""
BLACKDARK — Glass Box Challenge ready pack (launch narrative).

Not a seventh product surface: packaging for Locked Predictions + Public Ledger
+ Decision Certificates. Timing/channel remain human LAUNCH_ONLY decisions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_glass_box_challenge_pack() -> dict[str, Any]:
    from locked_predictions import glass_box_status, list_locked_predictions

    locked = glass_box_status()
    recent = list_locked_predictions(limit=5)
    challenge_en = (
        "BLACKDARK Glass Box Challenge: We are the first crypto intelligence platform "
        "to publish our full accuracy ledger — including misses — permanently and verifiably. "
        "We challenge every competitor to publish theirs. Labels are not proof. Prove it."
    )
    hook = (
        "Before the next major macro event we seal a timed Decision Certificate in public. "
        "After the event we unlock it live — wins and losses."
    )
    story = (
        "Competitors sell Smart Money labels. Independent reviews show those labels fail. "
        "Nobody publishes a full public audited hit-rate. We do — including the losing trades."
    )
    loop = (
        "Every Decision Certificate is shareable and timestamp-sealed. "
        "Every share is proof-first distribution (Hook–Story–Loop)."
    )
    return {
        "name": "The Glass Box Challenge",
        "status": "ready_pack",
        "launch_only_fields": ["exact_datetime", "announcement_channel"],
        "hook": hook,
        "story": story,
        "loop": loop,
        "challenge_text_en": challenge_en,
        "product_surfaces": {
            "locked_predictions": "/oracle-accuracy#locked",
            "public_accuracy_ledger": "/oracle-accuracy",
            "monthly_losing_report": "/oracle-accuracy#losing",
            "audit_challenge": "/oracle-accuracy#audit-challenge",
            "decision_certificate_api": "/api/oracle/decision-certificate",
        },
        "locked_predictions_status": locked,
        "recent_locked": recent,
        "share_text": challenge_en,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Product machinery is live. Press the challenge when you choose the event clock.",
    }
