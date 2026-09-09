(function () {
  'use strict';

  var SESSION_COOKIE = 'bd_session_tz';
  var DETECTED_COOKIE = 'bd_detected_tz';
  var MAX_AGE = 60 * 60 * 24 * 365;
  var _ctxPromise = null;
  var _ctxCache = null;

  function setCookie(name, value) {
    try {
      document.cookie = name + '=' + encodeURIComponent(value) + '; Path=/; Max-Age=' + MAX_AGE + '; SameSite=Lax';
    } catch (_) {}
  }

  function getCookie(name) {
    try {
      var parts = ('; ' + document.cookie).split('; ' + name + '=');
      if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift() || '');
    } catch (_) {}
    return '';
  }

  function detectBrowserTimezone() {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    } catch (_) {
      return 'UTC';
    }
  }

  function bootDetection() {
    var detected = detectBrowserTimezone();
    if (!getCookie(DETECTED_COOKIE)) {
      setCookie(DETECTED_COOKIE, detected);
    }
    return detected;
  }

  function currentLang() {
    try {
      if (window.BD_I18N && BD_I18N.lang) return BD_I18N.lang;
    } catch (_) {}
    return 'en';
  }

  function resolvedTimezone(ctx) {
    var c = ctx || _ctxCache || {};
    return c.resolved_timezone || c.timezone || 'UTC';
  }

  function formatInstant(iso, opts) {
    opts = opts || {};
    var tz = opts.timezone || resolvedTimezone(opts.context) || 'UTC';
    var lang = opts.lang || currentLang();
    if (!iso) return '—';
    try {
      var dt = new Date(iso);
      if (Number.isNaN(dt.getTime())) return String(iso || '').slice(0, 19);
      return new Intl.DateTimeFormat(lang, {
        timeZone: tz,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
        timeZoneName: opts.withContext ? 'short' : undefined
      }).format(dt);
    } catch (_) {
      return String(iso || '').slice(0, 19);
    }
  }

  function formatApiTimestamp(iso, opts) {
    return formatInstant(iso, Object.assign({ withContext: true }, opts || {}));
  }

  function formatChartUnix(unixSeconds, opts) {
    return formatInstant(new Date(Number(unixSeconds) * 1000).toISOString(), Object.assign({ withContext: true }, opts || {}));
  }

  function fetchTimeContext() {
    if (_ctxCache) return Promise.resolve(_ctxCache);
    if (_ctxPromise) return _ctxPromise;
    _ctxPromise = fetch('/api/time/context', { credentials: 'same-origin' })
      .then(function (res) { return res.ok ? res.json() : {}; })
      .then(function (body) {
        _ctxCache = (body && body.time) ? body.time : {};
        return _ctxCache;
      })
      .catch(function () {
        _ctxCache = { resolved_timezone: detectBrowserTimezone() || 'UTC', source: 'detected_fallback' };
        return _ctxCache;
      });
    return _ctxPromise;
  }

  function applyChartTimezone(chart, ctx) {
    if (!chart) return;
    var tz = resolvedTimezone(ctx);
    var lang = currentLang();
    chart.applyOptions({
      localization: {
        locale: lang,
        timeFormatter: function (time) {
          if (typeof time === 'number') {
            return formatChartUnix(time, { timezone: tz, lang: lang, withContext: true });
          }
          return String(time);
        }
      }
    });
  }

  function renderTimestampElements(ctx) {
    var tz = resolvedTimezone(ctx);
    var lang = currentLang();
    document.querySelectorAll('[data-bd-time-iso]').forEach(function (el) {
      var iso = el.getAttribute('data-bd-time-iso');
      el.textContent = formatApiTimestamp(iso, { timezone: tz, lang: lang, withContext: true });
    });
  }

  function rememberSessionTimezone(tz) {
    if (!tz) return;
    setCookie(SESSION_COOKIE, tz);
  }

  function showTravelMismatch(ctx) {
    if (!ctx || !ctx.travel_mismatch) return;
    var el = document.getElementById('tzMismatch');
    if (!el) return;
    el.style.display = 'block';
    el.textContent = 'Your device appears to be in ' + (ctx.detected_timezone || 'another zone') +
      ' while your account timezone is ' + (ctx.account_timezone || 'UTC') + '. Update timezone?';
  }

  function bootPageTimeSurfaces() {
    fetchTimeContext().then(function (ctx) {
      renderTimestampElements(ctx);
      showTravelMismatch(ctx);
    });
  }

  window.BD_TIME = {
    detectBrowserTimezone: detectBrowserTimezone,
    bootDetection: bootDetection,
    formatInstant: formatInstant,
    formatApiTimestamp: formatApiTimestamp,
    formatChartUnix: formatChartUnix,
    fetchTimeContext: fetchTimeContext,
    applyChartTimezone: applyChartTimezone,
    renderTimestampElements: renderTimestampElements,
    rememberSessionTimezone: rememberSessionTimezone,
    showTravelMismatch: showTravelMismatch,
    resolvedTimezone: resolvedTimezone,
    bootPageTimeSurfaces: bootPageTimeSurfaces,
    SESSION_COOKIE: SESSION_COOKIE,
    DETECTED_COOKIE: DETECTED_COOKIE
  };

  bootDetection();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootPageTimeSurfaces);
  } else {
    bootPageTimeSurfaces();
  }
})();
