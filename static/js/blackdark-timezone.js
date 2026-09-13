/**
 * BLACKDARK timezone display — charts/UI (TZ-016, TZ-017).
 * Canonical instants remain UTC; this layer localizes display only.
 */
(function (global) {
  'use strict';

  var _resolvedTz = 'UTC';
  var _locale = 'en';

  function setDisplayTimezone(tz) {
    _resolvedTz = tz || 'UTC';
  }

  function setLocale(locale) {
    _locale = locale || 'en';
  }

  async function resolveTimezone(opts) {
    opts = opts || {};
    try {
      var res = await fetch('/api/timezone/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({
          session_preference: opts.session || null,
          detected_browser: (function () {
            try { return Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) { return null; }
          })(),
        }),
      });
      if (res.ok) {
        var data = await res.json();
        _resolvedTz = data.timezone || 'UTC';
      }
    } catch (e) { /* fallback UTC */ }
    return _resolvedTz;
  }

  async function formatInstant(isoUtc) {
    if (!isoUtc) return { label: '', timezone: _resolvedTz };
    try {
      var res = await fetch('/api/timezone/format', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ instant: isoUtc, timezone: _resolvedTz, include_label: true }),
      });
      if (res.ok) return await res.json();
    } catch (e) { /* fall through */ }
    return { label: String(isoUtc).slice(0, 19) + ' UTC', timezone: 'UTC', utc: isoUtc };
  }

  /** Lightweight Charts localization hook (TZ-017) */
  function chartLocalization() {
    return {
      timeFormatter: function (time) {
        var d = new Date(time * 1000);
        try {
          return d.toLocaleString(_locale, { timeZone: _resolvedTz, hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' }) + ' ' + _resolvedTz;
        } catch (e) {
          return d.toISOString().slice(0, 16) + ' UTC';
        }
      },
    };
  }

  function applyChartTimezone(chart) {
    if (chart && typeof chart.applyOptions === 'function') {
      chart.applyOptions({ localization: chartLocalization(), timeScale: { timeVisible: true } });
    }
  }

  function renderLabel(el, isoUtc) {
    if (!el) return;
    formatInstant(isoUtc).then(function (row) {
      el.textContent = row.label || '';
      el.setAttribute('data-timezone', row.timezone || _resolvedTz);
      el.title = (row.utc || isoUtc) + ' UTC canonical';
    });
  }

  global.BlackdarkTimezone = {
    setDisplayTimezone: setDisplayTimezone,
    setLocale: setLocale,
    resolveTimezone: resolveTimezone,
    formatInstant: formatInstant,
    chartLocalization: chartLocalization,
    applyChartTimezone: applyChartTimezone,
    renderLabel: renderLabel,
    getTimezone: function () { return _resolvedTz; },
  };
})(typeof window !== 'undefined' ? window : globalThis);
