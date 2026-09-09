/**
 * BLACKDARK institutional failure UX — offline, dedup, user actions (ERR-015–018, ERR-035–037).
 */
(function () {
  "use strict";

  var DEDUP_MS = 8000;
  var recent = Object.create(null);
  var bannerEl = null;
  var liveRegionEl = null;

  function t(key, fallback) {
    try {
      if (window.BD_I18N && window.BD_I18N[key]) return window.BD_I18N[key];
    } catch (e) {}
    return fallback || key;
  }

  function ensureLiveRegion() {
    if (liveRegionEl) return liveRegionEl;
    liveRegionEl = document.createElement("div");
    liveRegionEl.id = "bd-a11y-live-region";
    liveRegionEl.setAttribute("role", "status");
    liveRegionEl.setAttribute("aria-live", "polite");
    liveRegionEl.setAttribute("aria-atomic", "true");
    liveRegionEl.className = "sr-only";
    liveRegionEl.style.cssText = "position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0";
    document.body.appendChild(liveRegionEl);
    return liveRegionEl;
  }

  function shouldShow(key) {
    var now = Date.now();
    var last = recent[key] || 0;
    if (now - last < DEDUP_MS) return false;
    recent[key] = now;
    return true;
  }

  function announce(message, key) {
    if (!message) return;
    var dedupKey = key || message;
    if (!shouldShow(dedupKey)) return;
    var region = ensureLiveRegion();
    region.textContent = "";
    window.setTimeout(function () {
      region.textContent = message;
    }, 30);
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
    bannerEl.textContent = "";
    var text = document.createElement("span");
    text.textContent = message;
    bannerEl.appendChild(text);
    if (action === "VIEW_STATUS") {
      var link = document.createElement("a");
      link.href = "/status";
      link.textContent = t("error.view_status", "View status");
      link.className = "bd-incident-link";
      bannerEl.appendChild(document.createTextNode(" "));
      bannerEl.appendChild(link);
    }
    announce(message, "banner:" + message);
  }

  function showScopedError(container, problem) {
    if (!container) return;
    container.setAttribute("role", "alert");
    container.setAttribute("aria-live", "assertive");
    container.classList.add("bd-failure-scope");
    var msg =
      problem.detail ||
      t(problem.message_key, t("error.widget.unavailable", "This module is temporarily unavailable."));
    container.innerHTML = "";
    var p = document.createElement("p");
    p.className = "bd-scoped-error";
    p.id = container.id ? container.id + "-error" : "bd-scoped-error-msg";
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
    announce(msg, "scope:" + (problem.message_key || msg));
  }

  function handleWidgetFailure(container, opts) {
    opts = opts || {};
    showScopedError(container, {
      detail: opts.detail || null,
      message_key: opts.message_key || "error.widget.unavailable",
      user_action: opts.user_action || "RETRY",
      retryable: opts.retryable !== false,
    });
  }

  function showFieldError(input, message) {
    if (!input) return;
    var fieldId = input.id || input.name || "field";
    var errId = fieldId + "-error";
    var existing = document.getElementById(errId);
    if (!existing) {
      existing = document.createElement("span");
      existing.id = errId;
      existing.className = "bd-field-error";
      existing.setAttribute("role", "alert");
      input.parentNode && input.parentNode.appendChild(existing);
    }
    existing.textContent = message;
    input.setAttribute("aria-invalid", "true");
    var described = input.getAttribute("aria-describedby") || "";
    if (described.indexOf(errId) < 0) {
      input.setAttribute("aria-describedby", described ? described + " " + errId : errId);
    }
    announce(message, "field:" + fieldId);
  }

  function clearFieldError(input) {
    if (!input) return;
    input.removeAttribute("aria-invalid");
    var fieldId = input.id || input.name || "field";
    var errId = fieldId + "-error";
    var existing = document.getElementById(errId);
    if (existing) existing.remove();
  }

  function focusFirstInvalid(form) {
    if (!form) return null;
    var invalid = form.querySelector("[aria-invalid='true'], .bd-field-error");
    if (invalid) {
      var target = invalid.tagName === "INPUT" || invalid.tagName === "SELECT" || invalid.tagName === "TEXTAREA"
        ? invalid
        : form.querySelector("[aria-invalid='true']");
      if (target && target.focus) {
        target.focus();
        return target;
      }
    }
    return null;
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
    handleWidgetFailure: handleWidgetFailure,
    showFieldError: showFieldError,
    clearFieldError: clearFieldError,
    focusFirstInvalid: focusFirstInvalid,
    announce: announce,
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
