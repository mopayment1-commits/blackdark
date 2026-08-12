"""DEC-0218 — residual XSS sink hardening gates."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
STATIC_JS = ROOT / "static" / "js"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_shared_escape_helper_exists():
    helper = STATIC_JS / "dom_escape.js"
    assert helper.is_file()
    src = _read(helper)
    assert "function escapeHtml" in src
    assert "function safeUrl" in src
    assert 'u.protocol === "http:"' in src or "u.protocol === 'http:'" in src
    assert 'u.protocol === "https:"' in src or "u.protocol === 'https:'" in src


def test_templates_never_set_localstorage_bd_token():
    offenders: list[str] = []
    for path in TEMPLATES.rglob("*.html"):
        text = _read(path)
        if re.search(r"localStorage\s*\.\s*setItem\s*\(\s*['\"]bd_token['\"]", text):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"templates must not set localStorage bd_token: {offenders}"


def test_dashboard_and_platform_expose_escape_helpers():
    dash = _read(TEMPLATES / "dashboard.html")
    plat = _read(TEMPLATES / "platform.html")
    assert "function escapeHtml" in dash or "escapeHtml" in dash
    assert "function esc(" in dash or "esc(" in dash
    assert "escapeHtml" in plat and ("esc(" in plat or "esc =" in plat or "esc," in plat)
    assert "dom_escape.js" in plat or "dom_safe.js" in plat


def test_representative_sinks_escape_conflict_upgrade_api_fields():
    dash = _read(TEMPLATES / "dashboard.html")
    landing = _read(TEMPLATES / "landing.html")
    plat = _read(TEMPLATES / "platform.html")
    oracle = _read(TEMPLATES / "oracle_accuracy.html")
    since = _read(TEMPLATES / "since_you_left.html")
    arena = _read(TEMPLATES / "proof_arena.html")

    # Dashboard conflict / upgrade / API-ish fields
    assert "esc(conflict.severity)" in dash or "esc(conflict.reason" in dash
    assert "esc(d.upgrade_hint.message" in dash or "esc(cont.upgrade_hint" in dash
    assert "esc(o.kind_label" in dash or "esc(o.asset" in dash
    assert "textContent" in dash

    # Landing conflict / upgrade
    assert "esc(conflict.severity)" in landing or "Contradiction Veto" in landing and "esc(" in landing
    assert "esc(data.upgrade_hint.message" in landing
    assert "safeUrl(detail.upgrade_url)" in landing or "safeUrl(" in landing

    # Platform API rows
    assert "esc(o.asset)" in plat and "esc(o.buy_venue)" in plat
    assert "safeUrl(h.link)" in plat or "safeUrl(" in plat

    # Oracle + companion surfaces
    assert "esc(r.asset" in oracle or "esc(r.verdict" in oracle
    assert "esc(x.title)" in since and "safeUrl(x.href)" in since
    assert "esc(x.user)" in arena


def test_optional_dangerous_unescaped_innerhtml_pattern_scan():
    """Flag obvious unescaped template-literal innerHTML interpolations of known risky fields."""
    risky = re.compile(
        r"innerHTML\s*=\s*`[^`]*\$\{(?!esc\(|escapeHtml\(|safeUrl\(|safeShareUrl\(|fmt\(|Number\()"
        r"(?:detail\.message|upgrade_hint|conflict\.|x\.title|x\.detail|o\.asset|a\.body|a\.title|"
        r"d\.disclaimer|headline|cont\.summary)[^}]*\}",
        re.MULTILINE,
    )
    hits: list[str] = []
    priority = [
        "dashboard.html",
        "platform.html",
        "landing.html",
        "oracle_accuracy.html",
        "proof_arena.html",
        "since_you_left.html",
        "zero_tolerance.html",
        "priority_chain.html",
        "profile.html",
        "b2b.html",
    ]
    for name in priority:
        text = _read(TEMPLATES / name)
        for m in risky.finditer(text):
            hits.append(f"{name}: {m.group(0)[:120]}")
    assert hits == [], "unescaped risky innerHTML interpolations:\n" + "\n".join(hits)


def test_net_edge_truth_rejects_unknown_withdrawal():
    from net_edge_truth import compute_net_edge_truth

    # Missing key — must fail closed (never invent 0).
    missing = compute_net_edge_truth(
        {
            "net_profit_usdt": 5.0,
            "quote_amount": 1000,
            "total_slippage_bps": 2,
            "trading_fees_usdt": 0.1,
            "quote_age_ms": 100,
            "estimated_recipients": 1,
        }
    )
    assert missing["reject"] is True
    assert missing["pass"] is False
    assert "missing_withdrawal_fee" in missing["reasons"]
    assert missing["economics"]["withdrawal_fee_usdt"] is None

    # Explicit None — same (other economics present so withdrawal is the fail reason).
    none_fee = compute_net_edge_truth(
        {
            "net_profit_usdt": 5.0,
            "quote_amount": 1000,
            "total_slippage_bps": 2,
            "trading_fees_usdt": 0.1,
            "withdrawal_fee_usdt": None,
            "quote_age_ms": 100,
        }
    )
    assert none_fee["reject"] is True
    assert "missing_withdrawal_fee" in none_fee["reasons"]

    # Known zero is allowed (venue reported free withdrawal).
    known_zero = compute_net_edge_truth(
        {
            "net_profit_usdt": 2.5,
            "quote_amount": 500,
            "total_slippage_bps": 3,
            "withdrawal_fee_usdt": 0.0,
            "trading_fees_usdt": 0.2,
            "quote_age_ms": 120,
            "estimated_recipients": 2,
            "flywheel_net_after_crowd_usd": 2.1,
        }
    )
    assert known_zero.get("reject") is False or "missing_withdrawal_fee" not in known_zero.get("reasons", [])


def test_cex_dex_fee_matrix_authority_not_default_taker():
    src = _read(ROOT / "bd_platform" / "cex_dex_arbitrage.py")
    assert "def _indicative_fee_bps" in src
    assert "from fee_matrix import taker_fee" in src
    # Mid-price path must not use config.DEFAULT_TAKER_FEE as live fee authority.
    assert "config.DEFAULT_TAKER_FEE" not in src
    assert "fee_matrix" in src
    assert "indicative_fee_bps" in src


def test_admin_templates_escape_or_dom_text():
    for name in ("admin_launch.html", "admin_roadmap.html", "admin_plan.html"):
        text = _read(TEMPLATES / name)
        assert "dom_safe.js" in text or "escapeHtml" in text or "globalThis.esc" in text
        # Must not interpolate raw i.title / i.note without esc/textContent
        assert "${i.title}" not in text
        assert "${i.note||''}" not in text or "esc(i.note" in text


def test_platform_no_gatedhtml_passthrough():
    plat = _read(TEMPLATES / "platform.html")
    assert "gatedHtml" not in plat
    assert "renderLoadError" in plat or "renderGated" in plat


def test_csp_nonce_mode_scaffold():
    src = _read(ROOT / "security_middleware.py")
    assert "CSP_NONCE_MODE" in src
    assert "strict-dynamic" in src
    assert "csp_nonce" in src
    assert "_inject_html_csp_nonce" in src
    assert (STATIC_JS / "csp_events.js").is_file()


def test_discipline_mirror_uses_dom_only_rows():
    text = _read(TEMPLATES / "discipline.html")
    assert "innerHTML = rows" not in text
    assert "createElement" in text and "textContent" in text
    assert "dom_escape.js" in text


def test_templates_prefer_data_bd_over_inline_handlers():
    offenders: list[str] = []
    for path in TEMPLATES.rglob("*.html"):
        text = _read(path)
        # Allow JS property assignment (btn.onclick = ...) but not HTML on* attributes.
        for m in re.finditer(r"\bon(?:click|change|submit|input|keydown)\s*=\s*\"", text):
            offenders.append(f"{path.relative_to(ROOT)}:{text.count(chr(10), 0, m.start())+1}")
    assert offenders == [], f"inline HTML event handlers remain: {offenders}"


def test_safeurl_href_interpolations_are_escaped():
    for name in ("landing.html", "platform.html", "since_you_left.html", "miss_feed.html"):
        text = _read(TEMPLATES / name)
        # href="${safeUrl(...)}" without esc is attribute-breakable
        assert 'href="${safeUrl(' not in text
        assert "href=\"${safeUrl(" not in text


def test_fee_matrix_unknown_venue_none():
    import fee_matrix
    fee_matrix._matrix.clear()
    assert fee_matrix.taker_fee("totally_unknown_xyz") is None


def test_net_edge_rejects_missing_net_and_slip():
    from net_edge_truth import compute_net_edge_truth

    missing_net = compute_net_edge_truth({"quote_amount": 100, "total_slippage_bps": 1, "trading_fees_usdt": 0.1, "withdrawal_fee_usdt": 0.0})
    assert missing_net["reject"] is True
    assert "missing_net_profit" in missing_net["reasons"]

    missing_slip = compute_net_edge_truth({"net_profit_usdt": 1.0, "quote_amount": 100, "trading_fees_usdt": 0.1, "withdrawal_fee_usdt": 0.0})
    assert missing_slip["reject"] is True
    assert "missing_slippage_bps" in missing_slip["reasons"]
