
const fmt = (n, d=2) => n == null ? '—' : Number(n).toLocaleString(undefined, { maximumFractionDigits: d });
const vc = v => {
  const u = String(v || 'WAIT').toUpperCase();
  if (u === 'ACT' || u.includes('BUY') || u.includes('BULL')) return 'ACT';
  if (u.includes('SELL') || u.includes('BEAR')) return 'SELL';
  return 'WAIT';
};
let chart, series;
window._lastOracle = null;
window._lastToday = null;

function authHeaders() {
  const t = localStorage.getItem('bd_token');
  return t ? { Authorization: 'Bearer ' + t } : {};
}

async function loadAuth() {
  const tierEl = document.getElementById('userTier');
  const authLink = document.getElementById('authLink');
  const token = localStorage.getItem('bd_token');
  if (!token) return;
  try {
    const res = await fetch('/api/auth/me', { headers: authHeaders() });
    const d = await res.json();
    if (d.authenticated) {
      tierEl.textContent = (d.user.email || '') + ' · ' + (d.tier?.label || d.user.tier);
      authLink.textContent = 'Logout';
      authLink.href = '#';
      authLink.onclick = async e => {
        e.preventDefault();
        await fetch('/api/auth/logout', { method: 'POST', headers: authHeaders() });
        localStorage.removeItem('bd_token');
        location.reload();
      };
    }
  } catch (e) {}
}

async function upgradeTier(tier) {
  try {
    const res = await fetch('/api/billing/checkout', {
      method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ tier: tier || 'pro' }),
    });
    const d = await res.json();
    if (d.url) { location.href = d.url; return; }
  } catch (e) {}
  location.href = '/create-checkout-session?tier=' + (tier || 'pro');
}

function setSymbol(s) {
  document.getElementById('symbol').value = s;
  if (window.BDShell) BDShell.showPane('oracle');
  askOracle();
  loadChart();
}

function applyLang() {
  const root = document.getElementById('htmlRoot');
  root.lang = 'en';
  root.dir = 'ltr';
  const heroSub = document.getElementById('heroSub');
  if (heroSub) heroSub.textContent = 'One clear decision — ACT or WAIT · public verifiable accuracy';
  const askBtn = document.getElementById('askBtn');
  if (askBtn) askBtn.textContent = 'Get Decision';
}

async function loadToday() {
  const sinceList = document.getElementById('sinceList');
  const sinceCount = document.getElementById('sinceCount');
  const pulseGrid = document.getElementById('pulseGrid');
  const pulseSummary = document.getElementById('pulseSummary');
  const attentionList = document.getElementById('attentionList');
  const suggestions = document.getElementById('askSuggestions');
  try {
    const res = await fetch('/api/today', { headers: authHeaders() });
    const d = await res.json();
    window._lastToday = d;
    document.getElementById('todayGreeting').textContent = d.greeting || 'Welcome';
    document.getElementById('todayTagline').textContent = d.tagline || "Here's what changed since you left.";
    const acc = d.ai_accuracy_pct;
    document.getElementById('aiAccuracyChip').textContent =
      acc != null ? `AI Accuracy ${acc}%` : 'AI Accuracy · Ledger';
    const delayed = d.data_status === 'delayed' || (d.market_pulse && d.market_pulse.data_delayed);
    const chip = document.getElementById('dataStatusChip');
    const foot = document.getElementById('footerDataStatus');
    chip.textContent = delayed ? 'DATA DELAYED' : 'LIVE';
    chip.className = 'chip ' + (delayed ? 'delayed' : 'live');
    foot.textContent = delayed ? 'Status: DATA DELAYED' : 'Status: LIVE';

    const since = d.since_you_left || {};
    const items = since.items || [];
    sinceCount.textContent = items.length
      ? `${since.detected_count || items.length} meaningful market changes detected · showing top ${items.length}`
      : (since.empty_message || 'Quiet session');
    sinceList.innerHTML = items.length ? items.map(it => `
      <div class="change-card" onclick="openSinceItem('${(it.asset||'').replace(/'/g,'')}')">
        <strong>${it.asset || ''} · ${it.title || ''}</strong>
        <span class="badge">${it.importance || ''}</span>
        <div class="detail">${it.detail || ''}</div>
      </div>`).join('') : `<div class="empty">${since.empty_message || 'No changes'}</div>`;

    const pulse = d.market_pulse || {};
    pulseGrid.innerHTML = (pulse.states || []).map(s => `
      <div class="pulse-cell"><span>${s.label}</span><strong>${s.value}</strong></div>`).join('');
    pulseSummary.textContent = pulse.summary || '';

    attentionList.innerHTML = (d.needs_your_attention || []).map(it => `
      <div class="attention-card" onclick="openAttention('${(it.asset||'').replace(/'/g,'')}','${(it.cta||'').replace(/'/g,'')}')">
        <strong>${it.title || ''}</strong>
        <span class="badge">${it.priority || ''}</span>
        <div class="detail">${it.reason || ''}</div>
      </div>`).join('');

    suggestions.innerHTML = (d.ask_suggestions || []).map(s =>
      `<button type="button" onclick="prefillAsk(${JSON.stringify(s)})">${s}</button>`).join('');
  } catch (e) {
    sinceList.innerHTML = '<div class="empty">Today feed unavailable — open Oracle on BTC.</div>';
  }
}

