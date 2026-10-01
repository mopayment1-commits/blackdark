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

  /** Allow only http(s) absolute URLs or same-origin path-absolute links.
   *  For HTML attribute interpolation use esc(safeUrl(x)).
   */
  function safeUrl(value) {
    const raw = String(value ?? "").trim();
    if (!raw) return "";
    if (raw.startsWith("/") && !raw.startsWith("//")) {
      if (/[<>"']/.test(raw) || raw.toLowerCase().includes("javascript:")) return "";
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

  /** Hosts used for share/deep-link hrefs in inventoried templates (landing, emotion_tax, API share_urls). */
  const SHARE_NAV_HOSTS = new Set([
    "twitter.com",
    "www.facebook.com",
    "wa.me",
    "t.me",
    "www.reddit.com",
  ]);

  /** Navigation allowlist: same-origin http(s), root-relative path (not //), or known share hosts. */
  function allowedNavigationUrl(value) {
    const raw = String(value ?? "").trim();
    if (!raw) return "";
    if (raw.startsWith("/") && !raw.startsWith("//")) {
      if (/[<>"']/.test(raw) || /javascript:/i.test(raw)) return "";
      return raw;
    }
    try {
      const base = global.location ? global.location.origin : "";
      const u = new URL(raw, base || undefined);
      if (u.protocol !== "http:" && u.protocol !== "https:") return "";
      if (base && u.origin === base) return u.href;
      if (SHARE_NAV_HOSTS.has(u.hostname)) return u.href;
    } catch (_err) {
      /* reject */
    }
    return "";
  }

  function setAnchorHref(el, value) {
    if (!el) return;
    const safe = allowedNavigationUrl(value);
    el.href = safe || "#";
  }

  function assignLocationHref(value) {
    const safe = allowedNavigationUrl(value);
    if (safe) global.location.href = safe;
  }

  function openWindow(value) {
    const safe = allowedNavigationUrl(value);
    if (safe) global.open(safe, "_blank", "noopener");
  }

  function setText(el, value) {
    if (!el) return;
    el.textContent = value == null ? "" : String(value);
  }

  const api = {
    escapeHtml: escapeHtml,
    esc: escapeHtml,
    safeUrl: safeUrl,
    allowedNavigationUrl: allowedNavigationUrl,
    setAnchorHref: setAnchorHref,
    assignLocationHref: assignLocationHref,
    openWindow: openWindow,
    setText: setText,
  };

  global.BDDomSafe = api;
  global.escapeHtml = global.escapeHtml || escapeHtml;
  global.esc = global.esc || escapeHtml;
  global.safeUrl = global.safeUrl || safeUrl;
  global.setText = global.setText || setText;
})(typeof window !== "undefined" ? window : globalThis);
