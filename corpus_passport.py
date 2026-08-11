"""
BLACKDARK — Corpus Passport for acquirers (U8).

One card proving the labeled flywheel / signal lexicon moat for Data Room & M&A.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from committee_one_pager import build_minimal_pdf


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _registry_stats() -> dict[str, Any]:
    try:
        from signal_registry import registry_stats

        return registry_stats()
    except Exception as exc:
        return {"error": str(exc)}


def _public_accuracy() -> dict[str, Any]:
    try:
        from oracle_track_record import public_track_record

        return public_track_record() or {}
    except Exception as exc:
        return {"error": str(exc)}


def _kill_metrics() -> dict[str, Any]:
    try:
        from kill_rate_board import build_kill_rate_board

        return build_kill_rate_board().get("metrics") or {}
    except Exception as exc:
        return {"error": str(exc)}


def _net_edge_truth() -> dict[str, Any]:
    try:
        from net_edge_truth import net_edge_truth_status

        return net_edge_truth_status()
    except Exception as exc:
        return {"error": str(exc)}


def _flywheel_status() -> dict[str, Any]:
    try:
        from flywheel_saturation_guard import flywheel_saturation_status

        return flywheel_saturation_status()
    except Exception as exc:
        return {"error": str(exc)}


async def _data_moat_status() -> dict[str, Any]:
    try:
        from data_moat_guard import build_moat_build_status

        return await build_moat_build_status()
    except Exception as exc:
        return {"error": str(exc)}


def _passport_stamps(
    *,
    labeled: int,
    unlabeled: int,
    linked: int,
    status: str,
    registry: dict[str, Any],
    accuracy: dict[str, Any],
    kills: dict[str, Any],
    truth: dict[str, Any],
) -> list[str]:
    return [
        f"Labeled signals: {labeled}",
        f"Unlabeled / pending: {unlabeled}",
        f"Linked prediction_ids: {linked}",
        f"Public accuracy samples: {accuracy.get('resolved_count') or accuracy.get('n') or 0}",
        f"Public hit-rate %: {accuracy.get('hit_rate_percent') or accuracy.get('direction_hit_rate_percent') or 0}",
        f"Kill-rate %: {kills.get('kill_rate_percent', 0)}",
        f"Net-Edge reject rate: {truth.get('reject_rate', 0)}",
        f"Registry status: {status}",
        f"Moat claim: {registry.get('moat_claim') or 'sovereign_labeled_signal_lexicon'}",
        "Anti-leakage: temporal validation + labeled flywheel path",
        "Not selling: raw model weights / indicator spam",
    ]


async def build_corpus_passport() -> dict[str, Any]:
    registry = _registry_stats()
    accuracy = _public_accuracy()
    kills = _kill_metrics()
    truth = _net_edge_truth()
    flywheel = _flywheel_status()
    moat = await _data_moat_status()

    labeled = int(registry.get("labeled") or 0)
    unlabeled = int(registry.get("unlabeled") or 0)
    total = int(registry.get("total_in_memory") or (labeled + unlabeled) or 0)
    linked = int(registry.get("linked_prediction_ids") or 0)
    status = str(registry.get("status") or ("live" if labeled else "bootstrapping"))

    stamps = _passport_stamps(
        labeled=labeled,
        unlabeled=unlabeled,
        linked=linked,
        status=status,
        registry=registry,
        accuracy=accuracy,
        kills=kills,
        truth=truth,
    )

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>BLACKDARK Corpus Passport</title>
<style>
body{{font-family:Georgia,serif;max-width:720px;margin:28px auto;padding:0 16px;background:#f6f3ec;color:#111}}
.passport{{border:2px solid #111;padding:24px;background:#fff}}
h1{{margin:0 0 8px;font-size:26px;letter-spacing:.06em}}
.kicker{{text-transform:uppercase;font-size:12px;color:#555;letter-spacing:.08em}}
.stamp{{font-size:34px;font-weight:700;margin:16px 0;color:#0f766e}}
ul{{line-height:1.55}}
.foot{{font-size:11px;color:#666;margin-top:20px}}
@media print{{.noprint{{display:none}}}}
</style></head><body>
<div class="passport">
<p class="kicker">Acquirer · Data Room · Corpus Passport</p>
<h1>BLACKDARK Corpus Passport</h1>
<p class="stamp">{labeled} labeled</p>
<p>Sovereign Signal Registry — the asset a committee buys.</p>
<ul>{''.join(f'<li>{s}</li>' for s in stamps)}</ul>
<p class="foot">Not financial advice. Methodology glass-box — not raw weights. Verify on /oracle-accuracy + /kill-rate.</p>
</div>
<p class="noprint"><a href="/api/due-diligence/corpus-passport.pdf">Download PDF</a> ·
<a href="/b2b">B2B</a> · <a href="/data-room">Data Room</a></p>
</body></html>"""

    return {
        "surface": "corpus_passport",
        "generated_at": _utcnow(),
        "title": "BLACKDARK — Corpus Passport",
        "headline": f"{labeled} labeled signals — sovereign lexicon",
        "metrics": {
            "labeled": labeled,
            "unlabeled": unlabeled,
            "total": total,
            "linked_prediction_ids": linked,
            "registry_status": status,
            "by_type_performance": registry.get("by_type_performance") or {},
            "by_label": registry.get("by_label") or {},
            "accuracy_samples": accuracy.get("resolved_count") or accuracy.get("n") or 0,
            "accuracy_hit_rate_percent": accuracy.get("hit_rate_percent")
            or accuracy.get("direction_hit_rate_percent")
            or 0,
            "kill_rate_percent": kills.get("kill_rate_percent", 0),
            "net_edge_reject_rate": truth.get("reject_rate", 0),
        },
        "stamps": stamps,
        "sections": {
            "signal_registry": registry,
            "accuracy": accuracy,
            "kill_rate": kills,
            "net_edge_truth": truth,
            "flywheel": flywheel,
            "data_moat": moat,
        },
        "html": html,
        "one_liner_for_ic": (
            "Labeled live corpus + public kill-rate + audit chain — "
            "the Data Moat, not a dashboard."
        ),
        "endpoints": {
            "json": "/api/due-diligence/corpus-passport",
            "page": "/corpus-passport",
            "pdf": "/api/due-diligence/corpus-passport.pdf",
            "public_summary": "/api/due-diligence/corpus-passport/public",
        },
        "access": "whale_or_admin_full__public_summary_open",
        "tier_surface": "institutional_desk",
        "disclaimer": "Acquirer diligence artifact — not financial advice. Weights not exported.",
    }


