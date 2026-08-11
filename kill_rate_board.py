"""
BLACKDARK — Public Kill-Rate Board (U2).

Public board of how often we REJECT signals (Net-Edge Truth + Contradiction Veto
+ Half-Life kill). We brag about refusal — not noise.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from path_safety import ensure_under, safe_data_file
import logging

logger = logging.getLogger(__name__)

_DATA = safe_data_file("kill_rate_events.jsonl")
_DATA_BASE = Path(__file__).resolve().parent / "data"
_MAX_LINES = 5000


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def record_kill(source: str, reason: str, *, meta: dict[str, Any] | None = None) -> None:
    """Append a kill/reject event (best-effort durable)."""
    row = {
        "ts": _utcnow(),
        "source": str(source or "unknown"),
        "reason": str(reason or "unspecified"),
        "meta": meta or {},
    }
    try:
        path = ensure_under(_DATA, _DATA_BASE)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:  # NOSONAR pythonsecurity:S2083
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        # trim
        if path.stat().st_size > 2_000_000:
            lines = path.read_text(encoding="utf-8").splitlines()[-_MAX_LINES:]
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")  # NOSONAR pythonsecurity:S2083
    except OSError:
        logger.debug("persist skipped", exc_info=True)


def _load_events(limit: int = 2000) -> list[dict[str, Any]]:
    if not _DATA.exists():
        return []
    try:
        lines = _DATA.read_text(encoding="utf-8").splitlines()[-limit:]
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            logger.debug("json parse skipped", exc_info=True)
            continue
    return out


def build_kill_rate_board() -> dict[str, Any]:
    from net_edge_truth import net_edge_truth_status

    truth = net_edge_truth_status()
    evaluated = int(truth.get("evaluated") or 0)
    rejected = int(truth.get("rejected") or 0)
    passed = int(truth.get("passed") or 0)

    events = _load_events()
    by_source: dict[str, int] = {}
    by_reason: dict[str, int] = {}
    for ev in events:
        src = str(ev.get("source") or "unknown")
        reason = str(ev.get("reason") or "unspecified")
        by_source[src] = by_source.get(src, 0) + 1
        by_reason[reason] = by_reason.get(reason, 0) + 1

    # Process stats are authoritative for Truth; event log enriches veto/half-life
    veto_kills = int(by_source.get("contradiction_veto", 0))
    hl_kills = int(by_source.get("half_life", 0))
    truth_kills = rejected + int(by_source.get("net_edge_truth", 0))
    total_kills = truth_kills + veto_kills + hl_kills
    total_considered = max(evaluated, passed + rejected, total_kills)

    kill_rate = round(total_kills / total_considered, 4) if total_considered else 0.0
    truth_reject_rate = float(truth.get("reject_rate") or 0.0)

    headline = (
        f"We killed {total_kills} weak signals"
        if total_kills
        else "Kill board armed — rejections publish as the engine runs"
    )

    return {
        "surface": "public_kill_rate_board",
        "generated_at": _utcnow(),
        "headline": headline,
        "thesis": (
            "Most platforms brag about how many alerts they fire. "
            "BLACKDARK publishes how often we refuse — Net-Edge Truth, "
            "Contradiction Veto, and Half-Life kill."
        ),
        "metrics": {
            "kill_rate": kill_rate,
            "kill_rate_percent": round(kill_rate * 100, 2),
            "total_kills": total_kills,
            "total_considered": total_considered,
            "net_edge_reject_rate": truth_reject_rate,
            "net_edge_rejected": rejected,
            "net_edge_passed": passed,
            "net_edge_evaluated": evaluated,
            "contradiction_veto_kills": veto_kills,
            "half_life_kills": hl_kills,
        },
        "reject_reasons": {
            **dict(truth.get("reject_reasons") or {}),
            **by_reason,
        },
        "by_source": by_source,
        "recent_kills": list(reversed(events[-25:])),
        "share_line": (
            f"BLACKDARK Kill-Rate {round(kill_rate * 100, 1)}% — "
            f"we refuse weak edges in public. Verify: /kill-rate"
        ),
        "verify_url": "/kill-rate",
        "api": "/api/public/kill-rate",
        "disclaimer": "Analytical transparency — not financial advice. Refusal ≠ guaranteed profit.",
    }