function openSinceItem(asset) {
  if (asset && asset !== 'SYS' && asset !== 'ALERT') setSymbol(asset);
  else if (window.BDShell) BDShell.showPane('oracle');
}

function openAttention(asset, cta) {
  const c = (cta || '').toLowerCase();
  if (c.includes('ledger')) { location.href = '/oracle-accuracy'; return; }
  if (c.includes('inbox')) { if (window.BDShell) BDShell.showPane('alerts'); return; }
  if (c.includes('ask')) { document.getElementById('askInput')?.focus(); return; }
  if (asset && !['LEDGER','ASK','ALERT'].includes(asset)) setSymbol(asset);
  else if (window.BDShell) BDShell.showPane('oracle');
}

function prefillAsk(text) {
  const el = document.getElementById('askInput');
  if (el) el.value = text;
  askBlackdark();
}

async function askBlackdark() {
  const input = document.getElementById('askInput');
  const reply = document.getElementById('askReply');
  const message = (input?.value || '').trim();
  if (!message) return;
  reply.style.display = 'block';
  reply.textContent = 'Thinking…';
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ message, history: [] }),
    });
    const d = await res.json().catch(() => ({}));
    if (!res.ok) {
      const seed = window._lastToday?.market_pulse?.explain_seed;
      reply.textContent = seed
        || (d.detail && d.detail.message) || 'Ask requires Pro on some plans — use Get Decision on Oracle, or open the Ledger.';
    } else {
      reply.textContent = d.reply || d.message || d.response || d.answer || JSON.stringify(d).slice(0, 500);
    }
    if (window.BDShell) {
      BDShell.openDock('Ask BLACKDARK', `<div class="ask-reply" style="display:block;margin:0">${reply.textContent}</div>`);
    }
  } catch (e) {
    reply.textContent = 'Assistant unavailable — try Get Decision on BTC.';
  }
}

function explainMarket() {
  const seed = (window._lastToday && window._lastToday.market_pulse && window._lastToday.market_pulse.explain_seed)
    || 'Explain the market in 30 seconds';
  prefillAsk(typeof seed === 'string' && seed.length < 120 ? 'Explain the market in 30 seconds' : 'Explain the market in 30 seconds');
  if (window._lastToday?.market_pulse?.explain_seed && window.BDShell) {
    BDShell.openDock('Market explanation', `<p>${window._lastToday.market_pulse.explain_seed}</p><p class="mute" style="margin-top:.5rem">Ask BLACKDARK for a live expansion.</p>`);
  }
}

function showEvidenceDock() {
  const d = window._lastOracle;
  if (!d) {
    if (window.BDShell) BDShell.openDock('Evidence', '<p class="mute">Run Get Decision first, then open Why / Evidence.</p>');
    return;
  }
  openWhyDock();
}

