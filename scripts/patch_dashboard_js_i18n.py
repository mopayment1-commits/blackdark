#!/usr/bin/env python3
"""One-shot patches for dashboard.html JS i18n (idempotent-ish)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "templates" / "dashboard.html"
text = PATH.read_text(encoding="utf-8")

REPLACEMENTS: list[tuple[str, str]] = [
    (
        'chips.push(`<span class="tp-chip ${evCls}">Evidence: ${esc(ev)}</span>`);',
        'chips.push(`<span class="tp-chip ${evCls}">${esc(i18nT("dash.js.evidence", { ev }))}</span>`);',
    ),
    (
        'chips.push(`<span class="tp-chip ok">Net-Edge: ${esc(netEdge.truth_score)}</span>`);',
        'chips.push(`<span class="tp-chip ok">${esc(i18nT("dash.js.net_edge", { score: netEdge.truth_score }))}</span>`);',
    ),
    (
        "|| 'Verify Ledger';",
        "|| i18nT('dash.js.verify_ledger');",
    ),
    (
        'style="border:none;cursor:pointer;font:inherit">cert ${esc(String(proof.certificate_hash).slice(0,12))}…</button>`);',
        'style="border:none;cursor:pointer;font:inherit">${esc(i18nT("dash.js.cert_prefix"))} ${esc(String(proof.certificate_hash).slice(0,12))}…</button>`);',
    ),
    (
        'if (proof.prediction_id) chips.push(`<span class="tp-chip">id ${esc(proof.prediction_id)}</span>`);',
        'if (proof.prediction_id) chips.push(`<span class="tp-chip">${esc(i18nT("dash.js.id_prefix"))} ${esc(proof.prediction_id)}</span>`);',
    ),
    (
        'if (p.veto) chips.push(`<span class="tp-chip warn">Veto</span>`);',
        'if (p.veto) chips.push(`<span class="tp-chip warn">${esc(i18nT("dash.js.veto_chip"))}</span>`);',
    ),
    (
        "document.getElementById('tpFoot').innerHTML = '<strong>Anti-Hype</strong> · ' + escapeHtml(ledger.honesty_line) + footBit;",
        "document.getElementById('tpFoot').innerHTML = '<strong>' + esc(i18nT('common.anti_hype')) + '</strong> · ' + escapeHtml(ledger.honesty_line) + footBit;",
    ),
    (
        "const extra = (cont.new_factors||[]).length ? ' · New factors: ' + cont.new_factors.join(', ') : '';",
        "const extra = (cont.new_factors||[]).length ? i18nT('dash.js.new_factors', { factors: cont.new_factors.join(', ') }) : '';",
    ),
    (
        "cont.upgrade_hint||'Decision Pro'",
        "cont.upgrade_hint||i18nT('dash.js.decision_pro')",
    ),
    (
        "const prev = btn.dataset.shareLabel || btn.textContent || 'Share Proof';",
        "const prev = btn.dataset.shareLabel || btn.textContent || i18nT('dash.tp.share_proof');",
    ),
    (
        "btn.textContent = btn.dataset.shareLabel || 'Share Proof';",
        "btn.textContent = btn.dataset.shareLabel || i18nT('dash.tp.share_proof');",
    ),
    (
        "flashShareProofButton('Opened share');",
        "flashShareProofButton(i18nT('dash.js.opened_share'));",
    ),
    (
        "flashShareProofButton('Copy blocked', 2400);",
        "flashShareProofButton(i18nT('dash.js.copy_blocked'), 2400);",
    ),
    (
        'aria-label="Primary entries"',
        'aria-label="{{ t(\'dash.js.entry_rail_aria\') }}"',
    ),
    (
        "if (note) note.textContent = 'Chart unavailable — no OHLCV from Binance or fallback.';",
        "if (note) note.textContent = i18nT('dash.js.chart_unavailable');",
    ),
    (
        "el.innerHTML = `<div class=\"empty\">${esc(detail.message || 'Decision Pro required for daily report')}",
        "el.innerHTML = `<div class=\"empty\">${esc(detail.message || i18nT('dash.js.daily_pro_report'))}",
    ),
    (
        'data-bd-args="[&quot;pro&quot;]">Upgrade Pro</button></div></div>`;',
        'data-bd-args="[&quot;pro&quot;]">${esc(i18nT("dash.js.upgrade_pro_short"))}</button></div></div>`;',
    ),
    (
        "const title = d.title || d.headline || 'Daily research brief';",
        "const title = d.title || d.headline || i18nT('dash.js.daily_brief_title');",
    ),
    (
        "d.oracle_accuracy_percent != null ? ('Oracle accuracy ' + d.oracle_accuracy_percent + '%') : null,",
        "d.oracle_accuracy_percent != null ? i18nT('dash.js.oracle_accuracy', { pct: d.oracle_accuracy_percent }) : null,",
    ),
    (
        "d.moat_score != null ? ('Moat ' + d.moat_score + '/100') : null,",
        "d.moat_score != null ? i18nT('dash.js.moat', { score: d.moat_score }) : null,",
    ),
    (
        "d.whale_alerts_24h != null ? ('Whale alerts ' + d.whale_alerts_24h) : null,",
        "d.whale_alerts_24h != null ? i18nT('dash.js.whale_alerts_24h', { n: d.whale_alerts_24h }) : null,",
    ),
    (
        "d.arb_alerts_24h != null ? ('Arb alerts ' + d.arb_alerts_24h) : null,",
        "d.arb_alerts_24h != null ? i18nT('dash.js.arb_alerts_24h', { n: d.arb_alerts_24h }) : null,",
    ),
    (
        "+ esc(summary || 'Brief ready — open Markdown for full detail.') + '</div>'",
        "+ esc(summary || i18nT('dash.js.brief_ready')) + '</div>'",
    ),
    (
        "+ '<div style=\"margin-top:.55rem;font-size:.72rem;color:#71717a\"><strong>Anti-Hype</strong> · Research brief, not advice · Verify Ledger</div>';",
        "+ '<div style=\"margin-top:.55rem;font-size:.72rem;color:#71717a\"><strong>' + esc(i18nT('common.anti_hype')) + '</strong> · ' + esc(i18nT('dash.js.daily_foot')) + '</div>';",
    ),
    (
        "el.innerHTML = `<div class=\"empty\">${esc(detail.message || 'Pro/Whale required for subscriber value')}",
        "el.innerHTML = `<div class=\"empty\">${esc(detail.message || i18nT('dash.js.pro_whale_value'))}",
    ),
    (
        "el.innerHTML = `<strong>Subscriber value · ${esc(d.tier || '')}</strong>",
        "el.innerHTML = `<strong>${esc(i18nT('dash.js.subscriber_value', { tier: d.tier || '' }))}</strong>",
    ),
    (
        "<div style=\"margin-top:.35rem;font-size:.9rem\">Calls 30d: ${esc(u.oracle_calls_30d ?? 0)} · Risk warnings: ${esc(u.risk_warnings_30d ?? 0)}</div>",
        "<div style=\"margin-top:.35rem;font-size:.9rem\">${esc(i18nT('dash.js.calls_30d', { calls: u.oracle_calls_30d ?? 0, warnings: u.risk_warnings_30d ?? 0 }))}</div>",
    ),
    (
        "<div style=\"margin-top:.55rem;font-size:.72rem;color:#71717a\"><strong>Anti-Hype</strong> · Illustrative usage math · Not guaranteed ROI</div>`;",
        "<div style=\"margin-top:.55rem;font-size:.72rem;color:#71717a\"><strong>${esc(i18nT('common.anti_hype'))}</strong> · ${esc(i18nT('dash.js.subscriber_foot'))}</div>`;",
    ),
    (
        "el.innerHTML = '<table><thead><tr><th>Asset</th><th>OI</th><th>Funding</th></tr></thead><tbody>' +",
        "el.innerHTML = '<table><thead><tr><th>' + esc(i18nT('dash.js.oi_asset')) + '</th><th>' + esc(i18nT('dash.js.oi_col')) + '</th><th>' + esc(i18nT('dash.js.oi_funding')) + '</th></tr></thead><tbody>' +",
    ),
    (
        "el.innerHTML = '<div class=\"empty\">No OI data</div>';",
        "el.innerHTML = '<div class=\"empty\">' + esc(i18nT('dash.js.no_oi')) + '</div>';",
    ),
    (
        "if (stats) stats.textContent = `Live · Cross ${c.cross_exchange||0} · Executable ${arbitrage.executable_count||0} · Profitable ${arbitrage.profitable_count||0}`;",
        "if (stats) stats.textContent = i18nT('dash.js.arb_live_stats', { cross: c.cross_exchange||0, exec: arbitrage.executable_count||0, prof: arbitrage.profitable_count||0 });",
    ),
    (
        "const rej = rejected ? ' · REJECTED' : '';",
        "const rej = rejected ? ' · ' + i18nT('dash.js.rejected') : '';",
    ),
    (
        "<div style=\"font-size:.75rem;color:#71717a\">Truth ${esc(truth.truth_score??'—')} · HL ${esc(half.remaining_seconds??o.expected_half_life_seconds??'—')}s${rej}</div></div>`;",
        "<div style=\"font-size:.75rem;color:#71717a\">${esc(i18nT('dash.js.truth_hl', { truth: truth.truth_score??'—', hl: (half.remaining_seconds??o.expected_half_life_seconds??'—') + 's' }))}${rej}</div></div>`;",
    ),
    (
        "if (stats) stats.textContent = 'Live scan in progress…';",
        "if (stats) stats.textContent = i18nT('dash.js.live_scan_progress');",
    ),
    (
        "stats.textContent = detail.message || 'Pro required';",
        "stats.textContent = detail.message || i18nT('dash.js.pro_required_arb');",
    ),
    (
        "el.innerHTML = `<div class=\"empty\">${esc(detail.message || 'Upgrade required for arbitrage')}",
        "el.innerHTML = `<div class=\"empty\">${esc(detail.message || i18nT('dash.js.upgrade_arb'))}",
    ),
    (
        "stats.textContent = `Cross ${c.cross_exchange||0} · Executable ${data.executable_count||0} · Profitable ${data.profitable_count||0}`;",
        "stats.textContent = i18nT('dash.js.arb_cross_stats', { cross: c.cross_exchange||0, exec: data.executable_count||0, prof: data.profitable_count||0 });",
    ),
    (
        "rejected ? ' · REJECTED' : ''}</div></div>`;",
        "rejected ? ' · ' + i18nT('dash.js.rejected') : ''}</div></div>`;",
    ),
    (
        "}).join('') : '<div class=\"empty\">No opportunities now</div>';",
        "}).join('') : '<div class=\"empty\">' + esc(i18nT('dash.js.no_opportunities')) + '</div>';",
    ),
    (
        "} catch (error) { console.debug(error); el.innerHTML = '<div class=\"empty\">Scan failed</div>'; }",
        "} catch (error) { console.debug(error); el.innerHTML = '<div class=\"empty\">' + esc(i18nT('dash.js.scan_failed')) + '</div>'; }",
    ),
    (
        "if (forceRefresh) el.innerHTML = '<div class=\"loading\">Refreshing inbox…</div>';",
        "if (forceRefresh) el.innerHTML = '<div class=\"loading\">' + esc(i18nT('dash.js.refreshing_inbox')) + '</div>';",
    ),
    (
        "status.textContent = `Inbox ${stats.unread||0} unread · ${stats.generosity_note || 'no TV-style 15/3min hard cap'} · works without Telegram`;",
        "status.textContent = i18nT('dash.js.inbox_status', { unread: stats.unread||0, note: stats.generosity_note || i18nT('dash.js.inbox_note_default') });",
    ),
    (
        "<strong>${esc(a.title||'Alert')}</strong>",
        "<strong>${esc(a.title||i18nT('dash.js.alert_default'))}</strong>",
    ),
    (
        "${a.read ? 'read' : 'new · tap to mark read'}</div>",
        "${a.read ? i18nT('dash.js.read') : i18nT('dash.js.tap_mark_read')}</div>",
    ),
    (
        "<div style=\"margin-top:.4rem;font-size:.7rem;color:#71717a\"><strong>Anti-Hype</strong> · Truth + Half-Life gated · Not financial advice</div>",
        "<div style=\"margin-top:.4rem;font-size:.7rem;color:#71717a\"><strong>${esc(i18nT('common.anti_hype'))}</strong> · ${esc(i18nT('dash.js.inbox_card_foot'))}</div>",
    ),
    (
        "}).join('') : '<div class=\"empty\">No alerts yet — inbox has no TradingView-style 15/3min hard cap</div>';",
        "}).join('') : '<div class=\"empty\">' + esc(i18nT('dash.js.inbox_empty')) + '</div>';",
    ),
    (
        "} catch (error) { console.debug(error); el.innerHTML = '<div class=\"empty\">Inbox unavailable</div>'; }",
        "} catch (error) { console.debug(error); el.innerHTML = '<div class=\"empty\">' + esc(i18nT('dash.js.inbox_unavailable')) + '</div>'; }",
    ),
    (
        'list.innerHTML = \'<li class="empty">No price alerts yet.</li>\';',
        "list.innerHTML = '<li class=\"empty\">' + esc(i18nT('dash.alerts.none')) + '</li>';",
    ),
    (
        "const fired = a.triggered ? ' · <strong style=\"color:#22c55e\">triggered</strong>' : (a.condition_met ? ' · <strong style=\"color:#fbbf24\">condition met</strong>' : '');",
        "const fired = a.triggered ? ' · <strong style=\"color:#22c55e\">' + esc(i18nT('dash.js.triggered')) + '</strong>' : (a.condition_met ? ' · <strong style=\"color:#fbbf24\">' + esc(i18nT('dash.js.condition_met')) + '</strong>' : '');",
    ),
    (
        'data-pa-del="${esc(a.id)}">Remove</button>',
        'data-pa-del="${esc(a.id)}">${esc(i18nT("dash.js.remove"))}</button>',
    ),
    (
        "list.innerHTML = '<li class=\"empty\">No headlines available right now.</li>';",
        "list.innerHTML = '<li class=\"empty\">' + esc(i18nT('dash.js.no_headlines')) + '</li>';",
    ),
    (
        "list.innerHTML = '<li class=\"empty\">Headlines unavailable.</li>';",
        "list.innerHTML = '<li class=\"empty\">' + esc(i18nT('dash.js.headlines_unavailable')) + '</li>';",
    ),
    (
        "if (list) list.innerHTML = '<li class=\"empty\">Price alerts unavailable.</li>';",
        "if (list) list.innerHTML = '<li class=\"empty\">' + esc(i18nT('dash.js.price_alerts_unavailable')) + '</li>';",
    ),
    (
        "if (refresh) el.innerHTML = '<div class=\"loading\">Scanning…</div>';",
        "if (refresh) el.innerHTML = '<div class=\"loading\">' + esc(i18nT('dash.arb.scanning')) + '</div>';",
    ),
    (
        "? `<div class=\"whale-card\" style=\"border-color:rgba(34,211,238,.35)\"><strong>One sentence · Signal vs Noise</strong>",
        "? `<div class=\"whale-card\" style=\"border-color:rgba(34,211,238,.35)\"><strong>${esc(i18nT('dash.js.whale_one_sentence'))}</strong>",
    ),
    (
        "el.innerHTML = '<div class=\"empty\">No whale narratives</div>';",
        "el.innerHTML = '<div class=\"empty\">' + esc(i18nT('dash.js.no_whale')) + '</div>';",
    ),
    (
        "foot.innerHTML = '<strong>Anti-Hype</strong> · Whale labels are classified, not guaranteed alpha · Not financial advice · Verify on Public Accuracy Ledger';",
        "foot.innerHTML = '<strong>' + esc(i18nT('common.anti_hype')) + '</strong> · ' + esc(i18nT('dash.js.whale_foot'));",
    ),
]

missing = []
for old, new in REPLACEMENTS:
    if old not in text:
        missing.append(old[:80])
        continue
    text = text.replace(old, new, 1)

PATH.write_text(text, encoding="utf-8")
if missing:
    print("WARN missing", len(missing))
    for m in missing[:10]:
        print(" ", m)
else:
    print("OK", len(REPLACEMENTS), "replacements")
