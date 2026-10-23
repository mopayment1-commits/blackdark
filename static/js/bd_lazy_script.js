/**
 * Lightweight deferred script loader — keeps parse/execute off the critical path.
 */
(function (global) {
  "use strict";

  const cache = Object.create(null);

  function load(src) {
    if (cache[src]) return cache[src];
    cache[src] = new Promise(function (resolve, reject) {
      const s = document.createElement("script");
      s.src = src;
      s.defer = true;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error("script load failed: " + src)); };
      (document.head || document.documentElement).appendChild(s);
    });
    return cache[src];
  }

  function whenIdle(fn, timeoutMs) {
    const run = function () {
      try { fn(); } catch (e) { console.debug(e); }
    };
    if (typeof global.requestIdleCallback === "function") {
      global.requestIdleCallback(run, { timeout: timeoutMs || 4000 });
    } else {
      global.setTimeout(run, timeoutMs || 2000);
    }
  }

  global.BDLazyScript = { load: load, whenIdle: whenIdle };
})(typeof window !== "undefined" ? window : globalThis);