function openWhyDock() {
  const d = window._lastOracle;
  if (!d) {
    if (window.BDShell) BDShell.openDock('Evidence', '<p class="mute">No decision loaded.</p>');
    return;
  }
  const factors = (d.explanation && d.explanation.top_3_factors) || d.top_3_factors || [];
  const conflict = d.dimension_conflict || {};
  const sig = d.signal_registry || {};
  const html = `
    <p><strong>${d.decision_action || vc(d.verdict)}</strong> · ${d.symbol || ''} · score ${d.opportunity_score ?? '—'}</p>
    <p class="mute" style="margin:.5rem 0">${d.decision_sentence || d.narrative || ''}</p>
    <div style="margin-top:.65rem">${factors.slice(0,5).map(f => {
      const label = f.factor || f.label || f.name || f;
      const src = f.source ? ` · ${f.source}` : '';
      return `<div style="padding:.4rem 0;border-bottom:1px solid var(--line)"><strong>${label}</strong><div class="mute">${f.detail || ''}${src}</div></div>`;
    }).join('') || '<p class="mute">No factor breakdown yet.</p>'}</div>
    ${conflict.veto || conflict.abstain ? `<p style="margin-top:.65rem;color:var(--stop)">Contradiction Veto active</p>` : ''}
    ${sig.signal_id ? `<p class="mute" style="margin-top:.5rem">Signal ${sig.signal_id}</p>` : ''}
    <p class="mute" style="margin-top:.75rem">AI that shows its work · verify on <a href="/oracle-accuracy">Ledger</a></p>`;
  if (window.BDShell) BDShell.openDock('Evidence / Why', html);
}

