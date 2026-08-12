/**
 * BLACKDARK — CSP-safe event binder (DEC-0217).
 * Replaces inline on* handlers with data-bd-* attributes so script-src
 * can drop 'unsafe-inline' under nonce + strict-dynamic.
 *
 * Supported attributes:
 *   data-bd-call="fnName"              → window.fnName()
 *   data-bd-args='["a",1,true]'        → JSON args (optional)
 *   data-bd-prevent="1"                → preventDefault + return false semantics
 *   data-bd-keydown-call="fnName"      → call on Enter (or Enter/Space if data-bd-keys="enter space")
 *   data-bd-change-call="fnName"       → change handler; passes element value as first arg if data-bd-pass-value="1"
 *   data-bd-submit-call="fnName"       → submit; passes event as first arg
 *   data-bd-input-call="fnName"        → input handler
 */
(function () {
  "use strict";

  function parseArgs(el) {
    const raw = el.getAttribute("data-bd-args");
    if (!raw) return [];
    try {
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (_err) {
      return [];
    }
  }

  function resolveCall(name) {
    if (!name || typeof name !== "string") return null;
    if (name === "window.print") return function () { window.print(); };
    if (name.indexOf(".") !== -1) {
      const parts = name.split(".");
      let cur = window;
      for (let i = 0; i < parts.length; i++) {
        if (cur == null) return null;
        cur = cur[parts[i]];
      }
      return typeof cur === "function" ? cur : null;
    }
    const fn = window[name];
    return typeof fn === "function" ? fn : null;
  }

  function invoke(el, event, attr) {
    const name = el.getAttribute(attr);
    const fn = resolveCall(name);
    if (!fn) return;
    if (el.getAttribute("data-bd-prevent") === "1" && event && event.preventDefault) {
      event.preventDefault();
    }
    const args = parseArgs(el);
    if (el.getAttribute("data-bd-pass-event") === "1") {
      fn.apply(el, [event].concat(args));
      return;
    }
    if (el.getAttribute("data-bd-pass-value") === "1") {
      fn.apply(el, [el.value].concat(args));
      return;
    }
    fn.apply(el, args);
  }

  document.addEventListener(
    "click",
    function (event) {
      const el = event.target && event.target.closest
        ? event.target.closest("[data-bd-call]")
        : null;
      if (!el) return;
      invoke(el, event, "data-bd-call");
    },
    false
  );

  document.addEventListener(
    "submit",
    function (event) {
      const el = event.target && event.target.closest
        ? event.target.closest("[data-bd-submit-call]")
        : null;
      if (!el) return;
      el.setAttribute("data-bd-pass-event", "1");
      el.setAttribute("data-bd-prevent", "1");
      invoke(el, event, "data-bd-submit-call");
    },
    false
  );

  document.addEventListener(
    "change",
    function (event) {
      const el = event.target && event.target.closest
        ? event.target.closest("[data-bd-change-call]")
        : null;
      if (!el) return;
      invoke(el, event, "data-bd-change-call");
    },
    false
  );

  document.addEventListener(
    "input",
    function (event) {
      const el = event.target && event.target.closest
        ? event.target.closest("[data-bd-input-call]")
        : null;
      if (!el) return;
      invoke(el, event, "data-bd-input-call");
    },
    false
  );

  document.addEventListener(
    "keydown",
    function (event) {
      const el = event.target && event.target.closest
        ? event.target.closest("[data-bd-keydown-call]")
        : null;
      if (!el) return;
      const keys = (el.getAttribute("data-bd-keys") || "enter").toLowerCase().split(/\s+/);
      const map = {
        enter: event.key === "Enter",
        space: event.key === " " || event.key === "Spacebar",
      };
      const hit = keys.some(function (k) { return map[k]; });
      if (!hit) return;
      invoke(el, event, "data-bd-keydown-call");
    },
    false
  );
})();
