/**
 * BLACKDARK — shared DOM escape helpers (DEC-0218).
 * Alias entrypoint for dom_safe.js — escapeHtml + safeUrl (http(s) only).
 */
(function (global) {
  "use strict";

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  /** Allow only http(s) absolute URLs or same-origin path-absolute links. */
  function safeUrl(value) {
    const raw = String(value ?? "").trim();
    if (!raw) return "";
    if (raw.startsWith("/") && !raw.startsWith("//")) {
      if (raw.toLowerCase().includes("javascript:")) return "";
      return raw;
    }
    try {
      const u = new URL(raw, global.location ? global.location.origin : "https://invalid.local");
      if (u.protocol === "http:" || u.protocol === "https:") return u.href;
    } catch (_err) {
      /* reject */
    }
    return "";
  }

  function setText(el, value) {
    if (!el) return;
    el.textContent = value == null ? "" : String(value);
  }

  const api = {
    escapeHtml: escapeHtml,
    esc: escapeHtml,
    safeUrl: safeUrl,
    setText: setText,
  };

  global.BDDomSafe = api;
  global.escapeHtml = global.escapeHtml || escapeHtml;
  global.esc = global.esc || escapeHtml;
  global.safeUrl = global.safeUrl || safeUrl;
  global.setText = global.setText || setText;
})(typeof window !== "undefined" ? window : globalThis);