async function askOracle() {
  const sym = document.getElementById('symbol').value.trim().toUpperCase();
  const box = document.getElementById('oracleBox');
  const el = document.getElementById('oracleContent');
  const mode = document.getElementById('uxMode').value;
  const lang = 'en';
  if (!sym) return;
  box.classList.add('show');
  el.innerHTML = '<div class="loading">Getting your decision…</div>';
  try {
    let res = await fetch('/oracle/' + encodeURIComponent(sym) + '/quick?ux_mode=' + encodeURIComponent(mode) + '&lang=' + encodeURIComponent(lang), { headers: { ...authHeaders(), Accept: 'application/json' } });
    let d = null;
    try { d = await res.json(); } catch (e) { d = null; }
    if (!d || !res.ok) {
      res = await fetch('/oracle/' + encodeURIComponent(sym) + '?ux_mode=' + encodeURIComponent(mode) + '&lang=' + encodeURIComponent(lang), { headers: { ...authHeaders(), Accept: 'application/json' } });
      d = await res.json();
    } else if (mode === 'pro') {
      try {
        const full = await fetch('/oracle/' + encodeURIComponent(sym) + '?ux_mode=' + encodeURIComponent(mode) + '&lang=' + encodeURIComponent(lang), { headers: { ...authHeaders(), Accept: 'application/json' } });
        if (full.ok) d = await full.json();
      } catch (e) {}
    }
    if (!d) throw new Error('fail');
    window._lastOracle = d;
    const sentence = d.decision_sentence || d.narrative || d.oracle || d.action_line || '';
    let action = String(d.decision_action || d.verdict || d.action || 'WAIT').toUpperCase();
    if (action.includes('BUY') || action.includes('BULL') || action === 'ACT') action = 'ACT';
    else action = 'WAIT';
    const truth = d.net_edge_truth || {};
    const half = d.opportunity_half_life || {};
    const sig = d.signal_registry || {};
    let proBlock = '';
    const factors = (d.explanation && d.explanation.top_3_factors) || [];
    const factorBlock = factors.length ? `
      <div style="margin-top:.85rem">
        <div style="font-size:.8rem;color:var(--mute);margin-bottom:.4rem">Why (Top 3)</div>
        ${factors.slice(0,3).map(f => `<div style="font-size:.85rem;padding:.35rem 0;border-bottom:1px solid var(--line)"><strong>${f.factor}</strong> — ${f.detail||''}<div style="color:var(--mute);font-size:.75rem">${f.source||''}</div></div>`).join('')}
      </div>` : '';
    if (mode === 'pro') {
      proBlock = `
      <div class="metrics">
        <div class="metric"><strong>${truth.truth_score ?? '—'}</strong><span>Truth</span></div>
        <div class="metric"><strong>${half.remaining_seconds ?? '—'}s</strong><span>Half-Life</span></div>
        <div class="metric"><strong>${d.market_regime || '—'}</strong><span>Regime</span></div>
        <div class="metric"><strong>${(sig.signal_id || '—').toString().slice(0,10)}</strong><span>Signal</span></div>
      </div>${factorBlock}`;
    } else {
      proBlock = factorBlock;
    }
    let upgradeBlock = '';
    if (d.upgrade_hint) {
      const t = d.upgrade_hint.teaser || {};
      upgradeBlock = `
      <div style="margin-top:1rem;padding:.85rem 1rem;border:1px solid var(--line);border-radius:10px;color:var(--mute);font-size:.85rem">
        ${d.upgrade_hint.message || ''}
        ${t.truth_score != null || t.remaining_seconds != null ? `<div style="margin-top:.35rem">Teaser · Truth ${t.truth_score ?? '—'} · Half-life ${t.remaining_seconds ?? '—'}s</div>` : ''}
        <button class="btn" style="margin-top:.65rem" type="button" onclick="document.getElementById('uxMode').value='pro';askOracle()">Switch to Pro</button>
      </div>`;
    }
    const conflict = d.dimension_conflict || {};
    const vetoBlock = (mode === 'pro' && (conflict.veto || conflict.abstain || (conflict.severity && conflict.severity !== 'none')))
      ? `<div style="margin-top:.75rem;padding:.7rem .9rem;border:1px solid rgba(255,82,82,.35);border-radius:10px;color:#fca5a5;font-size:.85rem">
          Contradiction Veto — ${conflict.veto ? 'WAIT / Do Not Touch' : 'Abstain'}
          ${conflict.severity ? ` · ${conflict.severity}` : ''}
         </div>` : '';
    const proofBlock = d.prediction_id
      ? `<div style="margin-top:.65rem;font-size:.8rem;color:var(--mute)">Proof · prediction_id <code style="color:var(--trust)">${d.prediction_id}</code> · <a href="/oracle-accuracy">Public accuracy</a></div>`
      : '';
    el.innerHTML = `
      <div class="verdict ${action}">${action}</div>
      <div style="color:var(--mute);font-size:.9rem">${d.symbol || sym} · $${fmt(d.price,2)} ·
        <span class="${(d.change_24h||0)>=0?'up':'down'}">${(d.change_24h||0)>=0?'+':''}${fmt(d.change_24h||0,2)}%</span></div>
      <div class="narrative">${sentence || (action === 'ACT' ? `ACT on ${sym}` : `WAIT on ${sym}`)}</div>
      <div class="metrics">
        <div class="metric"><strong>${d.opportunity_score ?? '—'}</strong><span>Score</span></div>
        <div class="metric"><strong>${d.confidence != null ? d.confidence + '%' : '—'}</strong><span>Confidence</span></div>
        <div class="metric"><strong>${d.ux_mode || mode}</strong><span>Mode</span></div>
      </div>
      ${proBlock}${vetoBlock}${proofBlock}${upgradeBlock}
      <div style="margin-top:.65rem"><button type="button" class="btn-secondary" onclick="openWhyDock()">Open Evidence</button>
      <a href="/discipline-mirror" style="margin-left:.5rem;font-size:.85rem">Discipline Mirror</a></div>`;

    const strip = document.getElementById('todayDecisionStrip');
    const body = document.getElementById('todayDecisionBody');
    if (strip && body) {
      strip.style.display = 'block';
      body.innerHTML = `<div class="verdict ${action}" style="font-size:1.4rem">${action}</div>
        <div class="sub">${d.symbol || sym} · score ${d.opportunity_score ?? '—'}</div>
        <div class="narrative" style="margin-top:.5rem">${sentence || ''}</div>`;
    }
  } catch (e) {
    el.innerHTML = '<div class="empty">Could not analyze ' + sym + '</div>';
  }
}

