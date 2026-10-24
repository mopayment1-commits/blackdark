/**
 * Global header lens tabs — Prove / Operate / Desk / Room each keep a distinct entry URL.
 */
(function () {
  "use strict";

  var LENS_HREFS = {
    prove: "/dashboard?lens=prove",
    operate: "/dashboard?lens=operate",
    desk: "/dashboard?lens=desk",
    room: "/data-room?lens=room",
  };

  function syncGlobalNavActive(lensId) {
    var key = String(lensId || "").toLowerCase();
    document.querySelectorAll(".site-top-nav a[data-nav-key]").forEach(function (a) {
      var navKey = (a.getAttribute("data-nav-key") || "").toLowerCase();
      var isActive = navKey === key;
      a.classList.toggle("active", isActive);
      if (isActive) {
        a.setAttribute("aria-current", "page");
      } else {
        a.removeAttribute("aria-current");
      }
    });
  }

  function lensHrefForKey(key) {
    return LENS_HREFS[String(key || "").toLowerCase()] || null;
  }

  function wireLensNavLinks() {
    document.querySelectorAll(".site-top-nav a[data-nav-key]").forEach(function (a) {
      var key = (a.getAttribute("data-nav-key") || "").toLowerCase();
      var canonical = lensHrefForKey(key);
      if (canonical) {
        a.setAttribute("href", canonical);
      }
      a.addEventListener("click", function (event) {
        var target = lensHrefForKey(key);
        if (!target) return;
        if (a.getAttribute("href") !== target) {
          a.setAttribute("href", target);
        }
        if (location.pathname === "/dashboard" && (key === "prove" || key === "operate" || key === "desk")) {
          event.preventDefault();
          if (typeof window.applyLens === "function") {
            window.applyLens(key, { persist: true, scroll: true });
          } else {
            location.assign(target);
          }
        }
      });
    });
  }

  function syncFromLocation() {
    if (location.pathname.startsWith("/data-room")) {
      syncGlobalNavActive("room");
      return;
    }
    if (!location.pathname.startsWith("/dashboard")) return;
    var lens = (new URLSearchParams(location.search).get("lens") || "prove").toLowerCase();
    syncGlobalNavActive(lens);
  }

  window.syncGlobalNavActive = syncGlobalNavActive;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      wireLensNavLinks();
      syncFromLocation();
    });
  } else {
    wireLensNavLinks();
    syncFromLocation();
  }
})();
