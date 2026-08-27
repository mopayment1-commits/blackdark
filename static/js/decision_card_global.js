/**
 * BLACKDARK — Global Decision Card activation (P1 #1).
 * Renders sticky decision surface on every page with #decisionCardSticky.
 */
(function (global) {
  "use strict";

  const API = "/api/platform/intelligence-ledger/ui/decision-card";

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = String(s ?? "");
    return d.innerHTML;
  }

  function uxMode() {
    return localStorage.getItem("bd_ux_mode")
      || document.getElementById("uxMode")?.value
      || "beginner";
  }

  async function fetchDecisionCard(payload) {
    const res = await fetch(API, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payload, ux_mode: uxMode() }),
    });
    if (!res.ok) throw new Error("decision_card_failed");
    const data = await res.json();
    return data.decision_card;
  }

  function renderCard(card, layer) {
    const el = document.getElementById("decisionCardSticky");
    if (!el || !card) return;

    const verdict = card.verdict || card.action || "OBSERVE";
    const sentence = card.decision_sentence || card.why || "Review monitoring data before acting.";
    const risk = card.risk_warning || "Monitoring only — not investment advice.";
    const conf = card.confidence != null ? ` · Confidence ${Math.round(card.confidence * 100)}%` : "";
    const truth = card.truth_score != null ? ` · Truth ${card.truth_score}` : "";

    el.innerHTML = `
      <div class="verdict">${esc(verdict)}</div>
      <div>${esc(sentence)}${esc(conf)}${esc(truth)}</div>
      <div class="risk">${esc(typeof risk === "string" ? risk : risk.text || "")}</div>
      <div style="margin-top:.4rem;display:flex;gap:.35rem;flex-wrap:wrap">
        <button type="button" id="dcExpand" class="dc-btn">${layer === "summary" ? "Details" : "Summary"}</button>
        <button type="button" id="dcDismiss" class="dc-btn">Dismiss</button>
      </div>`;
    el.hidden = false;

    document.getElementById("dcDismiss")?.addEventListener("click", () => { el.hidden = true; });
    document.getElementById("dcExpand")?.addEventListener("click", async () => {
      const next = layer === "summary" ? "details" : "summary";
      const expanded = await fetchDecisionCard({ ...(card._payload || {}), _layer: next });
      if (expanded) {
        expanded._payload = card._payload;
        renderCard(expanded, next);
      }
    });
  }

  async function activateFromPayload(payload) {
    try {
      const card = await fetchDecisionCard(payload);
      if (card) {
        card._payload = payload;
        renderCard(card, card.layer || "summary");
      }
    } catch (_) {
      /* fail silent on optional surfaces */
    }
  }

  async function activateFromPage() {
    const ctx = global.__BD_DECISION_CONTEXT__;
    if (ctx) {
      await activateFromPayload(ctx);
      return;
    }
    const page = document.body?.dataset?.page || "dashboard";
    const defaults = {
      dashboard: { verdict: "DECIDE", decision_sentence: "Check Oracle verdict and portfolio risk before acting.", page },
      "intelligence-hub": { verdict: "EXPLORE", decision_sentence: "Use typed panels — each module answers what / why / risks.", page },
      capability: { verdict: "MONITOR", decision_sentence: document.getElementById("capDecisionQ")?.textContent || "Review capability data.", page },
      portfolio: { verdict: "PROTECT", decision_sentence: "Non-executive risk awareness — no automatic fund movement.", page },
    };
    await activateFromPayload(defaults[page] || defaults.dashboard);
  }

  async function loadRiskScoreStrip() {
    const strip = document.getElementById("riskScoreStrip");
    if (!strip) return;
    try {
      const res = await fetch("/api/platform/intelligence-ledger/portfolio-ai/risk-score");
      const data = await res.json();
      const port = data.portfolio_risk_score ?? "—";
      const band = data.portfolio_risk_band || "";
      let html = `<span class="risk-strip-label">Portfolio Risk <strong>${esc(port)}</strong> (${esc(band)})</span>`;
      (data.asset_risk_scores || []).slice(0, 6).forEach((a) => {
        html += `<span class="risk-chip" title="${esc(a.display)}">${esc(a.asset)} ${esc(a.risk_score)}</span>`;
      });
      strip.innerHTML = html;
    } catch (_) {
      strip.innerHTML = "";
    }
  }

  function init() {
    if (document.getElementById("decisionCardSticky")) {
      activateFromPage();
    }
    loadRiskScoreStrip();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  global.BDDecisionCard = { activateFromPayload, fetchDecisionCard, renderCard };
})(typeof window !== "undefined" ? window : globalThis);