function initChart() {
  const el = document.getElementById('chart');
  if (!el || typeof LightweightCharts === 'undefined') return;
  chart = LightweightCharts.createChart(el, {
    layout: { background: { color: '#10161f' }, textColor: '#8892a6' },
    grid: { vertLines: { color: '#243041' }, horzLines: { color: '#243041' } },
  });
  series = chart.addCandlestickSeries({ upColor: '#00c853', downColor: '#ff5252', borderVisible: false });
  new ResizeObserver(() => chart.applyOptions({ width: el.clientWidth })).observe(el);
}

async function loadChart() {
  if (!series) return;
  const sym = (document.getElementById('symbol').value || 'BTC').toUpperCase();
  const iv = document.getElementById('chartIv').value;
  try {
    const res = await fetch('/api/market/klines?symbol=' + encodeURIComponent(sym) + '&interval=' + encodeURIComponent(iv) + '&limit=100');
    const payload = await res.json();
    const rows = payload.klines || payload || [];
    series.setData(rows.map(k => ({ time: Math.floor(k[0]/1000), open:+k[1], high:+k[2], low:+k[3], close:+k[4] })));
    chart.timeScale().fitContent();
  } catch (e) {}
}

async function loadMarket() {
  const el = document.getElementById('market');
  if (!el) return;
  try {
    const res = await fetch('/api/market/overview');
    const data = await res.json();
    el.innerHTML = (data.assets||[]).slice(0,12).map(a => `
      <div class="card" onclick="setSymbol('${a.symbol}')">
        <strong>${a.symbol}</strong> <span>${vc(a.verdict)}</span>
        <div>$${fmt(a.price,a.price<1?4:2)}</div>
        <div class="${a.change_24h>=0?'up':'down'}">${a.change_24h>=0?'+':''}${fmt(a.change_24h,2)}%</div>
      </div>`).join('');
  } catch (e) { el.innerHTML = '<div class="empty">Unavailable</div>'; }
}

async function loadOI() {
  const el = document.getElementById('oi');
  if (!el) return;
  try {
    const res = await fetch('/api/market/open-interest');
    const data = await res.json();
    const rows = data.assets || [];
    if (!rows.length) { el.innerHTML = '<div class="empty">No OI data</div>'; return; }
    el.innerHTML = '<table><thead><tr><th>Asset</th><th>OI</th><th>Funding</th></tr></thead><tbody>' +
      rows.slice(0,8).map(r => `<tr onclick="setSymbol('${r.asset}')" style="cursor:pointer">
        <td>${r.asset}</td><td>$${fmt(r.open_interest_usd,0)}</td><td>${fmt(r.funding_rate_pct,4)}%</td></tr>`).join('') + '</tbody></table>';
  } catch (e) { el.innerHTML = '<div class="empty">Unavailable</div>'; }
}

async function loadArbitrage(refresh) {
  const el = document.getElementById('arbitrage');
  const stats = document.getElementById('arbStats');
  if (!el) return;
  try {
    const url = refresh ? '/api/arbitrage/scan' : '/api/arbitrage/opportunities?live=true';
    const res = await fetch(url, refresh ? { method: 'POST', headers: authHeaders() } : { headers: authHeaders() });
    const data = await res.json();
    if (res.status === 403) {
      const detail = data.detail || {};
      stats.textContent = detail.message || 'Pro required';
      el.innerHTML = `<div class="empty">${detail.message || 'Upgrade required'}
        <div style="margin-top:.75rem"><button class="btn" onclick="upgradeTier('pro')">Upgrade Pro</button></div></div>`;
      return;
    }
    const c = data.counts || {};
    stats.textContent = `Cross ${c.cross_exchange||0} · Executable ${data.executable_count||0} · Profitable ${data.profitable_count||0}`;
    const opps = data.opportunities || [];
    el.innerHTML = opps.length ? opps.slice(0,6).map(o => {
      const half = o.opportunity_half_life || {};
      const truth = o.net_edge_truth || {};
      const rejected = o.truth_rejected || truth.reject;
      return `<div class="arb-card"><strong>${o.kind_label||o.kind}</strong> ${o.asset||''}
      <div class="${(o.net_profit_usdt||0)>=0?'up':'down'}">${(o.net_profit_usdt||0)>=0?'+':''}$${fmt(Math.abs(o.net_profit_usdt||0),4)}</div>
      <div style="font-size:.75rem;color:var(--mute)">Truth ${truth.truth_score??'—'} · HL ${half.remaining_seconds??o.expected_half_life_seconds??'—'}s${rejected ? ' · REJECTED' : ''}</div></div>`;
    }).join('') : '<div class="empty">No opportunities now</div>';
  } catch (e) { el.innerHTML = '<div class="empty">Scan failed</div>'; }
}

