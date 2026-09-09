/**
 * BLACKDARK institutional failure UX — offline, dedup, user actions (ERR-015–018, ERR-035–037).
 */
(function () {
  "use strict";

  var DEDUP_MS = 8000;
  var recent = Object.create(null);
  var bannerEl = null;

  function t(key, fallback) {
    try {
      if (window.BD_I18N && window.BD_I18N[key]) return window.BD_I18N[key];
    } catch (e) {}
    return fallback || key;
  }

  function shouldShow(key) {
    var now = Date.now();
    var last = recent[key] || 0;
    if (now - last < DEDUP_MS) return false;
    recent[key] = now;
    return true;
  }

  function renderBanner(message, action) {
    if (!bannerEl) {
      bannerEl = document.createElement("div");
      bannerEl.id = "bd-global-incident-banner";
      bannerEl.setAttribute("role", "status");
      bannerEl.setAttribute("aria-live", "polite");
      bannerEl.className = "bd-incident-banner";
      document.body.prepend(bannerEl);
    }
    bannerEl.textContent = message;
    if (action === "VIEW_STATUS") {
      var link = document.createElement("a");
      link.href = "/status";
      link.textContent = t("error.view_status", "View status");
      link.className = "bd-incident-link";
      bannerEl.appendChild(document.createTextNode(" "));
      bannerEl.appendChild(link);
    }
  }

  function showScopedError(container, problem) {
    if (!container) return;
    container.setAttribute("role", "alert");
    container.setAttribute("aria-live", "assertive");
    var msg = problem.detail || t(problem.message_key, t("error.widget.unavailable", "This module is temporarily unavailable."));
    container.innerHTML = "";
    var p = document.createElement("p");
    p.className = "bd-scoped-error";
    p.textContent = msg;
    container.appendChild(p);
    var action = problem.user_action || "NONE";
    if (action === "RETRY" && problem.retryable) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "bd-error-action";
      btn.textContent = t("error.action.retry", "Retry");
      btn.addEventListener("click", function () {
        window.location.reload();
      });
      container.appendChild(btn);
    } else if (action === "CHECK_STATUS" || action === "VIEW_STATUS") {
      var a = document.createElement("a");
      a.href = "/status";
      a.className = "bd-error-action";
      a.textContent = t("error.action.check_status", "Check status");
      container.appendChild(a);
    }
  }

  function handleOffline() {
    var key = "offline";
    if (!shouldShow(key)) return;
    renderBanner(t("error.offline", "You appear to be offline. We will reconnect automatically."), "WAIT");
  }

  function handleOnline() {
    if (bannerEl && bannerEl.textContent.indexOf("offline") >= 0) {
      bannerEl.remove();
      bannerEl = null;
    }
  }

  window.addEventListener("offline", handleOffline);
  window.addEventListener("online", handleOnline);

  window.BDFailure = {
    shouldShow: shouldShow,
    renderBanner: renderBanner,
    showScopedError: showScopedError,
    parseProblem: function (resp) {
      if (!resp) return null;
      return {
        detail: resp.detail,
        message_key: resp.message_key,
        user_action: resp.user_action,
        retryable: resp.retryable,
        correlation_id: resp.correlation_id,
        support_reference: resp.support_reference,
      };
    },
    fetchIncidentBanner: function () {
      fetch("/api/failure/incident/banner", { credentials: "same-origin" })
        .then(function (r) {
          return r.json();
        })
        .then(function (body) {
          if (body && body.banner && body.banner.message) {
            renderBanner(body.banner.message, body.banner.user_action);
          }
        })
        .catch(function () {});
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      window.BDFailure.fetchIncidentBanner();
      if (!navigator.onLine) handleOffline();
    });
  } else {
    window.BDFailure.fetchIncidentBanner();
    if (!navigator.onLine) handleOffline();
  }
})();
