"""
BLACKDARK — Six Heroes quality gates (expert polish).

Binding bar from HEROES_STRATEGY_BINDING.md:
  OQS Why <5s · Whale one sentence · Ledger shareable ·
  Portfolio plain language · Single-Sentence Oracle · Certificate exportable.

No seventh product surface. Quiet engines stay quiet.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

# Sonar S1192: duplicated string literals
PATH_DASHBOARD = '/dashboard'


def normalize_top_factors(payload: dict[str, Any] | None) -> list[dict[str, str]]:
    """Normalize Top-3 factors so UI can render Why in <5 seconds."""
    payload = payload or {}
    raw = (
        (payload.get("explanation") or {}).get("top_3_factors")
        or payload.get("top_3_factors")
        or []
    )
    out: list[dict[str, str]] = []
    for item in raw[:3]:
        if isinstance(item, str):
            out.append({"factor": item, "detail": "", "source": "model"})
            continue
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "factor": str(item.get("factor") or item.get("label") or item.get("name") or "Factor"),
                "detail": str(item.get("detail") or item.get("why") or ""),
                "source": str(item.get("source") or "live market"),
                "weight_hint": str(item.get("weight_hint") or ""),
            }
        )
    return out


def build_oqs_why_block(payload: dict[str, Any]) -> dict[str, Any]:
    """Hero #1 — Why this opportunity in <5s (Top-3 + sources)."""
    factors = normalize_top_factors(payload)
    lines = []
    for i, f in enumerate(factors, 1):
        bit = f"{i}. {f['factor']}"
        if f.get("detail"):
            bit += f" — {f['detail']}"
        if f.get("source"):
            bit += f" ({f['source']})"
        lines.append(bit)
    grasp = (
        "Top 3 reasons below — read in under five seconds."
        if factors
        else "Factor breakdown unavailable on this response — score still shown."
    )
    return {
        "hero": "opportunity_score_explainability",
        "acceptance": "why_in_under_5_seconds",
        "grasp_line": grasp,
        "top_3_factors": factors,
        "why_text": "\n".join(lines),
        "ready": len(factors) >= 1,
    }


def build_ledger_share_kit(
    *,
    accuracy_pct: float | None = None,
    total_predictions: int | None = None,
    misses_shown: bool = True,
    origin: str = "https://blackdark.app",
) -> dict[str, Any]:
    """Hero #3 — Public Accuracy Ledger shareability pack."""
    url = f"{origin.rstrip('/')}/oracle-accuracy"
    stats = []
    if accuracy_pct is not None:
        stats.append(f"{accuracy_pct:.1f}% labeled accuracy")
    if total_predictions is not None:
        stats.append(f"{total_predictions} logged decisions")
    stats_bit = (" · " + " · ".join(stats)) if stats else ""
    text = (
        f"BLACKDARK Public Accuracy Ledger{stats_bit}. "
        f"Full ledger including misses. Labels are not proof. Verify: {url}"
    )
    return {
        "hero": "public_accuracy_ledger",
        "url": url,
        "share_text": text,
        "misses_shown": misses_shown,
        "share_urls": {
            "x": f"https://twitter.com/intent/tweet?text={quote(text)}",
            "telegram": f"https://t.me/share/url?url={quote(url)}&text={quote(text)}",
            "whatsapp": f"https://wa.me/?text={quote(text)}",
        },
        "og": {
            "title": "BLACKDARK — Public Oracle Accuracy Ledger",
            "description": "Full public ledger including misses. Glass Box ready. Prove it.",
            "url": url,
        },
        "generated_at": datetime.now(UTC).isoformat(),
    }


def build_portfolio_clarity(analysis: dict[str, Any]) -> dict[str, Any]:
    """Hero #4 — one plain-language risk sentence + structured clarity."""
    risk = str(analysis.get("risk_level") or "MEDIUM").upper()
    score = analysis.get("risk_score")
    beta = analysis.get("btc_beta_weighted")
    loss = analysis.get("estimated_loss_formatted") or analysis.get("estimated_loss_usd")
    drop = analysis.get("scenario_btc_drop_pct") or 15
    total = analysis.get("total_value_formatted") or analysis.get("total_value")
    one = (
        f"Your portfolio looks {risk.lower()} risk"
        + (f" ({score}/10)" if score is not None else "")
        + (f" on ~{total}" if total is not None else "")
        + (f"; BTC beta ~{float(beta):.0%}" if beta is not None else "")
        + (f". If BTC drops {drop:.0f}%, expect about {loss} drawdown." if loss is not None else ".")
    )
    return {
        "hero": "portfolio_ai",
        "one_sentence": one,
        "risk_level": risk,
        "risk_score": score,
        "plain_language": analysis.get("plain_language") or one,
        "scenario_note": analysis.get("scenario_note") or "",
        "ready": True,
    }


def heroes_quality_manifest() -> dict[str, Any]:
    """Public readiness map for the six heroes (no seventh button)."""
    return {
        "principle": "Polish six heroes — do not add a seventh product button",
        "ui_language": "en",
        "heroes": [
            {
                "id": "opportunity_score_explainability",
                "bar": "Why in <5s with Top-3 factors + sources",
                "surfaces": [PATH_DASHBOARD, "/", "/oracle/{symbol}/explain"],
                "api": ["/api/heroes/quality"],
            },
            {
                "id": "whale_intelligence_radar",
                "bar": "One plain sentence; Signal vs Noise labeled",
                "surfaces": ["/dashboard#whales"],
                "api": ["/api/whale/signal-vs-noise"],
            },
            {
                "id": "public_accuracy_ledger",
                "bar": "Full public proof, no login; shareable",
                "surfaces": ["/oracle-accuracy"],
                "api": ["/api/ledger/share-kit", "/api/audit-challenge"],
            },
            {
                "id": "portfolio_ai",
                "bar": "Portfolio risk in plain language",
                "surfaces": ["/dashboard#portfolio"],
                "api": ["/portfolio/analyze"],
            },
            {
                "id": "single_sentence_oracle",
                "bar": "One symbol → one Act/Wait sentence (front door)",
                "surfaces": ["/", PATH_DASHBOARD],
                "api": ["/oracle/{symbol}", "/oracle/{symbol}/quick"],
            },
            {
                "id": "decision_certificate",
                "bar": "Exportable / shareable proof per decision",
                "surfaces": ["/", PATH_DASHBOARD],
                "api": ["/api/oracle/decision-certificate"],
            },
        ],
        "not_building": [
            "viral_arena",
            "browser_extension_platform",
            "neuro_design_surface",
            "neuro_design_canvas",
            "sor_twap_tca_claims",
            "100_indicator_retail_surface",
            "fifteen_section_platform_map",
        ],
        "five_outcomes": [
            "Discover opportunities",
            "Make a decision",
            "Reduce risk",
            "Save time",
            "Improve execution quality",
        ],
        "success_metric": "60_second_grasp",
        "binding_doc": "docs/STRATEGIC_CORRECTION_BINDING.md",
        "generated_at": datetime.now(UTC).isoformat(),
    }
