"""
BLACKDARK — Sovereign Signal Registry (Differentiator D8).

Owns a labeled lexicon of signals:
  signal_type · asof · features_hash · prediction_id · label · provenance

This is the acquisition asset: a non-replicable named corpus, not a chart UI.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import config

logger = logging.getLogger("BLACKDARK.SignalRegistry")

_LOCK = threading.Lock()
_SIGNALS: dict[str, dict[str, Any]] = {}
_MAX_MEMORY = int(getattr(config, "SIGNAL_REGISTRY_MAX_MEMORY", 2000))
_PATH = Path(getattr(config, "SIGNAL_REGISTRY_PATH", "data/signal_registry.jsonl"))


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _features_hash(features: dict[str, Any] | None) -> str:
    payload = json.dumps(features or {}, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def register_signal(
    *,
    signal_type: str,
    asset: str,
    features: dict[str, Any] | None = None,
    score: float | None = None,
    verdict: str | None = None,
    horizon_seconds: int | None = None,
    provenance: dict[str, Any] | None = None,
    prediction_id: str | None = None,
    label: str | None = None,
    asof: str | None = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Register a sovereign signal record and optionally append to JSONL."""
    sid = prediction_id or f"sig_{uuid4().hex[:16]}"
    record = {
        "signal_id": sid,
        "signal_type": str(signal_type),
        "asset": str(asset).upper(),
        "asof": asof or _utcnow(),
        "features_hash": _features_hash(features),
        "score": None if score is None else round(float(score), 4),
        "verdict": verdict,
        "horizon_seconds": horizon_seconds,
        "label": label,  # pending | correct | incorrect | expired | vetoed
        "provenance": provenance or {},
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    with _LOCK:
        _SIGNALS[sid] = record
        while len(_SIGNALS) > _MAX_MEMORY:
            oldest = next(iter(_SIGNALS))
            _SIGNALS.pop(oldest, None)
        if persist:
            try:
                _PATH.parent.mkdir(parents=True, exist_ok=True)
                with _PATH.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record, separators=(",", ":"), default=str) + "\n")
            except Exception:
                logger.debug("signal registry persist failed", exc_info=True)
    return dict(record)


def resolve_signal(signal_id: str, label: str, *, meta: dict[str, Any] | None = None) -> dict[str, Any] | None:
    with _LOCK:
        row = _SIGNALS.get(signal_id)
        if not row:
            return None
        row = dict(row)
        row["label"] = label
        row["updated_at"] = _utcnow()
        if meta:
            row["resolution"] = meta
        _SIGNALS[signal_id] = row
        return dict(row)


def get_signal(signal_id: str) -> dict[str, Any] | None:
    with _LOCK:
        row = _SIGNALS.get(signal_id)
        return dict(row) if row else None


def list_signals(
    *,
    limit: int = 50,
    signal_type: str | None = None,
    asset: str | None = None,
    unlabeled_only: bool = False,
) -> list[dict[str, Any]]:
    with _LOCK:
        rows = list(_SIGNALS.values())
    if signal_type:
        rows = [r for r in rows if r.get("signal_type") == signal_type]
    if asset:
        asset_u = asset.upper()
        rows = [r for r in rows if str(r.get("asset") or "").upper() == asset_u]
    if unlabeled_only:
        rows = [r for r in rows if not r.get("label") or r.get("label") == "pending"]
    rows.sort(key=lambda r: str(r.get("asof") or ""), reverse=True)
    return rows[: max(1, min(limit, 500))]


def registry_stats() -> dict[str, Any]:
    with _LOCK:
        rows = list(_SIGNALS.values())
    by_type: dict[str, int] = {}
    by_label: dict[str, int] = {}
    for row in rows:
        st = str(row.get("signal_type") or "unknown")
        by_type[st] = by_type.get(st, 0) + 1
        lab = str(row.get("label") or "pending")
        by_label[lab] = by_label.get(lab, 0) + 1
    labeled = sum(1 for r in rows if r.get("label") and r.get("label") != "pending")
    return {
        "total_in_memory": len(rows),
        "labeled": labeled,
        "unlabeled": len(rows) - labeled,
        "by_type": by_type,
        "by_label": by_label,
        "persist_path": str(_PATH),
        "moat_claim": "sovereign_labeled_signal_lexicon",
        "generated_at": _utcnow(),
        "uptime_seconds": round(time.time() - _BOOT, 1),
    }


_BOOT = time.time()


def register_from_evaluation(evaluated: dict[str, Any]) -> dict[str, Any]:
    """Convenience: persist Oracle/arb evaluation as a registry row."""
    payload = evaluated.get("payload") or {}
    features = {
        "opportunity_score": evaluated.get("opportunity_score"),
        "net_profit_usdt": evaluated.get("net_profit_usdt"),
        "market_regime": payload.get("market_regime"),
        "truth_score": (payload.get("net_edge_truth") or {}).get("truth_score"),
        "half_life_seconds": (payload.get("opportunity_half_life") or {}).get("expected_half_life_seconds"),
        "dimension_conflict": bool((payload.get("dimension_conflict") or {}).get("veto")),
    }
    label = "pending"
    if (payload.get("dimension_conflict") or {}).get("veto"):
        label = "vetoed"
    elif (payload.get("net_edge_truth") or {}).get("reject"):
        label = "rejected_net_edge"
    return register_signal(
        signal_type=str(evaluated.get("kind") or payload.get("kind") or "oracle_decision"),
        asset=str(evaluated.get("asset") or "BTC"),
        features=features,
        score=float(evaluated.get("opportunity_score") or 0),
        verdict=str((evaluated.get("oracle") or {}).get("verdict") or evaluated.get("verdict") or ""),
        horizon_seconds=int((payload.get("opportunity_half_life") or {}).get("expected_half_life_seconds") or 45),
        provenance={
            "engine": payload.get("unified_engine") or "unified_multimodal_v1",
            "public_verdict": payload.get("public_verdict"),
            "proof_hint": "oracle_audit_chain",
        },
        label=label,
    )
