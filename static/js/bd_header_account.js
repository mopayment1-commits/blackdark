/**
 * Global header account menu + logout (site_top_nav).
 */
(function () {
  "use strict";

  function closeMenus() {
    document.querySelectorAll(".bd-account-panel").forEach(function (panel) {
      panel.hidden = true;
    });
    document.querySelectorAll("[data-bd-account-open]").forEach(function (btn) {
      btn.setAttribute("aria-expanded", "false");
    });
  }

  document.addEventListener("click", function (ev) {
    const trigger = ev.target.closest("[data-bd-account-open]");
    if (trigger) {
      ev.preventDefault();
      const menu = trigger.closest(".bd-account-menu");
      const panel = menu ? menu.querySelector(".bd-account-panel") : null;
      if (!panel) return;
      const open = panel.hidden;
      closeMenus();
      panel.hidden = !open;
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
      return;
    }
    if (!ev.target.closest(".bd-account-menu")) {
      closeMenus();
    }
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") closeMenus();
  });

  const logoutBtn = document.getElementById("bdHeaderLogout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", function () {
      fetch("/api/auth/logout", { method: "POST", credentials: "same-origin" }).catch(
        function () {}
      );
      try {
        localStorage.removeItem("bd_user");
        localStorage.removeItem("bd_token");
        localStorage.removeItem("token");
      } catch (error) {
        console.debug(error);
      }
      window.location.href = "/";
    });
  }
})();