async function loadInbox() {
  const el = document.getElementById('inbox');
  const status = document.getElementById('tgStatus');
  if (!el) return;
  try {
    const res = await fetch('/api/alerts/inbox?limit=12', { headers: authHeaders() });
    const data = await res.json();
    const stats = data.stats || {};
    if (status) status.textContent = `Inbox ${stats.unread||0} unread · works without Telegram`;
    const rows = data.alerts || [];
    el.innerHTML = rows.length ? rows.map(a => `
      <div class="arb-card" style="cursor:pointer" onclick="markInboxRead('${a.id}')">
        <strong>${a.title||'Alert'}</strong>
        <div style="font-size:.85rem;color:var(--mute);margin-top:.25rem">${a.body||''}</div>
      </div>`).join('') : '<div class="empty">No alerts yet</div>';
  } catch (e) { el.innerHTML = '<div class="empty">Inbox unavailable</div>'; }
}

async function markInboxRead(id) {
  if (!id) return;
  try {
    await fetch('/api/alerts/inbox/' + encodeURIComponent(id) + '/read', { method: 'POST', headers: authHeaders() });
    loadInbox();
  } catch (e) {}
}

async function loadWhales(refresh) {
  const el = document.getElementById('whales');
  const foot = document.getElementById('whaleCompliance');
  if (!el) return;
  if (refresh) el.innerHTML = '<div class="loading">Scanning…</div>';
  try {
    const res = await fetch('/api/whale/signal-vs-noise?limit=8');
    const data = await res.json();
    const classified = data.classified || [];
    const stories = data.stories || [];
    const headline = data.headline || (stories[0] || '');
    const headHtml = headline
      ? `<div class="whale-card"><strong>Plain sentence</strong><div style="margin-top:.35rem;font-size:.9rem">${headline}</div></div>`
      : '';
    if (classified.length) {
      el.innerHTML = headHtml + classified.map(a => `
        <div class="whale-card">
          <strong>${a.label||'—'}</strong> · ${a.asset||'—'}
          <div style="font-size:.8rem;color:var(--mute);margin-top:.25rem">${a.sentence||a.class_id||''}</div>
        </div>`).join('');
    } else if (stories.length) {
      el.innerHTML = headHtml + stories.slice(0,8).map(s => `<div class="whale-card">${s}</div>`).join('');
    } else {
      el.innerHTML = '<div class="empty">No whale narratives</div>';
    }
    if (foot) foot.innerHTML = '<strong>Anti-Hype</strong> · Classified labels, not guaranteed alpha';
  } catch (e) { el.innerHTML = '<div class="empty">Unavailable</div>'; }
}

