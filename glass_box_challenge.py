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
    event_template = {
        "title": "Glass Box Public Event (operator-scheduled)",
        "steps": [
            "Pick one macro/crypto event window (date + timezone).",
            "Seal ≥3 timed Decision Certificates on /oracle-accuracy#locked before the event.",
            "Publish challenge text + ledger link on X/Telegram (human channel choice).",
            "After resolution, unlock results live — wins and losses — on the Public Accuracy Ledger.",
            "Invite competitors to publish their full ledgers (including misses).",
        ],
        "share_kit": {
            "primary_url": "/oracle-accuracy#glass-box-challenge",
            "challenge_text_en": challenge_en,
            "hashtags": ["#GlassBoxChallenge", "#ProveIt", "#BLACKDARK"],
        },
        "human_only": [
            "exact_datetime",
            "announcement_channel",
            "press_outreach",
        ],
    }
    locked_count = int((locked or {}).get("locked") or 0)
    unlocked_count = int((locked or {}).get("unlocked") or 0)
    operator_runbook = {
        "title": "Glass Box operator runbook (launch packaging)",
        "doc": "docs/GLASS_BOX_OPERATOR_RUNBOOK.md",
        "machine_ready": True,
        "gates": [
            {
                "id": "ledger_live",
                "label": "Public Accuracy Ledger page live",
                "status": "ready",
                "check": "/oracle-accuracy",
            },
            {
                "id": "locked_surface",
                "label": "Locked Predictions Glass Box surface live",
                "status": "ready",
                "check": "/oracle-accuracy#locked",
                "locked_count": locked_count,
                "unlocked_count": unlocked_count,
            },
            {
                "id": "challenge_api",
                "label": "Challenge pack API live",
                "status": "ready",
                "check": "/api/glass-box/challenge",
            },
            {
                "id": "seal_before_event",
                "label": "Seal ≥3 certificates before chosen event",
                "status": "operator" if locked_count < 3 else "ready",
                "human": True,
            },
            {
                "id": "announce",
                "label": "Human announce on chosen channel (X/TG/press)",
                "status": "human_only",
                "human": True,
            },
            {
                "id": "unlock_live",
                "label": "Unlock wins and losses live after resolution",
                "status": "operator",
                "human": True,
            },
        ],
        "t_minus_checklist": [
            "T-48h: pick event window + timezone; draft challenge post",
            "T-24h: seal ≥3 Decision Certificates; confirm ledger share kit",
            "T-1h: post Hook + Ledger link; pin Glass Box Challenge section",
            "T+0: do not edit sealed rows; only unlock after resolution",
            "T+resolve: unlock live; publish misses; invite competitor ledgers",
        ],
        "human_only": [
            "exact_datetime",
            "announcement_channel",
            "press_outreach",
            "counsel_review_if_needed",
        ],
    }
    return {
        "name": "The Glass Box Challenge",
        "status": "ready_pack",
        "launch_only_fields": ["exact_datetime", "announcement_channel"],
        "hook": hook,
        "story": story,
        "loop": loop,
        "challenge_text_en": challenge_en,
        "event_template": event_template,
        "operator_runbook": operator_runbook,
        "product_surfaces": {
            "locked_predictions": "/oracle-accuracy#locked",
            "public_accuracy_ledger": "/oracle-accuracy",
            "monthly_losing_report": "/oracle-accuracy#losing",
            "audit_challenge": "/oracle-accuracy#audit-challenge",
            "decision_certificate_api": "/api/oracle/decision-certificate",
            "operator_api": "/api/glass-box/operator",
        },
        "locked_predictions_status": locked,
        "recent_locked": recent,
        "share_text": challenge_en,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Product machinery is live. Use event_template + operator_runbook to run one "
            "public challenge — scheduling and press remain human."
        ),
    }


def build_glass_box_operator_pack() -> dict[str, Any]:
    """Operator-facing subset of the challenge pack (launch packaging only)."""
    pack = build_glass_box_challenge_pack()
    return {
        "name": pack["name"],
        "status": pack["status"],
        "operator_runbook": pack["operator_runbook"],
        "event_template": pack["event_template"],
        "product_surfaces": pack["product_surfaces"],
        "locked_predictions_status": pack["locked_predictions_status"],
        "challenge_text_en": pack["challenge_text_en"],
        "share_text": pack["share_text"],
        "launch_only_fields": pack["launch_only_fields"],
        "note": pack["note"],
        "generated_at": pack["generated_at"],
    }
