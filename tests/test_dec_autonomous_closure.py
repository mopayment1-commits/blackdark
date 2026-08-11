"""Executable closure evidence for autonomous product/UX decisions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _flatten_strings(item)]
    if isinstance(value, (list, tuple, set)):
        return [text for item in value for text in _flatten_strings(item)]
    return []


def test_dec_0004_quiet_engines_absent_from_rendered_retail_navigation():
    """Retail entry chrome exposes lenses/heroes, never internal engine names."""
    from dashboard import app

    client = TestClient(app)
    forbidden = {
        "microstructure",
        "sentiment",
        "macro",
        "on-chain",
        "onchain",
        "storage tier",
        "stream kernel",
        "arbitrage",
        "whale",
    }
    for path in ("/", "/dashboard?lens=prove"):
        response = client.get(path)
        assert response.status_code == 200
        nav = re.search(r"<nav\b.*?</nav>", response.text, flags=re.IGNORECASE | re.DOTALL)
        assert nav, path
        links = re.findall(
            r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
            nav.group(0),
            flags=re.IGNORECASE | re.DOTALL,
        )
        nav_text = " ".join(
            f"{href} {re.sub(r'<[^>]+>', ' ', label)}" for href, label in links
        ).lower()
        assert not (forbidden & {term for term in forbidden if term in nav_text}), (path, nav_text)


def test_dec_0023_sealed_first_viewport_has_only_brand_ctas_and_trust_pulse():
    from dashboard import app

    response = TestClient(app).get("/")
    assert response.status_code == 200
    html = response.text
    top = html.index('id="top"')
    seal = html.index('id="seal"')
    first_viewport = html[top:seal]

    for required in (
        "BLACKDARK",
        "We publish the miss.",
        "hero-bleed",
        'id="trust-pulse"',
        "Try Oracle Free",
    ):
        assert required in first_viewport
    for clutter in (
        'id="pricing"',
        'id="landingStats"',
        'id="waitlist"',
        "oracle-demo",
        "feature-card",
        "institutionalInquiryForm",
        "Telegram Free Alerts",
    ):
        assert clutter not in first_viewport


def test_dec_0026_all_ai_surface_templates_use_shared_anti_hype_footer():
    # Explicit user-facing AI inventory: Oracle entry/result, audit ledger,
    # model disclosure, regime disclosure, and Anti-Hype control surface.
    ai_surfaces = (
        "landing.html",
        "dashboard.html",
        "oracle_accuracy.html",
        "platform.html",
        "model_card.html",
        "d5_honesty.html",
        "anti_hype.html",
    )
    for name in ai_surfaces:
        source = (TEMPLATES / name).read_text(encoding="utf-8")
        assert 'partials/site_footer.html' in source, name

    footer = (TEMPLATES / "partials" / "site_footer.html").read_text(encoding="utf-8")
    assert "Anti-Hype" in footer
    assert "Not financial advice" in footer
    assert "/oracle-accuracy" in footer


def test_dec_0027_companion_rail_manifest_is_complete():
    from site_services import site_services_manifest

    manifest = site_services_manifest()
    footer = manifest["footer"]
    hrefs = {
        item["href"]
        for group in ("product", "trust", "company", "legal")
        for item in footer[group]
    }
    assert {"/contact", "/faq", "/how-it-works", "/status", "/legal"} <= hrefs
    assert footer["follow"]
    assert all(item["href"] for item in footer["follow"])
    assert footer["contact"]["support_email"]
    assert footer["contact"]["feedback_path"] == "/feedback"
    assert {"proof_card", "ledger_snapshot"} <= set(manifest["share_policy"]["allowed"])
    assert {"x", "whatsapp", "telegram", "copy"} <= set(manifest["share_policy"]["channels"])


@pytest.mark.asyncio
async def test_dec_0108_user_visible_returns_claims_are_explicitly_denied():
    claim = re.compile(r"\bguarantee(?:d|s|ing)?[- ]+(?:returns?|profits?|roi|outcomes?)\b", re.IGNORECASE)
    denial = re.compile(
        r"\b(?:no|not|never|cannot|can't|forbid(?:den)?|deny|denied|out of scope|stay off)\b|≠",
        re.IGNORECASE,
    )

    for path in TEMPLATES.rglob("*.html"):
        source = path.read_text(encoding="utf-8")
        for match in claim.finditer(source):
            context = source[max(0, match.start() - 100) : match.end() + 100]
            assert denial.search(context), f"positive returns claim in {path}: {context!r}"

    from buyer_model_card import build_buyer_model_card
    from pricing_catalog import pricing_catalog
    from site_services import site_services_manifest

    for payload in (pricing_catalog(), site_services_manifest()):
        for text in _flatten_strings(payload):
            if claim.search(text):
                assert denial.search(text), text
    assert "Guaranteed returns" in (await build_buyer_model_card())["out_of_scope"]


def test_dec_0020_fail_closed_gate_matrix_and_dependency_failure(monkeypatch):
    from constitution_gates import ensure_execution_gates, is_alertable

    allowed = {
        "execution_feasibility": "full",
        "net_edge_truth": {"reject": False},
        "opportunity_half_life": {
            "remaining_seconds": 30,
            "disappearance_probability": 0.1,
        },
        "dimension_conflict": {"veto": False, "abstain": False},
    }
    assert is_alertable(allowed) is True

    rejected_rows = (
        {**allowed, "net_edge_truth": {"reject": True}},
        {**allowed, "opportunity_half_life": None},
        {**allowed, "dimension_conflict": {"veto": True, "abstain": False}},
        {**allowed, "dimension_conflict": {"veto": False, "abstain": True}},
        {**allowed, "gates_missing": True},
    )
    assert all(is_alertable(row) is False for row in rejected_rows)

    def unavailable(_row):
        raise RuntimeError("truth dependency unavailable")

    monkeypatch.setattr("net_edge_truth.compute_net_edge_truth", unavailable)
    gated = ensure_execution_gates(
        {
            "execution_feasibility": "full",
            "opportunity_half_life": allowed["opportunity_half_life"],
            "dimension_conflict": allowed["dimension_conflict"],
        }
    )
    assert gated["gates_missing"] is True
    assert gated["net_edge_truth"]["reject"] is True
    assert is_alertable(gated) is False


def test_dec_0020_ood_and_high_drift_fail_closed(monkeypatch):
    from ml.drift_monitor import enforce_drift_actions, ood_score

    monkeypatch.setattr("ml.drift_monitor.load_feature_envelope", lambda: None)
    monkeypatch.setattr("ml.drift_monitor.config.ML_OOD_FAIL_CLOSED", True)
    assert ood_score({"price": 50_000})["is_ood"] is True

    freezes: list[tuple[str, int]] = []

    def freeze(reason: str, *, duration_sec: int):
        freezes.append((reason, duration_sec))
        return {"frozen": True, "reason": reason}

    monkeypatch.setattr("risk_manager.freeze_trading", freeze)
    action = enforce_drift_actions(
        {
            "drift_detected": True,
            "alerts": [{"feature": "volatility", "psi": 0.75, "severity": "high"}],
        }
    )
    assert action["action"] == "freeze_trading"
    assert freezes and freezes[0][0].startswith("ml_drift_high:")


def test_dec_0310_stale_or_unknown_data_never_defaults_to_live():
    from zero_tolerance import apply_zero_tolerance

    for freshness in (None, {"state": "stale", "stale": True}):
        payload = {"live_label": "LIVE"}
        if freshness is not None:
            payload["data_freshness"] = freshness
        gated = apply_zero_tolerance(payload)
        assert gated["live_label"] == "STALE_OR_UNKNOWN"
        assert gated["live_claim_allowed"] is False

    landing = (TEMPLATES / "landing.html").read_text(encoding="utf-8")
    dashboard = (TEMPLATES / "dashboard.html").read_text(encoding="utf-8")
    assert "fresh.label || 'Live'" not in landing
    assert "(fromStream ? 'Live'" not in dashboard
    assert "Freshness unknown" in landing
    assert "Stale — not live" in landing
    assert "Stale — not live" in dashboard