let lastMevShare = '';
async function loadMevReport() {
  const el = document.getElementById('mevResult');
  if (!el) return;
  const asset = (document.getElementById('mevAsset').value || 'ETH').trim();
  const notional = document.getElementById('mevNotional').value || 10000;
  el.innerHTML = '<div class="loading">Building…</div>';
  try {
    const res = await fetch('/api/mev/sandwich-report?asset=' + encodeURIComponent(asset) + '&notional_usd=' + encodeURIComponent(notional));
    const d = await res.json();
    lastMevShare = d.share_text || '';
    const mit = (d.mitigations || []).map(m => `<li style="margin:.25rem 0">${m}</li>`).join('');
    el.innerHTML = `<div class="arb-card"><strong>${d.title||'MEV Report'}</strong> · ${d.asset}
      <div style="margin-top:.4rem">Est. sandwich drag ~${d.estimated_sandwich_bps} bps</div>
      <ul style="margin:.5rem 0 0 1.1rem;font-size:.85rem;color:var(--mute)">${mit}</ul></div>`;
  } catch (e) { el.innerHTML = '<div class="empty">Report unavailable</div>'; }
}
function copyMevShare() {
  if (!lastMevShare) { loadMevReport().then(() => navigator.clipboard.writeText(lastMevShare)); return; }
  navigator.clipboard.writeText(lastMevShare);
}

async function runStealthAdvisor() {
  const el = document.getElementById('stealthResult');
  if (!el) return;
  el.innerHTML = '<div class="loading">Advising…</div>';
  try {
    const res = await fetch('/api/whale/stealth-advisor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({
        asset: (document.getElementById('stealthAsset').value || 'ETH').trim(),
        notional_usd: Number(document.getElementById('stealthNotional').value || 0),
        side: document.getElementById('stealthSide').value || 'buy',
      }),
    });
    const d = await res.json();
    el.innerHTML = `<div class="arb-card"><strong>${d.style||'advisory'}</strong> · ${d.asset} ${d.side}
      <div style="margin-top:.4rem">${d.recommended_slices} slices · urgency ${d.urgency}</div>
      <div style="font-size:.85rem;color:var(--mute);margin-top:.35rem">${d.advice||''}</div>
      <div style="margin-top:.65rem;font-size:.72rem;color:var(--mute)"><strong>Anti-Hype</strong> · ${d.disclaimer||''}</div></div>`;
  } catch (e) { el.innerHTML = '<div class="empty">Advisor unavailable</div>'; }
}

let portfolioAssets = [];
function addPortfolioAsset() {
  const symbol = (document.getElementById('pfSym').value || '').toUpperCase().trim();
  const amount = Number(document.getElementById('pfAmt').value || 0);
  if (!symbol || !(amount > 0)) return;
  portfolioAssets.push({ symbol, amount });
  document.getElementById('pfSym').value = '';
  document.getElementById('pfAmt').value = '';
  renderPortfolioList();
}
function renderPortfolioList() {
  const el = document.getElementById('portfolioList');
  if (!el) return;
  if (!portfolioAssets.length) { el.textContent = ''; return; }
  el.innerHTML = portfolioAssets.map((a,i) =>
    `${a.symbol}: ${a.amount} <button class="btn-secondary" style="padding:.15rem .4rem;font-size:.7rem" onclick="portfolioAssets.splice(${i},1);renderPortfolioList()">×</button>`
  ).join(' · ');
}
async function analyzePortfolio() {
  const el = document.getElementById('portfolioResult');
  if (!portfolioAssets.length) { el.innerHTML = '<div class="empty">Add at least one holding</div>'; return; }
  el.innerHTML = '<div class="loading">Analyzing…</div>';
  try {
    const res = await fetch('/portfolio/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(portfolioAssets),
    });
    const d = await res.json();
    el.innerHTML = `<div class="arb-card"><strong>Portfolio AI</strong>
      <div style="margin-top:.4rem">${d.plain_language || d.summary || ''}</div></div>`;
  } catch (e) { el.innerHTML = '<div class="empty">Portfolio AI unavailable</div>'; }
}

async function loadTgStatus() {
  const el = document.getElementById('tgStatus');
  if (!el) return;
  try {
    const res = await fetch('/api/alerts/telegram/status');
    const d = await res.json();
    el.textContent = d.bot_token_set ? 'Telegram bot configured' : 'Set TELEGRAM_BOT_TOKEN to enable Telegram alerts';
  } catch (e) {}
}

async function testTelegram() {
  try {
    const res = await fetch('/api/alerts/telegram/test', { method: 'POST', headers: authHeaders() });
    const d = await res.json();
    alert(d.message || (d.success ? 'Sent!' : 'Failed'));
  } catch (e) { alert('Test failed'); }
}

