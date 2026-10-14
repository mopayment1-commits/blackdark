/**
 * W3C menu button pattern — #bdAccountTrigger opens #bdAccountMenu.
 * Sign out: server revoke + clear cookie, then hard navigation to /.
 */
(function () {
  "use strict";

  function logoutFailMessage() {
    const btn = document.getElementById("bdHeaderLogout");
    if (btn && btn.getAttribute("data-logout-fail")) {
      return btn.getAttribute("data-logout-fail");
    }
    return "Could not sign out. Try again.";
  }

  function showLogoutFailure(msg) {
    const status = document.getElementById("bdLogoutStatus");
    if (status) {
      status.hidden = false;
      status.textContent = msg;
      return;
    }
    const btn = document.getElementById("bdHeaderLogout");
    if (btn) {
      btn.setAttribute("aria-invalid", "true");
      btn.title = msg;
    }
  }

  function clearClientSessionHints() {
    try {
      localStorage.removeItem("bd_user");
      localStorage.removeItem("bd_token");
      localStorage.removeItem("token");
    } catch (error) {
      console.debug(error);
    }
  }

  const LOGOUT_TIMEOUT_MS = 8000;

  async function performHeaderLogout() {
    const logoutBtn = document.getElementById("bdHeaderLogout");
    if (logoutBtn) {
      logoutBtn.disabled = true;
    }
    const status = document.getElementById("bdLogoutStatus");
    if (status) {
      status.hidden = true;
      status.textContent = "";
    }
    const failMsg = logoutFailMessage();
    try {
      const timeoutSignal =
        typeof AbortSignal !== "undefined" && AbortSignal.timeout
          ? AbortSignal.timeout(LOGOUT_TIMEOUT_MS)
          : undefined;
      const res = await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "same-origin",
        headers: { Accept: "application/json" },
        signal: timeoutSignal,
      });
      const bodyText = await res.text();
      if (res.status !== 200 || !bodyText) {
        showLogoutFailure(failMsg);
        if (logoutBtn) logoutBtn.disabled = false;
        return;
      }
      try {
        const data = JSON.parse(bodyText);
        if (!data || data.success !== true) {
          showLogoutFailure(failMsg);
          if (logoutBtn) logoutBtn.disabled = false;
          return;
        }
      } catch (parseError) {
        console.debug(parseError);
        showLogoutFailure(failMsg);
        if (logoutBtn) logoutBtn.disabled = false;
        return;
      }
      clearClientSessionHints();
      window.location.assign("/");
    } catch (error) {
      console.debug(error);
      showLogoutFailure(failMsg);
      if (logoutBtn) logoutBtn.disabled = false;
    }
  }

  function initAccountMenu() {
    const trigger = document.getElementById("bdAccountTrigger");
    const panel = document.getElementById("bdAccountMenu");
    if (!trigger || !panel) return;
    if (trigger.dataset.bdAccountMenuBound === "1") return;
    trigger.dataset.bdAccountMenuBound = "1";

    function setOpen(open) {
      panel.hidden = !open;
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
    }

    function toggle() {
      setOpen(Boolean(panel.hidden));
    }

    trigger.addEventListener("click", function (ev) {
      ev.preventDefault();
      ev.stopPropagation();
      toggle();
    });

    trigger.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();
        toggle();
      } else if (ev.key === "ArrowDown" && panel.hidden) {
        ev.preventDefault();
        setOpen(true);
        const first = panel.querySelector("a, button");
        if (first) first.focus();
      }
    });

    document.addEventListener("click", function (ev) {
      if (!ev.target.closest(".bd-account-menu")) {
        setOpen(false);
      }
    });

    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") setOpen(false);
    });

    const logoutBtn = document.getElementById("bdHeaderLogout");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        performHeaderLogout();
      });
    }
  }

  window.BDHeaderAccount = { performHeaderLogout: performHeaderLogout };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAccountMenu);
  } else {
    initAccountMenu();
  }
})();
