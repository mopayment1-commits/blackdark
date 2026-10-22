/**
 * Oracle workspace — watchlist, decision log, offline cache, alerts, compare, theme, lang prefs.
 * localStorage only; does not alter server Oracle logic.
 */
(function (global) {
  'use strict';

  const KEYS = {
    watchlist: 'bd_watchlist_v1',
    decisions: 'bd_decision_log_v1',
    lastBySymbol: 'bd_oracle_last_by_symbol_v1',
    watchActions: 'bd_watchlist_last_action_v1',
    alertDedup: 'bd_decision_alert_dedup_v1',
    lang: 'bd_lang_pref_v1',
    theme: 'bd_theme_pref_v1',
  };

  const MAX_DECISIONS = 50;
  const DEFAULT_SYMBOLS = ['BTC', 'ETH', 'SOL'];

  function readJson(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return fallback;
      return JSON.parse(raw);
    } catch (e) {
      return fallback;
    }
  }

  function writeJson(key, val) {
    try {
      localStorage.setItem(key, JSON.stringify(val));
    } catch (e) {
      /* quota */
    }
  }

  function normSym(s) {
    return String(s || '').trim().toUpperCase();
  }

  function mapAction(data) {
    if (!data || typeof data !== 'object') return 'WAIT';
    const raw = data.decision_action || data.model_state || data.verdict || data.action || 'WAIT';
    let action = String(raw).toUpperCase();
    if (action.includes('CONDITION') || action === 'ACT' || action.includes('BUY') || action.includes('BULL')) {
      return 'ACT';
    }
    if (action.includes('ABSTAIN') || action.includes('SELL')) return 'ABSTAIN';
    if (action === 'CAUTION') return 'CAUTION';
    return 'WAIT';
  }

  function scoreFrom(data) {
    const s = data && (data.score ?? data.oracle_score ?? data.confidence);
    const n = Number(s);
    return Number.isFinite(n) ? Math.round(n) : null;
  }

  function certHashFrom(data) {
    const c = data && data.decision_certificate;
    if (c && c.certificate_hash) return String(c.certificate_hash);
    if (data && data.certificate_hash) return String(data.certificate_hash);
    if (data && data.proof && data.proof.certificate_hash) return String(data.proof.certificate_hash);
    return null;
  }

  function ageLabel(data) {
    const age = data && (data.quote_age_sec ?? data.age_sec);
    if (age == null) return null;
    const n = Number(age);
    if (!Number.isFinite(n)) return null;
    if (n < 60) return `${Math.round(n)}s`;
    return `${Math.round(n / 60)}m`;
  }

  const hooks = {
    fetchQuick: null,
    getLang: () => document.documentElement.lang || 'en',
    getUxMode: () => 'beginner',
    applyLang: null,
  };

  function getWatchlist() {
    const list = readJson(KEYS.watchlist, null);
    if (Array.isArray(list) && list.length) return list.map(normSym).filter(Boolean);
    return DEFAULT_SYMBOLS.slice();
  }

  function setWatchlist(symbols) {
    const uniq = [];
    symbols.forEach((s) => {
      const v = normSym(s);
      if (v && !uniq.includes(v)) uniq.push(v);
    });
    writeJson(KEYS.watchlist, uniq);
    return uniq;
  }

  function toggleWatchSymbol(sym) {
    const v = normSym(sym);
    const list = getWatchlist();
    const i = list.indexOf(v);
    if (i >= 0) list.splice(i, 1);
    else list.push(v);
    return setWatchlist(list);
  }

  function saveLastDecision(sym, data) {
    const symbol = normSym(sym || data.symbol || data.asset);
    if (!symbol) return;
    const map = readJson(KEYS.lastBySymbol, {});
    map[symbol] = {
      symbol,
      data,
      saved_at: new Date().toISOString(),
      action: mapAction(data),
      score: scoreFrom(data),
      cert_hash: certHashFrom(data),
    };
    writeJson(KEYS.lastBySymbol, map);
  }

  function getLastDecision(sym) {
    const map = readJson(KEYS.lastBySymbol, {});
    return map[normSym(sym)] || null;
  }

  function appendDecisionLog(sym, data) {
    const symbol = normSym(sym || data.symbol || data.asset);
    const entry = {
      symbol,
      action: mapAction(data),
      score: scoreFrom(data),
      at: new Date().toISOString(),
      cert_hash: certHashFrom(data),
      offline: !!data._offline,
    };
    const log = readJson(KEYS.decisions, []);
    if (log[0] && log[0].symbol === symbol && log[0].action === entry.action) {
      const age = Date.now() - Date.parse(log[0].at || '');
      if (Number.isFinite(age) && age < 60000) return entry;
    }
    log.unshift(entry);
    writeJson(KEYS.decisions, log.slice(0, MAX_DECISIONS));
    return entry;
  }

  function getDecisionLog() {
    return readJson(KEYS.decisions, []);
  }

  function alertDedupKey(symbol, action) {
    return `${normSym(symbol)}:${action}`;
  }

  function maybeAlertDecisionChange(symbol, action) {
    const sym = normSym(symbol);
    const lastMap = readJson(KEYS.watchActions, {});
    const prev = lastMap[sym];
    lastMap[sym] = action;
    writeJson(KEYS.watchActions, lastMap);
    if (!getWatchlist().includes(sym)) return;
    if (!prev || prev === action) return;
    const dedup = readJson(KEYS.alertDedup, {});
    const key = alertDedupKey(sym, `${prev}->${action}`);
    if (dedup[key]) return;
    dedup[key] = Date.now();
    writeJson(KEYS.alertDedup, dedup);
    showDecisionToast(`${sym}: ${prev} → ${action}`);
  }

  let toastTimer = null;
  function showDecisionToast(message) {
    const el = document.getElementById('bdDecisionToast');
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      el.hidden = true;
      el.classList.remove('show');
    }, 8000);
  }

  function onOracleSuccess(sym, data) {
    if (!data || data._offline) return data;
    saveLastDecision(sym, data);
    const entry = appendDecisionLog(sym, data);
    maybeAlertDecisionChange(entry.symbol, entry.action);
    renderWatchlist();
    renderMyDecisions();
    return data;
  }

  function applyOfflineBanner(el, isOffline) {
    if (!el || !isOffline) return;
    const note = el.querySelector('.bd-offline-note');
    if (note) return;
    const p = document.createElement('p');
    p.className = 'bd-offline-note wl-offline-tag';
    p.textContent = 'Offline · last known';
    el.prepend(p);
  }

  function getOfflinePayload(sym) {
    const row = getLastDecision(sym);
    if (!row || !row.data) return null;
    const payload = Object.assign({}, row.data);
    payload._offline = true;
    payload._offline_saved_at = row.saved_at;
    payload.symbol = row.symbol;
    return payload;
  }

  function applyTheme(theme) {
    const t = theme === 'light' ? 'light' : 'dark';
    document.documentElement.dataset.bdTheme = t;
    document.body.classList.toggle('bd-theme-light', t === 'light');
    localStorage.setItem(KEYS.theme, t);
    const btn = document.getElementById('bdThemeToggle');
    if (btn) btn.setAttribute('aria-pressed', t === 'light' ? 'true' : 'false');
    if (btn) btn.textContent = t === 'light' ? '☀' : '☾';
  }

  function initTheme() {
    const saved = localStorage.getItem(KEYS.theme);
    if (saved === 'light' || saved === 'dark') applyTheme(saved);
  }

  function toggleTheme() {
    const cur = document.documentElement.dataset.bdTheme === 'light' ? 'light' : 'dark';
    applyTheme(cur === 'light' ? 'dark' : 'light');
  }

  function initLang() {
    const saved = localStorage.getItem(KEYS.lang) || localStorage.getItem('bd_lang');
    if (!saved) return;
    const sel = document.querySelector('.bd-lang-select select, select#bdLangSelect, #langSelect');
    if (sel && sel.value !== saved) {
      sel.value = saved;
      sel.dispatchEvent(new Event('change', { bubbles: true }));
    }
    document.documentElement.lang = saved;
    if (typeof hooks.applyLang === 'function') hooks.applyLang(saved);
  }

  function persistLang(lang) {
    if (!lang) return;
    localStorage.setItem(KEYS.lang, lang);
    localStorage.setItem('bd_lang', lang);
  }

  function bindLangPersistence() {
    const sel = document.querySelector('.bd-lang-select select, select#bdLangSelect, #langSelect');
    if (!sel || sel.dataset.bdLangBound === '1') return;
    sel.dataset.bdLangBound = '1';
    sel.addEventListener('change', () => persistLang(sel.value));
  }

  function esc(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  async function refreshWatchlistRow(sym) {
    const symbol = normSym(sym);
    const rowEl = document.querySelector(`[data-wl-symbol="${symbol}"]`);
    if (!rowEl) return;
    const status = rowEl.querySelector('.wl-status');
    if (status) status.textContent = '…';
    try {
      if (typeof hooks.fetchQuick !== 'function') throw new Error('no fetch');
      const data = await hooks.fetchQuick(symbol);
      onOracleSuccess(symbol, data);
      const action = mapAction(data);
      const sc = scoreFrom(data);
      if (status) {
        status.textContent = data._offline
          ? `Offline · ${action}${sc != null ? ' · ' + sc : ''}`
          : `${action}${sc != null ? ' · score ' + sc : ''}`;
      }
    } catch (e) {
      const off = getOfflinePayload(symbol);
      if (off) {
        const action = mapAction(off);
        if (status) status.textContent = `Offline · last known · ${action}`;
      } else if (status) status.textContent = 'Unavailable';
    }
  }

  async function renderWatchlist() {
    const listEl = document.getElementById('bdWatchlistRows');
    if (!listEl) return;
    const symbols = getWatchlist();
    listEl.innerHTML = symbols
      .map((sym) => {
        const last = getLastDecision(sym);
        const action = last ? last.action : '—';
        const sc = last && last.score != null ? last.score : '';
        return `<li class="wl-row" data-wl-symbol="${esc(sym)}">
          <strong>${esc(sym)}</strong>
          <span class="wl-status">${esc(action)}${sc !== '' ? ' · ' + esc(String(sc)) : ''}</span>
          <button type="button" class="wl-remove" data-wl-remove="${esc(sym)}" aria-label="Remove ${esc(sym)}">×</button>
        </li>`;
      })
      .join('');
    listEl.querySelectorAll('[data-wl-remove]').forEach((btn) => {
      btn.addEventListener('click', () => {
        toggleWatchSymbol(btn.getAttribute('data-wl-remove'));
        renderWatchlist();
      });
    });
    for (const sym of symbols) {
      await refreshWatchlistRow(sym);
    }
  }

  function renderMyDecisions() {
    const el = document.getElementById('bdMyDecisionsList');
    if (!el) return;
    const log = getDecisionLog();
    if (!log.length) {
      el.innerHTML = '<li class="empty">No saved decisions yet.</li>';
      return;
    }
    el.innerHTML = log
      .map((row) => {
        const hash = row.cert_hash ? `<code style="font-size:.7rem;color:#71717a">${esc(row.cert_hash.slice(0, 12))}…</code>` : '';
        return `<li><strong>${esc(row.symbol)}</strong> · ${esc(row.action)}${row.score != null ? ' · ' + esc(String(row.score)) : ''}
          <span style="color:#71717a;font-size:.75rem"> · ${esc(row.at)}</span>${row.offline ? ' · <em>offline</em>' : ''} ${hash}</li>`;
      })
      .join('');
  }

  function bindWatchlistAdd() {
    const input = document.getElementById('bdWatchlistInput');
    const btn = document.getElementById('bdWatchlistAddBtn');
    if (!btn || btn.dataset.bound === '1') return;
    btn.dataset.bound = '1';
    btn.addEventListener('click', () => {
      const v = normSym(input && input.value);
      if (!v) return;
      const list = getWatchlist();
      if (!list.includes(v)) setWatchlist(list.concat([v]));
      if (input) input.value = '';
      renderWatchlist();
    });
  }

  function openCompareModal() {
    const modal = document.getElementById('bdCompareModal');
    if (!modal) return;
    modal.hidden = false;
    void runCompare();
  }

  function closeCompareModal() {
    const modal = document.getElementById('bdCompareModal');
    if (modal) modal.hidden = true;
  }

  async function runCompare() {
    const box = document.getElementById('bdCompareBody');
    if (!box) return;
    const picks = [];
    document.querySelectorAll('.bd-compare-pick:checked').forEach((el) => picks.push(normSym(el.value)));
    const unique = picks.slice(0, 3);
    if (unique.length < 2) {
      box.innerHTML = '<p class="empty">Select 2–3 symbols.</p>';
      return;
    }
    box.innerHTML = '<p class="loading">Loading…</p>';
    const cards = [];
    for (const sym of unique) {
      let data = null;
      try {
        if (typeof hooks.fetchQuick === 'function') data = await hooks.fetchQuick(sym);
      } catch (e) {
        data = getOfflinePayload(sym);
      }
      if (!data) {
        cards.push(`<div class="bd-compare-card"><h4>${esc(sym)}</h4><p class="empty">No data</p></div>`);
        continue;
      }
      if (!data._offline) onOracleSuccess(sym, data);
      const action = mapAction(data);
      const sc = scoreFrom(data);
      const age = ageLabel(data);
      const off = data._offline ? '<div class="wl-offline-tag">Offline · last known</div>' : '';
      cards.push(`<div class="bd-compare-card"><h4>${esc(sym)}</h4>${off}
        <div class="verdict-lite">${esc(action)}</div>
        <p>Score: ${sc != null ? esc(String(sc)) : '—'}</p>
        <p style="font-size:.75rem;color:#71717a">Age: ${age ? esc(age) : '—'}</p></div>`);
    }
    box.innerHTML = `<div class="bd-compare-grid">${cards.join('')}</div>`;
  }

  function bindCompareUi() {
    document.querySelectorAll('[data-bd-call="openCompare"]').forEach((el) => {
      if (el.dataset.bound === '1') return;
      el.dataset.bound = '1';
      el.addEventListener('click', (e) => {
        e.preventDefault();
        openCompareModal();
      });
    });
    const close = document.getElementById('bdCompareClose');
    if (close && close.dataset.bound !== '1') {
      close.dataset.bound = '1';
      close.addEventListener('click', closeCompareModal);
    }
    const modal = document.getElementById('bdCompareModal');
    if (modal && modal.dataset.bound !== '1') {
      modal.dataset.bound = '1';
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeCompareModal();
      });
    }
    document.querySelectorAll('.bd-compare-pick').forEach((el) => {
      el.addEventListener('change', () => void runCompare());
    });
  }

  function buildShareText(sym, data) {
    const symbol = normSym(sym || data.symbol);
    const action = mapAction(data);
    const sentence = data.decision_sentence || data.conditions_met_review || '';
    const url = `${location.origin}/dashboard?lens=prove&symbol=${encodeURIComponent(symbol)}#trust-pulse`;
    return `BLACKDARK Oracle — ${symbol}: ${action}${sentence ? '\n' + sentence : ''}\n${url}`;
  }

  async function shareDecision(sym, data) {
    const payload = data || getLastDecision(sym)?.data;
    if (!payload) return;
    const text = buildShareText(sym, payload);
    const shareData = { title: 'BLACKDARK decision', text, url: text.split('\n').pop() };
    if (navigator.share) {
      try {
        await navigator.share(shareData);
        return;
      } catch (e) {
        /* fallback */
      }
    }
    const modal = document.getElementById('bdShareDecisionModal');
    const ta = document.getElementById('bdShareDecisionText');
    if (modal && ta) {
      ta.value = text;
      modal.hidden = false;
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(text);
      showDecisionToast('Decision copied to clipboard');
    }
  }

  function bindShareDecision() {
    document.querySelectorAll('[data-bd-share-decision]').forEach((btn) => {
      if (btn.dataset.bound === '1') return;
      btn.dataset.bound = '1';
      btn.addEventListener('click', () => shareDecision());
    });
    const close = document.getElementById('bdShareDecisionClose');
    if (close && close.dataset.bound !== '1') {
      close.dataset.bound = '1';
      close.addEventListener('click', () => {
        const m = document.getElementById('bdShareDecisionModal');
        if (m) m.hidden = true;
      });
    }
    const copy = document.getElementById('bdShareDecisionCopy');
    if (copy && copy.dataset.bound !== '1') {
      copy.dataset.bound = '1';
      copy.addEventListener('click', async () => {
        const ta = document.getElementById('bdShareDecisionText');
        if (ta && navigator.clipboard) {
          await navigator.clipboard.writeText(ta.value);
          showDecisionToast('Copied');
        }
      });
    }
  }

  function scrollToSection(id) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function bindNavShortcuts() {
    document.querySelectorAll('[data-bd-scroll]').forEach((el) => {
      if (el.dataset.bound === '1') return;
      el.dataset.bound = '1';
      el.addEventListener('click', (e) => {
        const id = el.getAttribute('data-bd-scroll');
        if (id) {
          e.preventDefault();
          scrollToSection(id);
        }
      });
    });
  }

  function initThemeToggle() {
    const btn = document.getElementById('bdThemeToggle');
    if (!btn || btn.dataset.bound === '1') return;
    btn.dataset.bound = '1';
    btn.addEventListener('click', toggleTheme);
  }

  let _inited = false;

  function init(options) {
    if (_inited) {
      Object.assign(hooks, options || {});
      return;
    }
    _inited = true;
    Object.assign(hooks, options || {});
    initTheme();
    initLang();
    bindLangPersistence();
    initThemeToggle();
    bindWatchlistAdd();
    bindCompareUi();
    bindShareDecision();
    bindNavShortcuts();
    renderWatchlist();
    renderMyDecisions();
    document.addEventListener('bd-i18n-ready', bindLangPersistence);
  }

  global.BDOracleWorkspace = {
    KEYS,
    init,
    getWatchlist,
    setWatchlist,
    toggleWatchSymbol,
    onOracleSuccess,
    getOfflinePayload,
    mapAction,
    scoreFrom,
    showDecisionToast,
    renderWatchlist,
    renderMyDecisions,
    shareDecision,
    buildShareText,
    persistLang,
    openCompareModal,
    scrollToSection,
  };
})(typeof window !== 'undefined' ? window : globalThis);
