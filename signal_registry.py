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

# Type-level lexicon — definition / default source / default weight (D8 moat schema)
SIGNAL_TYPE_LEXICON: dict[str, dict[str, Any]] = {
    "oracle_direction": {
        "definition": "Primary Oracle directional decision after Truth + Veto + Half-Life gates",
        "source": "unified_multimodal_v1",
        "weight": 1.0,
    },
    "oracle_decision": {
        "definition": "Evaluated opportunity verdict packaged for audit / accuracy ledger",
        "source": "ai_oracle.evaluate_opportunity",
        "weight": 1.0,
    },
    "cross_exchange": {
        "definition": "Cross-venue spot price discrepancy surviving Net-Edge truth gates",
        "source": "arbitrage_engine.cross_exchange",
        "weight": 0.9,
    },
    "triangular": {
        "definition": "Triangular arb cycle across three pairs on one or more venues",
        "source": "arbitrage_engine.triangular",
        "weight": 0.85,
    },
    "spot_futures": {
        "definition": "Spot–perpetual basis / cash-and-carry style edge",
        "source": "arbitrage_engine.spot_futures",
        "weight": 0.8,
    },
    "funding": {
        "definition": "Funding-rate differential opportunity across venues",
        "source": "arbitrage_engine.funding",
        "weight": 0.75,
    },
    "arbitrage": {
        "definition": "Cross-venue or triangular arb opportunity surviving Net-Edge truth",
        "source": "scan_coordinator",
        "weight": 0.85,
    },
    "whale_transfer": {
        "definition": "On-chain whale transfer classified Signal vs Noise",
        "source": "whale_signal_classifier",
        "weight": 0.55,
    },
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _features_hash(features: dict[str, Any] | None) -> str:
    payload = json.dumps(features or {}, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _lexicon_for(signal_type: str) -> dict[str, Any]:
    return dict(SIGNAL_TYPE_LEXICON.get(str(signal_type), {
        "definition": "Unregistered signal type — treat as experimental until lexicon entry exists",
        "source": "unknown",
        "weight": 0.25,
    }))


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
    definition: str | None = None,
    source: str | None = None,
    weight: float | None = None,
) -> dict[str, Any]:
    """Register a sovereign signal record and optionally append to JSONL."""
    lex = _lexicon_for(signal_type)
    sid = str(prediction_id) if prediction_id not in (None, "", 0) else f"sig_{uuid4().hex[:16]}"
    record = {
        "signal_id": sid,
        "prediction_id": str(prediction_id) if prediction_id not in (None, "", 0) else None,
        "signal_type": str(signal_type),
        "asset": str(asset).upper(),
        "asof": asof or _utcnow(),
        "features_hash": _features_hash(features),
        "score": None if score is None else round(float(score), 4),
        "verdict": verdict,
        "horizon_seconds": horizon_seconds,
        "label": label or "pending",  # pending | correct | incorrect | expired | vetoed
        "definition": definition or lex.get("definition"),
        "source": source or lex.get("source"),
        "weight": float(weight if weight is not None else lex.get("weight") or 0.5),
        "performance": {"hits": 0, "misses": 0, "pending": 1, "hit_rate": None},
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
        row = _SIGNALS.get(str(signal_id))
        if not row:
            # Try hydrate lookup by prediction_id / signal_id from disk once
            _hydrate_unlocked()
            row = _SIGNALS.get(str(signal_id))
        if not row:
            # Secondary key: prediction_id field match
            for sid, candidate in _SIGNALS.items():
                if str(candidate.get("prediction_id") or "") == str(signal_id):
                    row = candidate
                    signal_id = sid
                    break
        if not row:
            return None
        row = dict(row)
        row["label"] = label
        row["updated_at"] = _utcnow()
        if meta:
            row["resolution"] = meta
        perf = dict(row.get("performance") or {})
        lab = str(label).lower()
        if lab in {"correct", "win", "hit"}:
            perf["hits"] = int(perf.get("hits") or 0) + 1
            perf["pending"] = max(0, int(perf.get("pending") or 1) - 1)
        elif lab in {"incorrect", "loss", "miss", "partial"}:
            perf["misses"] = int(perf.get("misses") or 0) + 1
            perf["pending"] = max(0, int(perf.get("pending") or 1) - 1)
        decided = int(perf.get("hits") or 0) + int(perf.get("misses") or 0)
        perf["hit_rate"] = round(int(perf.get("hits") or 0) / decided, 4) if decided else None
        row["performance"] = perf
        _SIGNALS[str(signal_id)] = row
        _rewrite_jsonl_unlocked()
        return dict(row)


def attach_prediction_id(signal_id: str, prediction_id: str | int) -> dict[str, Any] | None:
    """Link an audit prediction_id onto an existing registry row (D8 close-loop)."""
    pid = str(prediction_id)
    with _LOCK:
        if not _SIGNALS:
            _hydrate_unlocked()
        row = _SIGNALS.get(str(signal_id))
        if not row:
            for sid, candidate in _SIGNALS.items():
                if str(candidate.get("signal_id") or "") == str(signal_id):
                    row = candidate
                    signal_id = sid
                    break
        if not row:
            return None
        row = dict(row)
        old_sid = str(row.get("signal_id") or signal_id)
        row["prediction_id"] = pid
        # Prefer prediction_id as canonical key when available
        row["signal_id"] = pid
        row["updated_at"] = _utcnow()
        prov = dict(row.get("provenance") or {})
        prov["prediction_id"] = pid
        row["provenance"] = prov
        if old_sid != pid and old_sid in _SIGNALS:
            _SIGNALS.pop(old_sid, None)
        _SIGNALS[pid] = row
        _rewrite_jsonl_unlocked()
        return dict(row)


def _hydrate_unlocked() -> int:
    """Load JSONL into memory if empty or sparse (boot / after restart)."""
    if not _PATH.exists():
        return 0
    loaded = 0
    try:
        for line in _PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            sid = str(row.get("signal_id") or "")
            if not sid:
                continue
            # Prefer newer updated_at if duplicate
            existing = _SIGNALS.get(sid)
            if existing and str(existing.get("updated_at") or "") >= str(row.get("updated_at") or ""):
                continue
            _SIGNALS[sid] = row
            loaded += 1
        while len(_SIGNALS) > _MAX_MEMORY:
            oldest = next(iter(_SIGNALS))
            _SIGNALS.pop(oldest, None)
    except Exception:
        logger.debug("signal registry hydrate failed", exc_info=True)
    return loaded


def hydrate_signal_registry() -> dict[str, Any]:
    with _LOCK:
        n = _hydrate_unlocked()
        return {"hydrated": n, "total_in_memory": len(_SIGNALS), "path": str(_PATH)}


def _rewrite_jsonl_unlocked() -> None:
    """Persist full in-memory registry (labels survive restart)."""
    try:
        _PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = _PATH.with_suffix(".jsonl.tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            for row in _SIGNALS.values():
                fh.write(json.dumps(row, separators=(",", ":"), default=str) + "\n")
        tmp.replace(_PATH)
    except Exception:
        logger.debug("signal registry rewrite failed", exc_info=True)


def get_signal(signal_id: str) -> dict[str, Any] | None:
    with _LOCK:
        if not _SIGNALS:
            _hydrate_unlocked()
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
        if not _SIGNALS:
            _hydrate_unlocked()
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
        if not _SIGNALS:
            _hydrate_unlocked()
        rows = list(_SIGNALS.values())
    by_type: dict[str, int] = {}
    by_label: dict[str, int] = {}
    by_type_perf: dict[str, dict[str, Any]] = {}
    linked = 0
    for row in rows:
        st = str(row.get("signal_type") or "unknown")
        by_type[st] = by_type.get(st, 0) + 1
        lab = str(row.get("label") or "pending")
        by_label[lab] = by_label.get(lab, 0) + 1
        if row.get("prediction_id"):
            linked += 1
        bucket = by_type_perf.setdefault(st, {"hits": 0, "misses": 0, "pending": 0, "hit_rate": None})
        if lab in {"correct", "win", "hit"}:
            bucket["hits"] += 1
        elif lab in {"incorrect", "loss", "miss", "partial"}:
            bucket["misses"] += 1
        else:
            bucket["pending"] += 1
    for st, bucket in by_type_perf.items():
        decided = bucket["hits"] + bucket["misses"]
        bucket["hit_rate"] = round(bucket["hits"] / decided, 4) if decided else None
        lex = _lexicon_for(st)
        bucket["definition"] = lex.get("definition")
        bucket["weight"] = lex.get("weight")
        bucket["source"] = lex.get("source")
    labeled = sum(1 for r in rows if r.get("label") and r.get("label") not in {"pending", None, ""})
    if labeled > 0 and linked > 0:
        status = "live"
    elif len(rows) > 0:
        status = "pending_labels" if labeled == 0 else "partial"
    else:
        status = "empty"
    return {
        "total_in_memory": len(rows),
        "labeled": labeled,
        "unlabeled": len(rows) - labeled,
        "linked_prediction_ids": linked,
        "by_type": by_type,
        "by_label": by_label,
        "by_type_performance": by_type_perf,
        "lexicon": SIGNAL_TYPE_LEXICON,
        "status": status,
        "persist_path": str(_PATH),
        "moat_claim": "sovereign_labeled_signal_lexicon",
        "generated_at": _utcnow(),
        "uptime_seconds": round(time.time() - _BOOT, 1),
    }


_BOOT = time.time()

# Boot hydrate so labels/stats survive process restart
try:
    hydrate_signal_registry()
except Exception:
    pass


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
    pred_id = evaluated.get("prediction_id") or payload.get("prediction_id")
    stype = str(evaluated.get("kind") or payload.get("kind") or "oracle_decision")
    return register_signal(
        signal_type=stype,
        asset=str(evaluated.get("asset") or "BTC"),
        features=features,
        score=float(evaluated.get("opportunity_score") or 0),
        verdict=str((evaluated.get("oracle") or {}).get("verdict") or evaluated.get("verdict") or ""),
        horizon_seconds=int((payload.get("opportunity_half_life") or {}).get("expected_half_life_seconds") or 45),
        provenance={
            "engine": payload.get("unified_engine") or "unified_multimodal_v1",
            "public_verdict": payload.get("public_verdict"),
            "proof_hint": "oracle_audit_chain",
            "prediction_id": pred_id,
        },
        prediction_id=str(pred_id) if pred_id not in (None, "", 0) else None,
        label=label,
    )


async def backfill_labels_from_oracle(*, limit: int = 2000) -> dict[str, Any]:
    """Close D8 moat gap: label pending registry rows from resolved oracle predictions."""
    try:
        from database import fetch_labeled_oracle_predictions
    except Exception as exc:
        return {"ok": False, "reason": str(exc)[:160]}

    rows = await fetch_labeled_oracle_predictions(limit=limit, include_synthetic=False)
    linked = 0
    labeled = 0
    registered = 0
    for pred in rows or []:
        pred_id = pred.get("id") or pred.get("prediction_id")
        outcome = str(pred.get("label") or pred.get("outcome") or "").lower().strip()
        if not pred_id or outcome not in {"correct", "incorrect", "partial", "win", "loss", "miss"}:
            continue
        # Prefer exact prediction_id match
        hit = resolve_signal(
            str(pred_id),
            outcome,
            meta={
                "accuracy": pred.get("accuracy_score"),
                "direction_label": pred.get("direction_label"),
                "resolved_via": "oracle_backfill",
                "asset": pred.get("asset"),
            },
        )
        if hit:
            linked += 1
            labeled += 1
            continue
        # No registry row yet — register a labeled historical row (moat growth)
        register_signal(
            signal_type=str(pred.get("kind") or "oracle_direction"),
            asset=str(pred.get("asset") or "BTC"),
            features={
                "opportunity_score": pred.get("opportunity_score"),
                "market_regime": pred.get("market_regime"),
                "confidence": pred.get("confidence"),
            },
            score=float(pred.get("opportunity_score") or 0) if pred.get("opportunity_score") is not None else None,
            verdict=str(pred.get("verdict") or ""),
            prediction_id=str(pred_id),
            label=outcome,
            asof=str(pred.get("timestamp") or _utcnow()),
            provenance={"source": "oracle_backfill", "prediction_id": pred_id},
        )
        registered += 1
        labeled += 1
    stats = registry_stats()
    return {
        "ok": True,
        "scanned": len(rows or []),
        "linked_existing": linked,
        "registered_labeled": registered,
        "labeled_total_touch": labeled,
        "registry": {
            "labeled": stats.get("labeled"),
            "unlabeled": stats.get("unlabeled"),
            "status": stats.get("status"),
        },
    }
