/**
 * BLACKDARK Capability Core — shared UI primitives for Route + Component Sovereignty.
 */
(function (global) {
  "use strict";

  const esc = (global.BDDomSafe && global.BDDomSafe.esc) || ((s) => {
    const d = document.createElement("div");
    d.textContent = String(s ?? "");
    return d.innerHTML;
  });

  function gradeClass(grade) {
    const g = String(grade || "C").replace(/[^A-Z+]/gi, "").toUpperCase();
    if (g.startsWith("AAA") || g === "AA" || g === "A") return "grade-A";
    if (g.startsWith("BBB") || g === "BB" || g === "B") return "grade-B";
    return "grade-D";
  }

  function provBadge(meta) {
    const m = meta || {};
    const payload = esc(JSON.stringify({
      source: m.source || m.data_source || "BLACKDARK Intelligence Ledger",
      formula: m.formula || m.formula_version || m.methodology_version || "—",
      version: m.version || m.rubric_version || m.methodology_version || "1.0",
      freshness: m.freshness || m.timestamp || "live",
    }));
    return `<span class="prov-badge" data-prov="${payload}" title="Provenance">ⓘ</span>`;
  }

  function bindProvPopovers(root) {
    const pop = document.getElementById("provPopover");
    if (!pop) return;
    (root || document).querySelectorAll(".prov-badge").forEach((el) => {
      el.onclick = (e) => {
        e.stopPropagation();
        let meta;
        try { meta = JSON.parse(el.getAttribute("data-prov") || "{}"); } catch (_) { meta = {}; }
        pop.innerHTML = `<dl>
          <dt>Source</dt><dd>${esc(meta.source)}</dd>
          <dt>Formula</dt><dd>${esc(meta.formula)}</dd>
          <dt>Version</dt><dd>${esc(meta.version)}</dd>
          <dt>Freshness</dt><dd>${esc(meta.freshness)}</dd>
        </dl>`;
        pop.classList.add("open");
        pop.style.left = Math.min(e.clientX, window.innerWidth - 340) + "px";
        pop.style.top = Math.max(10, e.clientY - 120) + "px";
      };
    });
    document.addEventListener("click", () => pop.classList.remove("open"), { once: true });
  }

  async function fetchJson(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }

  function renderDecisionSticky(payload) {
    const el = document.getElementById("decisionCardSticky");
    if (!el || !payload) return;
    const card = payload.decision_card || payload;
    const verdict = card.verdict || card.action || "OBSERVE";
    const sentence = card.decision_sentence || card.summary || payload.display || "Review the data before acting.";
    const risk = card.risk_warning?.text || card.risk || "Monitoring only — not investment advice.";
    el.innerHTML = `<div class="verdict">${esc(verdict)}</div>
      <div>${esc(sentence)}</div>
      <div class="risk">${esc(risk)}</div>
      <button type="button" id="decisionCardDismiss">Dismiss</button>`;
    el.hidden = false;
    const btn = document.getElementById("decisionCardDismiss");
    if (btn) btn.onclick = () => { el.hidden = true; };
  }

  async function loadDecisionCard(apiPayload) {
    if (typeof window !== "undefined" && window.BDDecisionCard && window.BDDecisionCard.activateFromPayload) {
      await window.BDDecisionCard.activateFromPayload(apiPayload || {});
      return;
    }
    try {
      const mode = localStorage.getItem("bd_ux_mode") || "beginner";
      const res = await fetch("/api/platform/intelligence-ledger/ui/decision-card", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ payload: apiPayload || {}, ux_mode: mode }),
      });
      const data = await res.json();
      if (data.decision_card) renderDecisionSticky({ decision_card: data.decision_card });
    } catch (_) { /* optional */ }
  }

  global.BDCapability = {
    esc,
    gradeClass,
    provBadge,
    bindProvPopovers,
    fetchJson,
    renderDecisionSticky,
    loadDecisionCard,
  };
})(typeof window !== "undefined" ? window : globalThis);
