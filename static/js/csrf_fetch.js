/**
 * Attach X-CSRF-Token from server-injected meta (HttpOnly bd_csrf cookie is not readable).
 */
(function (global) {
  "use strict";

  function readCsrfToken() {
    const meta = document.querySelector('meta[name="bd-csrf-token"]');
    const fromMeta = meta && meta.getAttribute("content");
    if (fromMeta) return fromMeta;
    const match = document.cookie.match(/(?:^|;\s*)bd_csrf=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  if (typeof global.fetch !== "function") return;

  const nativeFetch = global.fetch.bind(global);
  global.fetch = function (input, init) {
    const opts = init ? { ...init } : {};
    const headers = new Headers(opts.headers || {});
    const token = readCsrfToken();
    if (token && !headers.has("X-CSRF-Token")) {
      headers.set("X-CSRF-Token", token);
    }
    opts.headers = headers;
    if (!opts.credentials) {
      opts.credentials = "same-origin";
    }
    return nativeFetch(input, opts);
  };
})(typeof window !== "undefined" ? window : globalThis);
