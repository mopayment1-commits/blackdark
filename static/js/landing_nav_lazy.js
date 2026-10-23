/**
 * Landing-only: defer nav auxiliary scripts until idle (reduces TBT vs eager defer chain).
 */
(function () {
  "use strict";
  function boot() {
    if (!window.BDLazyScript) return;
    const lazy = window.BDLazyScript;
    lazy.whenIdle(function () {
      lazy.load("/static/js/bd_oracle_workspace.js").catch(function (e) { console.debug(e); });
      lazy.load("/static/js/bd_global_nav.js").catch(function (e) { console.debug(e); });
      lazy.load("/static/js/bd_header_account.js").catch(function (e) { console.debug(e); });
      lazy.load("/static/js/bd_site_search.js").catch(function (e) { console.debug(e); });
    }, 4500);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
