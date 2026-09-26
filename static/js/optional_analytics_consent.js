(function () {
  "use strict";

  function readCookie(name) {
    var m = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
    return m ? decodeURIComponent(m[1]) : "";
  }

  window.bdOptionalAnalyticsAllowed = function () {
    if (window.__bdForceEeaSimulate) {
      return readCookie("bd_optional_analytics") === "accept";
    }
    return true;
  };

  async function postJson(url, body) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(body || {}),
    });
  }

  async function initBanner() {
    var banner = document.getElementById("bd-eu-optional-analytics-banner");
    if (!banner) return;
    try {
      var res = await fetch("/api/privacy/optional-analytics-banner", { credentials: "same-origin" });
      if (!res.ok) return;
      var data = await res.json();
      if (!data.show_banner) {
        banner.hidden = true;
        window.__bdEeaVisitor = !!data.eea_visitor;
        window.bdOptionalAnalyticsAllowed = function () {
          return !!data.optional_analytics_allowed;
        };
        return;
      }
      var body = document.getElementById("bd-eu-consent-body");
      if (body) body.textContent = data.body || "";
      banner.hidden = false;
      window.__bdEeaVisitor = true;
      window.bdOptionalAnalyticsAllowed = function () {
        return readCookie("bd_optional_analytics") === "accept";
      };
      document.getElementById("bd-eu-consent-accept")?.addEventListener("click", function () {
        postJson("/api/privacy/optional-analytics-consent", { choice: "accept" }).then(function () {
          banner.hidden = true;
        });
      });
      document.getElementById("bd-eu-consent-reject")?.addEventListener("click", function () {
        postJson("/api/privacy/optional-analytics-consent", { choice: "reject" }).then(function () {
          banner.hidden = true;
        });
      });
      document.getElementById("bd-eu-consent-manage")?.addEventListener("click", function () {
        window.location.href = "/cookies";
      });
      document.getElementById("bd-eu-consent-close")?.addEventListener("click", function () {
        postJson("/api/privacy/optional-analytics-dismiss", {}).then(function () {
          banner.hidden = true;
        });
      });
    } catch (e) {
      console.debug("optional analytics banner init failed", e);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initBanner);
  } else {
    initBanner();
  }
})();
