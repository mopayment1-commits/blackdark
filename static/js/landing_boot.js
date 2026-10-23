/**
 * Landing entry — minimal parse cost; loads landing_boot_main.js on idle or first interaction.
 */
(function () {
  "use strict";

  var mainPromise = null;

  function ensureMain() {
    if (!mainPromise) {
      if (!window.BDLazyScript) {
        mainPromise = Promise.reject(new Error("BDLazyScript missing"));
        return mainPromise;
      }
      var lazy = window.BDLazyScript;
      mainPromise = lazy
        .load("/static/js/dom_escape.js?v=20261007-setAnchorHref")
        .then(function () { return lazy.load("/static/js/public_decision_map.js"); })
        .then(function () { return lazy.load("/static/js/csrf_fetch.js"); })
        .then(function () { return lazy.load("/static/js/landing_boot_main.js"); });
    }
    return mainPromise;
  }

  function forward(name) {
    return function () {
      var args = arguments;
      return ensureMain().then(function () {
        var fn = window["__landing_" + name];
        if (typeof fn === "function") {
          return fn.apply(null, args);
        }
      });
    };
  }

  function applyLandingPulseSSRMinimal() {
    var el = document.getElementById("landing-pulse-ssr");
    if (!el) return false;
    try {
      var p = JSON.parse(el.textContent || "{}");
      if (!p || (!p.symbol && !p.action)) return false;
      var act = p.action || p.verdict || "WAIT";
      var actionEl = document.getElementById("lpAction");
      if (actionEl) {
        actionEl.textContent = act;
        var css = act === "CONDITIONS MET" ? "WAIT" : String(act).replace(/\s+/g, "_");
        actionEl.className = "tp-mini-action bd-tp-action " + css;
      }
      var symEl = document.getElementById("lpSym");
      if (symEl && p.symbol) {
        var price = p.price != null ? " · $" + Number(p.price).toLocaleString(undefined, { maximumFractionDigits: 2 }) : "";
        symEl.textContent = String(p.symbol).toUpperCase() + price;
      }
      var sent = document.getElementById("lpSentence");
      if (sent && p.sentence) sent.textContent = p.sentence;
      return true;
    } catch (e) {
      console.debug(e);
      return false;
    }
  }

  window.consultOracle = forward("consultOracle");
  window.tryOracleFree = forward("tryOracleFree");
  window.applyAudience = forward("applyAudience");
  window.joinWaitlist = forward("joinWaitlist");
  window.openCompare = function () {
    var lazy = window.BDLazyScript;
    var loadWs = lazy ? lazy.load("/static/js/bd_oracle_workspace.js") : Promise.resolve();
    return loadWs.then(function () { return forward("openCompare")(); });
  };

  function warmMain() {
    ensureMain().catch(function (e) { console.debug(e); });
  }

  function scheduleWarm() {
    if (!window.BDLazyScript) return;
    window.BDLazyScript.whenIdle(warmMain, 5500);
    ["pointerdown", "keydown", "touchstart", "scroll"].forEach(function (ev) {
      window.addEventListener(ev, warmMain, { once: true, passive: true });
    });
  }

  function onReady() {
    requestAnimationFrame(function () {
      applyLandingPulseSSRMinimal();
      scheduleWarm();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady, { once: true });
  } else {
    onReady();
  }
})();
