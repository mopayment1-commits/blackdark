/** EU optional analytics banner — no-op until preferences API is wired. */
(function () {
  "use strict";
  window.bdOptionalAnalyticsAllowed = function () {
    try {
      var v = document.cookie.match(/(?:^|;\s*)bd_optional_analytics=([^;]+)/);
      return v && decodeURIComponent(v[1]) === "accept";
    } catch (e) {
      return false;
    }
  };
})();
