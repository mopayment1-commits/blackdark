/**
 * Attach X-CSRF-Token from bd_csrf cookie to same-origin fetch calls.
 */
(function (global) {
  "use strict";

  function readCsrfCookie() {
    const match = document.cookie.match(/(?:^|;\s*)bd_csrf=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  if (typeof global.fetch !== "function") return;

  const nativeFetch = global.fetch.bind(global);
  global.fetch = function (input, init) {
    const opts = init ? { ...init } : {};
    const headers = new Headers(opts.headers || {});
    const token = readCsrfCookie();
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
