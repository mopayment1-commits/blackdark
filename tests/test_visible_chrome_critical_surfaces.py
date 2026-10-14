"""Third-pass gates: Language / Login / Sign up / Pricing must be USER-VISIBLE."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(".")


def _landing() -> str:
    return (ROOT / "templates/landing.html").read_text(encoding="utf-8")


def test_landing_uses_global_header_with_session_chrome():
    land = _landing()
    assert "partials/global_header.html" in land
    global_hdr = (ROOT / "templates/partials/global_header.html").read_text(encoding="utf-8")
    assert "bd-global-header" in global_hdr
    assert "site_top_nav.html" in global_hdr
    assert "site_top_nav.html" in global_hdr


def test_top_utility_has_anonymous_chrome_branches():
    util = (ROOT / "templates/partials/site_top_nav.html").read_text(encoding="utf-8")
    assert "lang_switcher.html" in util
    assert "/login" in util
    assert "/login?tab=register" in util
    assert 'id="bdUtilPricing"' in util
    assert "bd-header-util" in util
    assert "header_authenticated" in util
    assert "bd-account-menu" in util
    assert "bd-tier-badge" in util
    assert "/profile" in util
    assert "bd-header-upgrade" not in util


def test_lang_switcher_lists_twenty_five_locales():
    from i18n_service import LOCALES, _locale_json_codes, list_locales

    sw = (ROOT / "templates/partials/lang_switcher.html").read_text(encoding="utf-8")
    assert 'id="bdLangTrigger"' in sw
    assert "_locales" in sw
    assert len(LOCALES) == 25
    exposed = list_locales()
    assert len(exposed) == len(_locale_json_codes())
    assert len(exposed) == 25


def test_login_has_register_tab_and_global_header():
    login = (ROOT / "templates/login.html").read_text(encoding="utf-8")
    assert 'id="registerShell"' in login
    assert "global_header.html" in login
    assert 'class="login-main"' in login
    assert 'class="auth-tabs"' in login
    assert "bd-global-header .bd-header-util" in login
    assert "login-chrome" not in login
    assert "doRegister" in login
    assert "accepted_terms" in login


def test_profile_has_lang_billing_and_signup_gate():
    profile = (ROOT / "templates/profile.html").read_text(encoding="utf-8")
    assert "global_header.html" in profile
    assert 'lang="{{ lang|default(\'en\') }}"' in profile or 'lang="{{ lang|default(' in profile
    assert "create-checkout-session?tier=pro" in profile
    assert "create-checkout-session?tier=elite" in profile
    assert "Plus · $29/mo" in profile
    assert "Pro · $49/mo" in profile
    assert "19.99" not in profile
    assert "tab=register" in profile
    assert "billingReady" not in profile


def test_dashboard_and_accuracy_include_global_header():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    acc = (ROOT / "templates/oracle_accuracy.html").read_text(encoding="utf-8")
    assert "global_header.html" in dash
    assert "global_header.html" in acc


def test_dashboard_prove_lens_upgrade_pro_routes_to_pricing():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "Upgrade Pro" in dash
    assert "currentLens === 'prove'" in dash
    assert "goNavUrl('/pricing')" in dash
    assert "btn-upgrade-cta" in dash
    assert "body.lens-prove .section-operate-plus .btn-upgrade-cta" in dash


def test_dashboard_prove_trust_pulse_symbol_quick_oracle():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert 'id="tpSymbol"' in dash
    assert "onTrustPulseSymbolChange" in dash
    assert "loadTrustPulseQuick" in dash
    assert "fetchOracleQuick" in dash
    assert "renderOracleQuickDecision" in dash
    assert "renderOracleBoxFromQuick" in dash
    assert "oracleQuickUrl" in dash
    assert "/oracle/${encodeURIComponent(symbol)}/quick" in dash
    quick_render = dash.split("function renderOracleQuickDecision", 1)[1].split("function mapOracleQuickAction", 1)[0]
    assert "mode === 'pro'" in quick_render
    assert "buildWhyFactorsHtml" in quick_render
    assert "buildCertBlock" in quick_render
    assert dash.split("function onUxModeChange", 1)[1].split("function syncProveSymbolSelects", 1)[0].count("currentLens === 'prove'") >= 1


def test_dashboard_open_full_proof_routes_to_readable_page():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "openTrustPulseProofPage" in dash
    assert "/trust-pulse/proof" in dash
    assert "JSON.stringify(cert" not in dash.split("function openDecisionCertificate", 1)[1].split("function clearVisibleTrust", 1)[0]


def test_dashboard_prove_lens_my_book_operate_gate_not_raw_billing_json():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "Requires Operate subscription" in dash
    assert "View pricing" in dash
    assert "يتطلب اشتراك Operate" not in dash
    assert "عرض الأسعار" not in dash
    assert "showOperateGate" in dash
    assert "openMyBookEntry" in dash
    assert "lockedId === 'my_book'" in dash
    assert "lockedId === 'alerts'" in dash
    assert "openAlertsEntry" in dash
    assert "create-checkout-session?tier=" not in dash.split("async function upgradeTier", 1)[1].split("let lastPulse", 1)[0]


def test_coverage_honesty_logo_uses_site_accent_cyan():
    html = (ROOT / "templates/coverage_honesty.html").read_text(encoding="utf-8")
    logo_line = next(line for line in html.splitlines() if ".logo{" in line.replace(" ", ""))
    assert "color:#22d3ee" in logo_line.replace(" ", "")
    assert "color:var(--ok)" not in logo_line


def test_miss_feed_share_honesty_button_stable_handler():
    html = (ROOT / "templates/miss_feed.html").read_text(encoding="utf-8")
    share_line = next(line for line in html.splitlines() if 'id="share"' in line)
    assert 'type="button"' in share_line
    assert "shareMissFeedHonesty" in html
    assert "flashMissFeedShare" in html
    assert "Copied!" in html
    assert "share_urls?.x" not in html or "getElementById('share').href" not in html


def test_half_life_page_omits_launch57_desk_line():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "isDedicatedHalfLifePage" in dash
    assert "desk timing grounded (no legacy oracle fetch)" in dash
    block = dash.split("function commandHomeToHalfLifeHeat", 1)[1].split("async function loadHalfLifeClock", 1)[0]
    assert "isDedicatedHalfLifePage()" in block


def test_dashboard_prove_lens_single_primary_entry_rail_under_trust_pulse():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert 'id="entryRail"' in dash
    assert "tp-entry-rail" in dash
    assert dash.count('id="entryRail"') == 1
    assert "body.lens-prove #intentWrap { display: none; }" in dash
    assert "if (currentLens === 'prove') return;" in dash.split("function renderLaunch57Intents", 1)[1].split("function readLastPulseVisit", 1)[0]


def test_dashboard_prove_lens_single_verify_entry_rail_only():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    tp_cta = dash.split('class="tp-cta"', 1)[1].split("</div>", 1)[0]
    toolbar = dash.split('class="toolbar hide-in-room"', 1)[1].split("</div>", 1)[0]
    assert "oracle-accuracy" not in tp_cta
    assert "oracle-accuracy" not in toolbar
    assert "it.id === 'verify'" in dash
    assert "id === 'verify'" in dash


def test_dashboard_desk_tools_opens_menu_on_prove_lens():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert 'id="deskToolsMenu"' in dash
    assert "desk-tools-details" in dash
    assert "desk-tools-dropmenu" in dash
    assert '/dashboard?lens=desk#stealth' in dash
    assert "function bindDeskToolsUi()" in dash
    assert "window.openDeskTools = openDeskTools" in dash
    toolbar = dash.split('class="toolbar hide-in-room"', 1)[1].split("</div>", 1)[0]
    assert "Desk tools" in toolbar
    assert 'class="desk-tools-details desk-tools-nav"' in dash
    assert "async function openDeskToolSection" in dash
    assert "DESK_TOOL_SECTIONS" in dash
    desk_menu = dash.split('aria-label="Desk tools"', 1)[1].split("</details>", 1)[0]
    assert 'href="/dashboard?lens=desk#stealth">Open Desk lens' in desk_menu
    assert "/dashboard#portfolio" not in desk_menu


def test_dashboard_markdown_on_prove_lens_shows_upgrade_not_raw_api_link():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    digest = dash.split('id="operate-digest"', 1)[1].split("</section>", 1)[0]
    assert 'data-bd-call="openDailyReportMarkdown"' in digest
    assert 'href="/api/reports/daily/markdown"' not in digest
    assert "function openDailyReportMarkdown()" in dash
    assert "operatePlusBlockedOnProveLens()" in dash.split("openDailyReportMarkdown", 1)[1][:800]
    assert "Upgrade to Pro" in dash.split("openDailyReportMarkdown", 1)[1][:800]


def test_header_prove_and_operate_lens_hrefs_distinct():
    nav = (ROOT / "templates/partials/site_top_nav.html").read_text(encoding="utf-8")
    assert 'data-nav-key="prove"' in nav
    assert 'href="/dashboard?lens=prove"' in nav
    assert 'data-nav-key="operate"' in nav
    assert 'href="/dashboard?lens=operate"' in nav
    assert "bd_global_nav.js" in nav
    js = (ROOT / "static/js/bd_global_nav.js").read_text(encoding="utf-8")
    assert 'operate: "/dashboard?lens=operate"' in js
    assert "syncGlobalNavActive" in js


def test_committee_one_pager_uses_dark_site_chrome():
    html = (ROOT / "templates/committee_one_pager.html").read_text(encoding="utf-8")
    assert "/static/css/trust-os.css" in html
    assert "background:#f7f4ee" not in html
    assert 'id="thesis"' in html and "Committee One-Pager" in html
    assert "Public kill-rate" in html
    assert 'id="checks"' in html


def test_corpus_passport_uses_dark_site_chrome():
    html = (ROOT / "templates/corpus_passport.html").read_text(encoding="utf-8")
    assert "/static/css/trust-os.css" in html
    assert "background:#f4f1ea" not in html
    assert "box-shadow:8px 8px 0 #111" not in html
    assert 'id="stamp"' in html and "BLACKDARK Corpus Passport" in html
    assert "Request corpus passport PDF" in html
    assert 'id="requestCorpusPdfBtn"' in html
    assert "requestCorpusPassportPdf" in html
    assert "/api/due-diligence/corpus-passport.pdf" in html
    assert 'id="corpusPassportRequestForm"' in html
    assert 'href="/contact"' not in html


def test_dashboard_anti_hype_toggle_has_visible_banner_and_metric_hook():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert 'id="antiHypeBanner"' in dash
    assert "body.anti-hype-on .anti-hype-banner" in dash
    assert "tp-hype-metric" in dash
    assert "banner.hidden = !on" in dash
    assert 'id="antiHypeBtn"' in dash and 'data-bd-sync="1"' in dash
    toggle_block = dash.split("async function toggleAntiHype()", 1)[1].split("async function loadSinceYouLeft", 1)[0]
    assert "applyAntiHypeClass();" in toggle_block.split("await fetch", 1)[0]


def test_dashboard_share_proof_builds_clipboard_fallback():
    dash = (ROOT / "templates/dashboard.html").read_text(encoding="utf-8")
    assert "buildTrustPulseShareBundle" in dash
    assert "syncTrustPulseShareState" in dash
    share_block = dash.split("async function shareTrustPulse()", 1)[1].split("window.shareTrustPulse", 1)[0]
    assert "copyTextWithFallback" in share_block
    assert "flashShareProofButton" in share_block
    assert "Copied!" in dash
    assert 'id="tpShareBtn"' in dash and 'data-bd-sync="1"' in dash
    assert "window.shareTrustPulse = shareTrustPulse" in dash
    csp = (ROOT / "static/js/csp_events.js").read_text(encoding="utf-8")
    assert "data-bd-sync" in csp


def test_pricing_ladder_not_embedded_on_landing():
    land = _landing()
    assert 'id="pricing"' not in land
    assert "pricing.title_os" not in land
    assert "pricing.decide_pro" not in land
    assert "pricing.see_edge_elite" not in land
    assert "pricing.execute_quant" not in land
    assert "pricing.scale_institutional" not in land
    assert "pricing.popular" not in land
    assert "feat.note" not in land
    assert "$19.99" not in land
    assert "$49.99" not in land
    assert "$129.99" not in land
    assert "pricing.from_open" not in land
    assert 'class="price"' not in land
    assert "Decision Desk" not in land
    assert "$29" not in land
    assert "3,000" not in land
    assert "billingReadyLine" not in land
    assert "/login?tab=register" in land
