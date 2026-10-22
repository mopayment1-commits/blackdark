/**
 * Dedupe /oracle/* fetches — one in-flight per symbol+kind; short cooldown after completion.
 */
(function (global) {
  "use strict";

  const inflight = new Map();
  const lastDoneMs = new Map();
  const COOLDOWN_MS = 4000;

  function gateKey(url) {
    try {
      const u = new URL(url, global.location.origin);
      const m = u.pathname.match(/^\/oracle\/([^/]+)(\/quick)?\/?$/i);
      if (!m) return String(url);
      const sym = String(m[1] || "").toUpperCase();
      const kind = m[2] ? "quick" : "full";
      return sym + ":" + kind;
    } catch (_err) {
      return String(url);
    }
  }

  function fetchOracle(url, options) {
    const key = gateKey(url);
    const now = Date.now();
    if (inflight.has(key)) return inflight.get(key);
    const last = lastDoneMs.get(key) || 0;
    if (now - last < COOLDOWN_MS) {
      return Promise.reject(new Error("oracle_fetch_cooldown"));
    }

    const p = global
      .fetch(url, options)
      .then((res) => {
        lastDoneMs.set(key, Date.now());
        return res;
      })
      .catch((err) => {
        lastDoneMs.set(key, Date.now());
        throw err;
      })
      .finally(() => {
        inflight.delete(key);
      });

    inflight.set(key, p);
    return p;
  }

  global.BDOracleFetchGate = {
    fetch: fetchOracle,
    gateKey,
    cooldownMs: COOLDOWN_MS,
  };
})(typeof window !== "undefined" ? window : globalThis);