def build_corpus_passport_public() -> dict[str, Any]:
    """Redacted teaser — no proprietary row dumps."""
    try:
        from signal_registry import registry_stats

        reg = registry_stats()
    except Exception:
        reg = {}
    try:
        from kill_rate_board import build_kill_rate_board

        kills = build_kill_rate_board()["metrics"]
    except Exception:
        kills = {}
    return {
        "surface": "corpus_passport_public",
        "generated_at": _utcnow(),
        "headline": "Corpus Passport — labeled signal moat (teaser)",
        "metrics": {
            "labeled": reg.get("labeled", 0),
            "registry_status": reg.get("status"),
            "kill_rate_percent": kills.get("kill_rate_percent", 0),
            "moat_claim": reg.get("moat_claim") or "sovereign_labeled_signal_lexicon",
        },
        "full": "/api/due-diligence/corpus-passport",
        "page": "/corpus-passport",
        "verify": ["/oracle-accuracy", "/kill-rate"],
        "disclaimer": "Public teaser. Full passport on Desk / Institutional session.",
    }


def render_corpus_passport_pdf(passport: dict[str, Any]) -> bytes:
    lines = [str(x) for x in passport.get("stamps") or []]
    lines.insert(0, str(passport.get("headline") or "Corpus Passport"))
    return build_minimal_pdf(lines, title=str(passport.get("title") or "BLACKDARK Corpus Passport"))
