"""Public Changed-Mind Record — sealed view revisions, not misses.

A miss is 'we were wrong after the horizon'. A changed mind is 'we published
a later sealed view that is not the same bucket as the previous sealed view
on the same asset'. Derived from the immutable audit chain. Never invented.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

from regulatory_compliance_guard import classify_internal_verdict, to_public_verdict


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _read_created_records(*, include_synthetic: bool) -> list[dict[str, Any]]:
    from oracle_audit_chain import chain_path
    from oracle_integrity import is_synthetic_prediction

    path = chain_path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("event") != "prediction_created":
                continue
            if not include_synthetic and is_synthetic_prediction(rec):
                continue
            rows.append(rec)
    return rows


def _reason(prev_bucket: str, next_bucket: str) -> str:
    if next_bucket == "unknown":
        return "view withdrawn — I DON'T KNOW (conflict or insufficient evidence)"
    if prev_bucket == "unknown":
        return "view formed after a published I DON'T KNOW"
    return "sealed view revised"


def build_changed_mind_record(*, limit: int = 40, include_synthetic: bool = False) -> dict[str, Any]:
    limit = max(1, min(int(limit), 100))
    created = _read_created_records(include_synthetic=include_synthetic)
    by_asset: dict[str, list[dict[str, Any]]] = {}
    for rec in created:
        asset = str(rec.get("asset") or rec.get("symbol") or "").upper() or "—"
        by_asset.setdefault(asset, []).append(rec)

    flips: list[dict[str, Any]] = []
    for asset, rows in by_asset.items():
        rows.sort(key=lambda r: str(r.get("timestamp") or r.get("proved_at") or ""))
        for prev, cur in zip(rows, rows[1:]):
            prev_v = str(prev.get("verdict") or "")
            cur_v = str(cur.get("verdict") or "")
            b0 = classify_internal_verdict(prev_v)
            b1 = classify_internal_verdict(cur_v)
            if b0 == b1:
                continue
            flips.append(
                {
                    "asset": asset,
                    "from_verdict": to_public_verdict(prev_v) if prev_v else prev_v,
                    "to_verdict": to_public_verdict(cur_v) if cur_v else cur_v,
                    "from_bucket": b0,
                    "to_bucket": b1,
                    "from_prediction_id": prev.get("prediction_id"),
                    "to_prediction_id": cur.get("prediction_id"),
                    "from_timestamp": prev.get("timestamp"),
                    "to_timestamp": cur.get("timestamp"),
                    "from_chain_hash": prev.get("chain_hash"),
                    "to_chain_hash": cur.get("chain_hash"),
                    "reason": _reason(b0, b1),
                    "verify_href": "/oracle-accuracy#audit-challenge",
                }
            )

    flips.sort(key=lambda r: str(r.get("to_timestamp") or ""), reverse=True)
    items = flips[:limit]
    share = (
        f"BLACKDARK Changed-Mind Record · {len(items)} sealed view revisions published · "
        f"We show when the view changed, not only when it missed. /changed-mind · Not financial advice"
    )
    return {
        "surface": "public_changed_mind_record",
        "generated_at": _utcnow(),
        "headline": "We publish when the view changes",
        "thesis": (
            "A miss is an outcome. A changed mind is a later sealed view that is not "
            "the same bucket as the previous sealed view on the same asset. "
            "Derived from the immutable audit chain — never invented."
        ),
        "count": len(items),
        "total_flips_in_window": len(flips),
        "created_events_scanned": len(created),
        "include_synthetic": include_synthetic,
        "items": items,
        "share_text": share,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(share)}",
            "whatsapp": f"https://wa.me/?text={quote(share)}",
        },
        "page": "/changed-mind",
        "api": "/api/public/changed-mind",
        "related": ["/miss-feed", "/oracle-accuracy", "/contradiction-replay"],
        "empty_honest": (
            "No sealed view changes in the live chain yet. Absence is published, not hidden."
            if not items
            else None
        ),
        "disclaimer": "Educational transparency — not financial advice. A revision is not a profit claim.",
        "product_complete": False,
    }
