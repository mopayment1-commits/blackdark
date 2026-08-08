/**
 * BLACKDARK Strict Disclaimer Architecture — Layer 3 modal + Layer 4 footer injector.
 * No third-party deps.
 */
(function () {
  const FOOTER_TEXT =
    "BLACKDARK is an analytical tool. Not financial advice. No guarantee of accuracy or profit.";
  const ACK =
    "I acknowledge that BLACKDARK is not a financial advisor. I accept full responsibility for my trades.";
  const BANNER =
    "Analytical tool · Not a financial advisor · regulatory_status=not_regulated";

  function ensureStylesheet() {
    if (document.getElementById("bd-legal-shield-css")) return;
    const link = document.createElement("link");
    link.id = "bd-legal-shield-css";
    link.rel = "stylesheet";
    link.href = "/static/css/legal-shield.css";
    document.head.appendChild(link);
  }

  function injectBanner() {
    if (document.getElementById("bdLegalBanner")) return;
    const el = document.createElement("div");
    el.id = "bdLegalBanner";
    el.className = "bd-legal-banner";
    el.setAttribute("role", "status");
    el.textContent = BANNER;
    document.body.insertBefore(el, document.body.firstChild);
  }

  function injectFooter() {
    if (document.getElementById("bdLegalFooter")) return;
    const el = document.createElement("div");
    el.id = "bdLegalFooter";
    el.className = "bd-legal-footer";
    el.innerHTML =
      "<strong>Legal Shield</strong> · " +
      FOOTER_TEXT +
      ' · <a href="/terms" style="color:#22d3ee">Terms</a> · ' +
      '<a href="/privacy" style="color:#22d3ee">Privacy</a> · ' +
      '<a href="/request-deletion" style="color:#22d3ee">Deletion</a>';
    document.body.appendChild(el);
  }

  function ensureModal() {
    if (document.getElementById("bdLegalModal")) return;
    const wrap = document.createElement("div");
    wrap.id = "bdLegalModal";
    wrap.className = "bd-legal-modal-backdrop";
    wrap.innerHTML =
      '<div class="bd-legal-modal" role="dialog" aria-modal="true">' +
      "<h2>Before you use the Oracle</h2>" +
      "<p>BLACKDARK is classified as an analytical tool — not a financial advisor.</p>" +
      '<label><input type="checkbox" id="bdLegalAckCheck"> <span>' +
      ACK +
      "</span></label>" +
      '<button type="button" id="bdLegalAckBtn" disabled>I Accept — Continue</button>' +
      "</div>";
    document.body.appendChild(wrap);
    const check = document.getElementById("bdLegalAckCheck");
    const btn = document.getElementById("bdLegalAckBtn");
    check.addEventListener("change", function () {
      btn.disabled = !check.checked;
    });
    btn.addEventListener("click", async function () {
      if (!check.checked) return;
      btn.disabled = true;
      btn.textContent = "Saving…";
      try {
        const headers = { "Content-Type": "application/json" };
        const token = localStorage.getItem("bd_token");
        if (token) headers.Authorization = "Bearer " + token;
        const res = await fetch("/api/legal/accept-terms", {
          method: "POST",
          credentials: "same-origin",
          headers: headers,
          body: JSON.stringify({
            ack: true,
            ack_text: ACK,
            source: "legal_shield_modal",
          }),
        });
        if (!res.ok) throw new Error("accept_failed");
        localStorage.setItem("bd_terms_accepted", "1");
        wrap.classList.remove("show");
        if (typeof window.__bdAfterLegalAccept === "function") {
          window.__bdAfterLegalAccept();
        }
      } catch (e) {
        btn.textContent = "Try again";
        btn.disabled = false;
      }
    });
  }

  async function hasAccepted() {
    try {
      const res = await fetch("/api/legal/terms-status", { credentials: "same-origin" });
      const d = await res.json();
      return !!d.accepted;
    } catch (e) {
      return localStorage.getItem("bd_terms_accepted") === "1";
    }
  }

  window.bdLegalShieldRequireConsent = async function (onAccepted) {
    ensureStylesheet();
    ensureModal();
    const ok = await hasAccepted();
    if (ok) {
      if (typeof onAccepted === "function") onAccepted();
      return true;
    }
    window.__bdAfterLegalAccept = onAccepted || null;
    document.getElementById("bdLegalModal").classList.add("show");
    return false;
  };

  function boot() {
    ensureStylesheet();
    injectBanner();
    injectFooter();
    ensureModal();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
