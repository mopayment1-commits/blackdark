/**
 * Client hint for HttpOnly bd_token session — avoids /api/auth/me when clearly logged out.
 */
(function (global) {
  "use strict";

  function likelyAuthenticated() {
    try {
      return document.cookie.split(";").some((part) => {
        const t = part.trim();
        if (!t.startsWith("bd_token=")) return false;
        const val = t.slice("bd_token=".length);
        return val.length > 12;
      });
    } catch (_err) {
      return false;
    }
  }

  global.BDSessionHint = { likelyAuthenticated };
})(typeof window !== "undefined" ? window : globalThis);