async function loadAlertsGenerosity() {
  const el = document.getElementById('alertsGenerosity');
  if (!el) return;
  try {
    const res = await fetch('/api/alerts/generosity');
    const d = await res.json();
    const bd = d.blackdark || {};
    el.innerHTML = `<strong>${d.title || 'Alert generosity'}</strong><br>${bd.in_app_inbox || ''}`;
  } catch (e) {}
}

async function loadSignals() {
  const el = document.getElementById('signalsPane');
  if (!el) return;
  try {
    const res = await fetch('/api/oracle/signals');
    const d = await res.json();
    const rows = d.signals || d.items || d.registry || [];
    if (!rows.length) {
      el.innerHTML = '<div class="empty">Signal Registry is quiet — decisions still attach proof when available.</div>';
      return;
    }
    el.innerHTML = rows.slice(0,12).map(s => `
      <div class="arb-card"><strong>${s.label || s.signal_id || s.type || 'Signal'}</strong>
      <div class="sub">${s.definition || s.source || ''}</div>
      <div style="font-size:.75rem;color:var(--mute)">weight ${s.weight ?? '—'} · hit ${(s.performance&&s.performance.hit_rate)!=null?s.performance.hit_rate:'—'}</div></div>`).join('');
  } catch (e) {
    el.innerHTML = '<div class="empty">Signals API unavailable</div>';
  }
}

function applyAudienceFromQuery() {
  const params = new URLSearchParams(location.search);
  const aud = (params.get('audience') || localStorage.getItem('bd_audience') || '').toLowerCase();
  const hash = (location.hash || '').toLowerCase();
  if (aud) localStorage.setItem('bd_audience', aud);
  const mode = document.getElementById('uxMode');
  if (mode && (aud === 'pro' || aud === 'whale' || aud === 'fund')) mode.value = 'pro';
  const banner = document.getElementById('audienceBanner');
  if (banner) {
    if (aud === 'whale') { banner.style.display = 'block'; banner.textContent = 'Whale mode · Stealth + MEV in Portfolio'; }
    else if (aud === 'fund') { banner.style.display = 'block'; banner.innerHTML = 'Fund mode · <a href="/b2b#fund-terminal">Emerging Fund Terminal</a>'; }
    else if (aud === 'pro') { banner.style.display = 'block'; banner.textContent = 'Pro mode · Truth + Half-Life + Evidence'; }
    else if (aud === 'retail') { banner.style.display = 'block'; banner.textContent = 'Retail mode · One clear ACT / WAIT decision'; }
  }
  if (aud === 'fund' && !hash) setTimeout(() => { location.href = '/b2b#fund-terminal'; }, 200);
  if (hash === '#stealth' || hash === '#mev' || aud === 'whale') {
    setTimeout(() => { if (window.BDShell) BDShell.showPane('portfolio'); }, 200);
  } else if (hash === '#portfolio') {
    setTimeout(() => { if (window.BDShell) BDShell.showPane('portfolio'); }, 200);
  } else if (hash === '#oracle') {
    setTimeout(() => { if (window.BDShell) BDShell.showPane('oracle'); }, 200);
  }
}

function boot() {
  loadAuth();
  applyLang();
  applyAudienceFromQuery();
  loadToday();
  document.getElementById('explainMarketBtn')?.addEventListener('click', explainMarket);
  document.getElementById('showEvidenceBtn')?.addEventListener('click', showEvidenceDock);
  document.addEventListener('bd:pane', (e) => {
    if (e.detail?.id === 'signals') loadSignals();
    if (e.detail?.id === 'today') loadToday();
  });
  loadMarket();
  loadOI();
  loadArbitrage(false);
  loadWhales(false);
  loadTgStatus();
  loadAlertsGenerosity();
  loadInbox();
  loadSignals();
  setInterval(loadToday, 120000);
  setInterval(loadMarket, 60000);
  setInterval(loadInbox, 90000);
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
else boot();
