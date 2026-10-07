/**
 * W3C menu button pattern — #bdAccountTrigger opens #bdAccountMenu.
 */
(function () {
  "use strict";

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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAccountMenu);
  } else {
    initAccountMenu();
  }
})();
