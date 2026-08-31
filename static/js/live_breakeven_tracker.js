/**
 * Live Breakeven Tracker — Feature #404 client-side instant calculation.
 * Mirrors server formula (average_cost_remaining). Server refresh every 30s.
 */
(function () {
  "use strict";

  const SERVER_REFRESH_MS = 30000;
  const { esc } = window.BDDomSafe || { esc: (s) => String(s ?? "") };

  function eventFeeUsd(event) {
    if (event.type !== "buy" && event.type !== "sell") return 0;
    const notional = Number(event.quantity) * Number(event.price);
    return notional * (Number(event.fee_pct || 0) / 100);
  }

  function computeDynamicBreakeven(events) {
    const sorted = [...events].sort((a, b) => (a.timestamp || "").localeCompare(b.timestamp || ""));
    let totalQty = 0;
    let totalCost = 0;
    let fundingTotal = 0;

    for (const event of sorted) {
      if (event.type === "buy") {
        const qty = Number(event.quantity);
        const price = Number(event.price);
        const exchangeFee = eventFeeUsd(event);
        const networkFee = Number(event.network_fee_usd || 0);
        const slippage = Number(event.slippage_usd || 0);
        totalCost += qty * price + exchangeFee + networkFee + slippage;
        totalQty += qty;
      } else if (event.type === "sell") {
        const qty = Number(event.quantity);
        if (totalQty <= 0) continue;
        const avgCost = totalCost / totalQty;
        totalCost -= qty * avgCost;
        totalQty -= qty;
      } else if (event.type === "funding") {
        fundingTotal += Number(event.amount_usd || 0);
      }
    }

    if (totalQty <= 0) return { ok: false, error: "zero_remaining_quantity" };
    return {
      ok: true,
      breakeven_price: (totalCost + fundingTotal) / totalQty,
      remaining_quantity: totalQty,
      remaining_cost_basis_usd: totalCost,
      funding_accumulation_usd: fundingTotal,
    };
  }

  function formatUsd(n, digits) {
    if (n == null || Number.isNaN(n)) return "غير متوفر";
    return "$" + Number(n).toLocaleString(undefined, {
      minimumFractionDigits: digits ?? 2,
      maximumFractionDigits: digits ?? 4,
    });
  }

  function renderFeeLines(feeTransparency) {
    if (!feeTransparency?.line_items?.length) return "";
    let html = '<div class="fee-lines"><h4>Fee Transparency — every cent</h4><ul>';
    feeTransparency.line_items.forEach((line) => {
      if (line.affects_remaining_breakeven === false) return;
      html += `<li>${esc(line.display || line.label)}</li>`;
    });
    html += "</ul></div>";
    return html;
  }

  function renderPanel(data, clientBreakeven) {
    const b = data.breakeven || {};
    const dist = data.distance_to_breakeven || {};
    const serverBe = b.price;
    const clientBe = clientBreakeven?.breakeven_price;
    const drift =
      serverBe && clientBe
        ? Math.abs((clientBe - serverBe) / serverBe) * 100
        : null;

    let html = `<div class="breakeven-hero">
      <div class="be-price">${formatUsd(clientBe ?? serverBe, 4)}</div>
      <div class="be-label">Live Breakeven (Dynamic Cost Basis)</div>
    </div>`;

    if (drift != null) {
      const ok = drift <= 0.01;
      html += `<div class="drift ${ok ? "ok" : "warn"}">Client/server drift: ${drift.toFixed(4)}% (target ±0.01%)</div>`;
    }

    html += `<div class="kv-grid">
      <div><span>Current price</span><strong>${formatUsd(dist.current_price)}</strong></div>
      <div><span>Distance</span><strong>${esc(dist.display || "")}</strong></div>
      <div><span>Remaining qty</span><strong>${esc(b.remaining_quantity)}</strong></div>
      <div><span>P/L vs breakeven</span><strong>${formatUsd(dist.unrealized_pnl_vs_breakeven_usd)}</strong></div>
    </div>`;

    html += renderFeeLines(data.fee_transparency);

    const cp = data.capital_protection;
    if (cp?.alerts?.length) {
      html += '<div class="alerts"><h4>Capital Protection (#410)</h4>';
      cp.alerts.forEach((a) => {
        html += `<div class="alert ${esc(a.severity)}">${esc(a.display)}</div>`;
      });
      html += "</div>";
    }

    html += `<div class="disclaimer">${esc(data.disclaimer || "")}</div>`;
    return html;
  }

  async function loadPosition(positionId) {
    const panel = document.getElementById("bePanel");
    const status = document.getElementById("beStatus");
    if (!panel) return;

    panel.innerHTML = '<div class="state"><span class="spinner"></span> Loading…</div>';
    try {
      const res = await fetch(
        `/api/platform/intelligence-ledger/portfolio-ai/live-breakeven?position_id=${encodeURIComponent(positionId)}`
      );
      const data = await res.json();
      if (!data.ok) {
        panel.innerHTML = `<div class="state error">${esc(data.error || "not_found")}</div>`;
        return;
      }

      const events = data.client_calculation?.events || [];
      const clientCalc = computeDynamicBreakeven(events);
      panel.innerHTML = renderPanel(data, clientCalc);

      if (status) {
        status.textContent = `Client instant ✓ | Server refresh ${SERVER_REFRESH_MS / 1000}s`;
      }

      window.__beLastPayload = data;
      window.__beClientCalc = clientCalc;
    } catch (err) {
      panel.innerHTML = `<div class="state error">${esc(String(err))}</div>`;
    }
  }

  async function runSimulation() {
    const positionId = document.getElementById("positionSelect")?.value || "pos_btc_001";
    const dcaQty = document.getElementById("dcaQty")?.value;
    const dcaPrice = document.getElementById("dcaPrice")?.value;
    const simOut = document.getElementById("simResult");
    if (!simOut) return;

    const params = new URLSearchParams({ position_id: positionId });
    if (dcaQty) params.set("hypothetical_dca_qty", dcaQty);
    if (dcaPrice) params.set("hypothetical_dca_price", dcaPrice);

    simOut.innerHTML = '<span class="spinner"></span>';
    try {
      const res = await fetch(
        `/api/platform/intelligence-ledger/portfolio-ai/live-breakeven/simulate?${params}`
      );
      const data = await res.json();
      if (!data.ok) {
        simOut.innerHTML = `<span class="error">${esc(data.error)}</span>`;
        return;
      }
      simOut.innerHTML = `<div class="sim-result">${esc(data.display)}</div>`;
    } catch (err) {
      simOut.innerHTML = `<span class="error">${esc(String(err))}</span>`;
    }
  }

  function init() {
    const select = document.getElementById("positionSelect");
    const loadBtn = document.getElementById("loadBtn");
    const simBtn = document.getElementById("simBtn");

    if (loadBtn) {
      loadBtn.addEventListener("click", () => {
        loadPosition(select?.value || "pos_btc_001");
      });
    }
    if (simBtn) {
      simBtn.addEventListener("click", runSimulation);
    }

    loadPosition(select?.value || "pos_btc_001");
    setInterval(() => loadPosition(select?.value || "pos_btc_001"), SERVER_REFRESH_MS);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.LiveBreakevenTracker = { computeDynamicBreakeven };
})();
