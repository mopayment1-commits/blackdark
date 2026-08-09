"""
BLACKDARK — Public Miss Feed (Brand radical: start with the miss).

Chronological public stream of incorrect/partial Oracle outcomes first.
Turns honesty into the brand — competitors bury misses; we lead with them.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote


async def build_public_miss_feed(*, limit: int = 40) -> dict[str, Any]:
    from database import fetch_labeled_oracle_predictions
    from kill_rate_board import build_kill_rate_board

    rows = await fetch_labeled_oracle_predictions(limit=1200, include_synthetic=False)
    misses = [
        r
        for r in (rows or [])
        if str(r.get("label") or "").lower() in {"incorrect", "partial", "miss", "wrong"}
    ]
    misses.sort(
        key=lambda r: str(r.get("timestamp") or r.get("created_at") or r.get("resolved_at") or ""),
        reverse=True,
    )

    items = []
    for r in misses[:limit]:
        pid = r.get("id") or r.get("prediction_id")
        asset = str(r.get("asset") or r.get("symbol") or "—").upper()
        verdict = str(r.get("verdict") or r.get("action") or "—")
        label = str(r.get("label") or "incorrect")
        ts = str(r.get("timestamp") or r.get("created_at") or r.get("resolved_at") or "")
        lesson = (
            "Contradiction / regime shift after seal"
            if label == "partial"
            else "Direction missed — published, not buried"
        )
        items.append(
            {
                "prediction_id": pid,
                "asset": asset,
                "verdict": verdict,
                "label": label,
                "score": r.get("opportunity_score") or r.get("score"),
                "timestamp": ts,
                "lesson": lesson,
                "verify_href": "/oracle-accuracy#losing",
                "share_line": (
                    f"BLACKDARK Miss Feed · {asset} · we said {verdict} · labeled {label}. "
                    f"We lead with misses. Verify: /miss-feed"
                ),
            }
        )

    kills = build_kill_rate_board()
    share = (
        f"BLACKDARK Public Miss Feed · {len(items)} recent misses published first · "
        f"Kill-Rate {kills['metrics'].get('kill_rate_percent', 0)}% · "
        f"We don't hide errors. /miss-feed · Not financial advice"
    )

    return {
        "surface": "public_miss_feed",
        "generated_at": datetime.now(UTC).isoformat(),
        "headline": "We start with the miss",
        "thesis": (
            "Brand is not logos — it is the courage to publish failure first. "
            "No major competitor leads their public surface with a miss stream."
        ),
        "count": len(items),
        "total_misses_in_window": len(misses),
        "items": items,
        "kill_rate_percent": kills["metrics"].get("kill_rate_percent", 0),
        "share_text": share,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(share)}",
            "whatsapp": f"https://wa.me/?text={quote(share)}",
        },
        "page": "/miss-feed",
        "api": "/api/public/miss-feed",
        "related": ["/oracle-accuracy#losing", "/kill-rate", "/api/glass-box/challenge"],
        "brand_role": "radical_fix_of_newer_brand_via_proof_honesty",
        "disclaimer": "Educational transparency — not financial advice. Past misses ≠ future results.",
    }
