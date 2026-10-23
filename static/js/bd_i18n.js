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
        enCatalog: parsed.enCatalog && typeof parsed.enCatalog === "object" ? parsed.enCatalog : {},
      };
    } catch (_err) {
      return { lang: "en", catalog: {} };
    }
  }

  const boot = readBoot();
  const enCatalog =
    boot.enCatalog && typeof boot.enCatalog === "object" ? boot.enCatalog : {};

  global.BD_I18N = global.BD_I18N || {
    lang: boot.lang,
    catalog: boot.catalog,
    enCatalog: enCatalog,
    t: function (key, vars) {
      var s = this.catalog && this.catalog[key];
      if (s === undefined || s === null || s === "") {
        s = this.enCatalog && this.enCatalog[key];
      }
      if (s === undefined || s === null || s === "") {
        return key;
      }
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
      try {
        var meta = document.querySelector('meta[name="bd-csrf-token"]');
        var csrf = meta && meta.getAttribute("content");
        var headers = { "Content-Type": "application/json" };
        if (csrf) headers["X-CSRF-Token"] = csrf;
        global.fetch("/api/auth/profile", {
          method: "PATCH",
          credentials: "same-origin",
          headers: headers,
          body: JSON.stringify({ ui_lang: code }),
        }).catch(function (err) {
          console.debug(err);
        });
      } catch (error) {
        console.debug(error);
      }
      var url = new URL(window.location.href);
      url.searchParams.set("lang", code);
      window.location.href = url.toString();
    },
    syncSelect: function () {
      var el = document.getElementById("bdLangTrigger") || document.getElementById("bdLangSelect");
      if (el) el.value = this.lang;
    },
  };

  function hydrateCatalogFromApi() {
    var lang = (global.BD_I18N && global.BD_I18N.lang) || boot.lang || "en";
    return global
      .fetch("/api/i18n/catalog?lang=" + encodeURIComponent(lang), {
        credentials: "same-origin",
      })
      .then(function (res) {
        return res.ok ? res.json() : null;
      })
      .then(function (body) {
        if (body && body.catalog && global.BD_I18N) {
          Object.assign(global.BD_I18N.catalog, body.catalog);
          if (body.lang) global.BD_I18N.lang = body.lang;
        }
      })
      .catch(function (err) {
        console.debug(err);
      });
  }

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
    var keys = global.BD_I18N && global.BD_I18N.catalog
      ? Object.keys(global.BD_I18N.catalog).length
      : 0;
    var finish = function () {
      if (global.BD_I18N) global.BD_I18N.syncSelect();
      try {
        global.dispatchEvent(new CustomEvent("bd-i18n-ready", { detail: { lang: global.BD_I18N.lang } }));
      } catch (e) {
        console.debug(e);
      }
    };
    if (keys < 200) {
      hydrateCatalogFromApi().finally(finish);
    } else {
      finish();
    }
  });
})(typeof window !== "undefined" ? window : globalThis);
