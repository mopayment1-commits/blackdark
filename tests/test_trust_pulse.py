"""Trust Pulse — first-open daily decision + live freshness."""

from __future__ import annotations

from pathlib import Path


def test_trust_pulse_manifest():
    from trust_pulse import trust_pulse_manifest

    m = trust_pulse_manifest()
    assert m["surface"] == "trust_pulse"
    assert "news_digest" in m["not"]
    assert m["endpoints"]["pulse"] == "/api/trust-pulse"
    assert m["endpoints"]["stream"] == "/api/trust-pulse/stream"


def test_norm_action_and_freshness():
    from trust_pulse import _freshness, _norm_action

    assert _norm_action("BUY") == "ACT"
    assert _norm_action("wait") == "WAIT"
    assert _norm_action("SELL") == "CAUTION"
    live = _freshness(8.0, stale=False)
    assert live["status"] == "live"
    stale = _freshness(200.0, stale=True)
    assert stale["stale"] is True


def test_shape_pulse_includes_proof_and_ledger():
    from trust_pulse import _shape_pulse

    payload = {
        "symbol": "BTC",
        "decision_action": "WAIT",
        "verdict": "WAIT",
        "decision_sentence": "Wait — mixed signals.",
        "opportunity_score": 55,
        "price": 100000,
        "change_24h": 1.2,
        "tier": "free",
        "oqs_why": {
            "grasp_line": "Top 3",
            "top_3_factors": [
                {"factor": "Momentum soft", "detail": "24h muted", "source": "live"}
            ],
        },
        "decision_certificate": {
            "certificate_hash": "abc123def456",
            "share_text": "share me",
            "share_urls": {"x": "https://x.com"},
            "watermark": "Free Proof",
            "verify_url": "/oracle-accuracy",
        },
        "compliance_footer": {"disclaimer": "Not financial advice."},
        "_pulse_meta": {"fetched_at": __import__("time").time(), "asset": "BTC"},
    }
    pulse = _shape_pulse(payload, previous_action="ACT")
    assert pulse["action"] == "WAIT"
    assert pulse["flip"]["from"] == "ACT"
    assert pulse["proof"]["watermark"] == "Free Proof"
    assert pulse["ledger"]["href"] == "/oracle-accuracy"
    assert pulse["why"]["factors"]


def test_continuity_pro_vs_free():
    from trust_pulse import _shape_pulse
    import time

    base = {
        "symbol": "ETH",
        "decision_action": "ACT",
        "decision_sentence": "Act with caution.",
        "tier": "pro",
        "oqs_why": {"top_3_factors": [{"factor": "Flow", "detail": "", "source": ""}]},
        "decision_certificate": {"certificate_hash": "x"},
        "_pulse_meta": {"fetched_at": time.time()},
    }
    pro = _shape_pulse(base, previous_action="WAIT", previous_seen_at="2026-08-01T00:00:00Z")
    assert pro["continuity"].get("flipped") is True
    assert pro["continuity"].get("locked") is not True

    free_payload = {**base, "tier": "free"}
    free = _shape_pulse(free_payload, previous_action="WAIT")
    assert free["continuity"].get("locked") is True


def test_routes_and_templates_wire():
    src = Path("dashboard.py").read_text(encoding="utf-8")
    assert '"/api/trust-pulse"' in src
    assert '"/api/trust-pulse/stream"' in src
    dash = Path("templates/dashboard.html").read_text(encoding="utf-8")
    land = Path("templates/landing.html").read_text(encoding="utf-8")
    assert 'id="trust-pulse"' in dash
    assert "loadTrustPulse" in dash
    assert "startTrustPulseStream" in dash
    assert 'id="trust-pulse"' in land
    assert "loadLandingTrustPulse" in land
    assert Path("docs/TRUST_PULSE.md").is_file()


def test_sse_generator_emits_connected():
    import asyncio
    from trust_pulse import trust_pulse_sse_generator

    async def _first():
        gen = trust_pulse_sse_generator("BTC", tier="free", interval_sec=60)
        first = await anext(gen)
        await gen.aclose()
        return first

    first = asyncio.run(_first())
    assert "connected" in first
    assert "trust_pulse" in first
