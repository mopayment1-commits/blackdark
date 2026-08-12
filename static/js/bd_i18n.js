/**
 * BLACKDARK — language switcher runtime.
 * Boot config is JSON in #bd-i18n-boot (application/json) — not Jinja-in-JS.
 */
(function (global) {
  "use strict";

  function readBoot() {
    const el = document.getElementById("bd-i18n-boot");
    if (!el) return { lang: "en", catalog: {} };
    try {
      const raw = (el.textContent || "").trim();
      if (!raw) return { lang: "en", catalog: {} };
      const parsed = JSON.parse(raw);
      return {
        lang: typeof parsed.lang === "string" ? parsed.lang : "en",
        catalog: parsed.catalog && typeof parsed.catalog === "object" ? parsed.catalog : {},
      };
    } catch (_err) {
      return { lang: "en", catalog: {} };
    }
  }

  const boot = readBoot();

  global.BD_I18N = global.BD_I18N || {
    lang: boot.lang,
    catalog: boot.catalog,
    t: function (key, vars) {
      var s = (this.catalog && this.catalog[key]) || key;
      if (vars) {
        Object.keys(vars).forEach(function (k) {
          s = s.replace(new RegExp("\\{" + k + "\\}", "g"), String(vars[k]));
        });
      }
      return s;
    },
    setLang: function (code) {
      try {
        localStorage.setItem("bd_lang", code);
      } catch (error) {
        console.debug(error);
      }
      document.cookie =
        "bd_lang=" + encodeURIComponent(code) + ";path=/;max-age=31536000;SameSite=Lax";
      var url = new URL(window.location.href);
      url.searchParams.set("lang", code);
      window.location.href = url.toString();
    },
    syncSelect: function () {
      var el = document.getElementById("bdLangSelect");
      if (el) el.value = this.lang;
    },
  };

  document.addEventListener("DOMContentLoaded", function () {
    try {
      var stored = localStorage.getItem("bd_lang");
      var url = new URL(window.location.href);
      if (stored && !url.searchParams.get("lang") && stored !== boot.lang) {
        url.searchParams.set("lang", stored);
        window.location.replace(url.toString());
        return;
      }
    } catch (error) {
      console.debug(error);
    }
    if (global.BD_I18N) global.BD_I18N.syncSelect();
  });
})(typeof window !== "undefined" ? window : globalThis);
