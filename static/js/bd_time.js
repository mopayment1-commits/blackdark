(function () {
  'use strict';

  var SESSION_COOKIE = 'bd_session_tz';
  var DETECTED_COOKIE = 'bd_detected_tz';
  var MAX_AGE = 60 * 60 * 24 * 365;

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

  function formatInstant(iso, opts) {
    opts = opts || {};
    var tz = opts.timezone || 'UTC';
    var lang = opts.lang || (window.BD_I18N && BD_I18N.lang) || 'en';
    try {
      var dt = new Date(iso);
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

  function formatChartUnix(unixSeconds, opts) {
    return formatInstant(new Date(Number(unixSeconds) * 1000).toISOString(), opts || {});
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

  window.BD_TIME = {
    detectBrowserTimezone: detectBrowserTimezone,
    bootDetection: bootDetection,
    formatInstant: formatInstant,
    formatChartUnix: formatChartUnix,
    rememberSessionTimezone: rememberSessionTimezone,
    showTravelMismatch: showTravelMismatch,
    SESSION_COOKIE: SESSION_COOKIE,
    DETECTED_COOKIE: DETECTED_COOKIE
  };

  bootDetection();
})();
