/**
 * Profile & billing page — save profile, avatar, MFA, logout-all.
 * Exposes handlers for data-bd-call (csp_events.js).
 */
(function () {
  "use strict";

  const dom = window.BDDomSafe || {};
  const esc = dom.esc || dom.escapeHtml || function (v) {
    return String(v ?? "");
  };
  const assignLocationHref =
    dom.assignLocationHref ||
    function (value) {
      if (value) window.location.href = value;
    };

  function tx(key, vars) {
    if (window.BD_I18N && typeof window.BD_I18N.t === "function") {
      return window.BD_I18N.t(key, vars);
    }
    return key;
  }

  function authHeaders() {
    return { "Content-Type": "application/json" };
  }

  function setMsg(id, text, ok) {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = "msg " + (ok ? "ok" : "error");
    el.textContent = text;
  }

  const PLAN_RANK = { free: 0, pro: 1, elite: 2, whale: 2, desk: 2, quant: 3, institutional: 4, inst: 4 };

  function publicPlanName(tierId) {
    const t = String(tierId || "free").toLowerCase();
    if (t === "free" || t === "proof" || t === "proof_pass") return tx("profile.plan.free");
    if (t === "pro" || t === "decision_pro" || t === "plus") return tx("profile.plan.plus");
    if (t === "elite" || t === "whale" || t === "desk" || t === "decision_desk") return tx("profile.plan.pro");
    if (t === "quant" || t === "institutional" || t === "inst") return tx("profile.plan.enterprise");
    return tx("profile.plan.free");
  }

  function syncPlanActions(tierId) {
    const rank = PLAN_RANK[String(tierId || "free").toLowerCase()] ?? 0;
    const plus = document.getElementById("btnUpgradePlus");
    const pro = document.getElementById("btnUpgradePro");
    const ent = document.getElementById("btnEnterprise");
    if (plus) plus.style.display = rank < 1 ? "" : "none";
    if (pro) pro.style.display = rank < 2 ? "" : "none";
    if (ent) ent.style.display = rank < 4 ? "" : "none";
  }

  function fillProfileFields(d) {
    const p = d.profile || {};
    const u = d.user || {};
    document.getElementById("name").value = p.name || "";
    document.getElementById("username").value = p.username || "";
    document.getElementById("ui_lang").value = p.ui_lang || "en";
    document.getElementById("ux_mode_pref").value = p.ux_mode_pref || "beginner";
    document.getElementById("timezone").value = p.timezone || "UTC";
    document.getElementById("telegram_chat_id").value = p.telegram_chat_id || "";
    document.getElementById("avatarImg").src =
      (p.avatar_url || "/api/auth/avatar/" + u.id + ".svg") + "?t=" + Date.now();
    const emailSuffix = p.email_verified ? tx("profile.email_verified") : tx("profile.email_pending");
    document.getElementById("emailLine").textContent = u.email + " · " + emailSuffix;
    document.getElementById("verifyHint").textContent = p.email_verified
      ? tx("profile.verify_ok")
      : tx("profile.verify_pending");
    const tierId = String((d.tier && (d.tier.tier || d.tier.id)) || u.tier || "free").toLowerCase();
    const planLabel = publicPlanName(tierId);
    const mfaPill =
      d.mfa && d.mfa.enabled
        ? '<span class="pill">' + esc(tx("profile.mfa_on_pill")) + "</span>"
        : '<span class="pill">' + esc(tx("profile.mfa_off_pill")) + "</span>";
    document.getElementById("planPills").innerHTML =
      '<span class="pill">' + esc(planLabel) + "</span>" + mfaPill;
    document.getElementById("mfaHint").textContent =
      d.mfa && d.mfa.enabled ? tx("profile.mfa_on_hint") : tx("profile.mfa_off_hint");
    const sub = d.subscription && d.subscription.status;
    const planCurrent = document.getElementById("planCurrent");
    if (planCurrent) {
      planCurrent.textContent = sub
        ? tx("profile.current_plan_status", { plan: planLabel, status: sub })
        : tx("profile.current_plan", { plan: planLabel });
    }
    syncPlanActions(tierId);
    return tierId;
  }

  function showWelcomeMessage() {
    if (new URLSearchParams(location.search).get("verified") === "1") {
      setMsg("profileMsg", tx("profile.msg.email_verified"), true);
    }
    const welcome = new URLSearchParams(location.search).get("welcome");
    const planQ = new URLSearchParams(location.search).get("plan");
    if (welcome !== "1") return;
    if (planQ === "pro") setMsg("profileMsg", tx("profile.msg.welcome_plus"), true);
    else if (planQ === "free") setMsg("profileMsg", tx("profile.msg.welcome_free"), true);
    else setMsg("profileMsg", tx("profile.msg.welcome_default"), true);
  }

  async function load() {
    const res = await fetch("/api/auth/me", { headers: authHeaders(), credentials: "same-origin" });
    const d = await res.json();
    if (!d.authenticated) {
      const tpl = document.getElementById("profileGateTpl");
      document.getElementById("gate").innerHTML = tpl ? tpl.innerHTML : tx("profile.gate_prefix");
      return;
    }
    document.getElementById("gate").style.display = "none";
    document.getElementById("app").style.display = "grid";
    fillProfileFields(d);
    showWelcomeMessage();
  }

  async function saveProfile() {
    const res = await fetch("/api/auth/profile", {
      method: "PATCH",
      headers: authHeaders(),
      credentials: "same-origin",
      body: JSON.stringify({
        name: document.getElementById("name").value,
        username: document.getElementById("username").value,
        ui_lang: document.getElementById("ui_lang").value,
        ux_mode_pref: document.getElementById("ux_mode_pref").value,
        timezone: document.getElementById("timezone").value,
        telegram_chat_id: document.getElementById("telegram_chat_id").value,
      }),
    });
    const d = await res.json();
    setMsg(
      "profileMsg",
      res.ok ? tx("profile.msg.saved") : d.detail || tx("profile.msg.save_failed"),
      res.ok
    );
    if (res.ok) load();
  }

  async function uploadAvatar() {
    const f = document.getElementById("avatarFile").files[0];
    if (!f) return setMsg("profileMsg", tx("profile.msg.choose_file"), false);
    const fd = new FormData();
    fd.append("file", f);
    const res = await fetch("/api/auth/avatar", { method: "POST", body: fd, credentials: "same-origin" });
    const d = await res.json();
    setMsg(
      "profileMsg",
      res.ok ? tx("profile.msg.avatar_updated") : d.detail || tx("profile.msg.upload_failed"),
      res.ok
    );
    if (res.ok) load();
  }

  async function resetAvatar() {
    const res = await fetch("/api/auth/avatar", {
      method: "DELETE",
      headers: authHeaders(),
      credentials: "same-origin",
    });
    setMsg("profileMsg", res.ok ? tx("profile.msg.initials_avatar") : tx("profile.msg.failed"), res.ok);
    if (res.ok) load();
  }

  async function changePassword() {
    const res = await fetch("/api/auth/change-password", {
      method: "POST",
      headers: authHeaders(),
      credentials: "same-origin",
      body: JSON.stringify({
        current_password: document.getElementById("current_password").value,
        new_password: document.getElementById("new_password").value,
      }),
    });
    const d = await res.json();
    if (res.ok) {
      try {
        localStorage.removeItem("bd_token");
        localStorage.removeItem("token");
      } catch (_e) {
        /* ignore */
      }
    }
    setMsg("secMsg", res.ok ? tx("profile.msg.password_updated") : d.detail || tx("profile.msg.failed"), res.ok);
  }

  async function resendVerify() {
    const res = await fetch("/api/auth/resend-verification", {
      method: "POST",
      headers: authHeaders(),
      credentials: "same-origin",
    });
    const d = await res.json();
    if (d.debug_link) console.info(d.debug_link);
    setMsg("secMsg", d.message || d.detail || tx("profile.msg.sent"), res.ok);
  }

  async function enrollMfa() {
    const res = await fetch("/api/auth/mfa/enroll", {
      method: "POST",
      headers: authHeaders(),
      credentials: "same-origin",
    });
    const d = await res.json();
    document.getElementById("mfaEnrollBox").textContent = res.ok
      ? tx("profile.msg.mfa_scan_prefix") + " " + (d.secret || d.otpauth_url || JSON.stringify(d, null, 2))
      : d.detail || tx("profile.msg.enroll_failed");
  }

  async function confirmMfa() {
    const res = await fetch("/api/auth/mfa/confirm", {
      method: "POST",
      headers: authHeaders(),
      credentials: "same-origin",
      body: JSON.stringify({ code: document.getElementById("mfaConfirm").value.trim() }),
    });
    const d = await res.json();
    setMsg("secMsg", res.ok ? tx("profile.msg.mfa_enabled") : d.detail || tx("profile.msg.failed"), res.ok);
    if (res.ok) load();
  }

  async function disableMfa() {
    const res = await fetch("/api/auth/mfa/disable", {
      method: "POST",
      headers: authHeaders(),
      credentials: "same-origin",
      body: JSON.stringify({ code: document.getElementById("mfaDisable").value.trim() }),
    });
    const d = await res.json();
    setMsg("secMsg", res.ok ? tx("profile.msg.mfa_disabled") : d.detail || tx("profile.msg.failed"), res.ok);
    if (res.ok) load();
  }

  async function logoutAll() {
    await fetch("/api/auth/logout-all", {
      method: "POST",
      headers: authHeaders(),
      credentials: "same-origin",
    });
    try {
      localStorage.removeItem("bd_token");
      localStorage.removeItem("bd_user");
    } catch (_e) {
      /* ignore */
    }
    assignLocationHref("/login");
  }

  async function openPortal() {
    const res = await fetch("/api/billing/portal", {
      method: "POST",
      headers: authHeaders(),
      credentials: "same-origin",
    });
    const d = await res.json();
    if (d.url) assignLocationHref(d.url);
    else setMsg("billingMsg", d.detail || tx("profile.msg.portal_unavailable"), false);
  }

  const api = {
    uploadAvatar: uploadAvatar,
    resetAvatar: resetAvatar,
    saveProfile: saveProfile,
    resendVerify: resendVerify,
    changePassword: changePassword,
    enrollMfa: enrollMfa,
    confirmMfa: confirmMfa,
    disableMfa: disableMfa,
    logoutAll: logoutAll,
    openPortal: openPortal,
    load: load,
  };

  Object.assign(window, api);

  function bindProfileButtons() {
    const map = {
      uploadAvatar: uploadAvatar,
      resetAvatar: resetAvatar,
      saveProfile: saveProfile,
      resendVerify: resendVerify,
      changePassword: changePassword,
      enrollMfa: enrollMfa,
      confirmMfa: confirmMfa,
      disableMfa: disableMfa,
      logoutAll: logoutAll,
      openPortal: openPortal,
    };
    document.querySelectorAll("[data-bd-call]").forEach(function (el) {
      const name = el.getAttribute("data-bd-call");
      const fn = map[name];
      if (!fn || el.dataset.bdProfileBound === "1") return;
      el.dataset.bdProfileBound = "1";
      el.addEventListener("click", function (ev) {
        ev.preventDefault();
        fn();
      });
    });
  }

  function boot() {
    bindProfileButtons();
    load().catch(function (err) {
      console.debug(err);
      setMsg("profileMsg", tx("profile.msg.save_failed"), false);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
