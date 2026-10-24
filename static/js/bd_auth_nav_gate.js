/**
 * Anonymous visitors: dashboard links → /login?next=<full path including hash>.
 */
(function (global) {
  "use strict";

  function likelyAuthenticated() {
    try {
      return global.BDSessionHint && global.BDSessionHint.likelyAuthenticated();
    } catch (_err) {
      return false;
    }
  }

  function bindDashboardAuthGate() {
    global.document.addEventListener(
      "click",
      (ev) => {
        if (likelyAuthenticated()) return;
        const anchor = ev.target && ev.target.closest ? ev.target.closest("a[href]") : null;
        if (!anchor) return;
        let url;
        try {
          url = new URL(anchor.href, global.location.href);
        } catch (_err) {
          return;
        }
        if (url.origin !== global.location.origin) return;
        if (!url.pathname.startsWith("/dashboard")) return;
        ev.preventDefault();
        const next = url.pathname + url.search + url.hash;
        global.location.assign("/login?next=" + encodeURIComponent(next));
      },
      true
    );
  }

  if (global.document.readyState === "loading") {
    global.document.addEventListener("DOMContentLoaded", bindDashboardAuthGate);
  } else {
    bindDashboardAuthGate();
  }
})(typeof window !== "undefined" ? window : globalThis);
