/**
 * BLACKDARK — Dedicated capability pages (/exchanges, /stablecoins, /arbitrage, /brief, /whales)
 */
(function () {
  "use strict";

  const root = document.getElementById("capRoot");
  if (!root) return;

  const cap = root.dataset.capability;
  const { esc, gradeClass, provBadge, bindProvPopovers, fetchJson, loadDecisionCard } = window.BDCapability;

  const CONFIG = {
    exchanges: {
      title: "Exchange Health",
      question: "Are my venues trustworthy enough to hold exposure?",
      apis: [
        "/api/platform/intelligence-ledger/portfolio-ai/exchange-health/grades",
        "/api/platform/intelligence-ledger/portfolio-ai/exchange-health",
      ],
      render: renderExchanges,
    },
    stablecoins: {
      title: "Stablecoin Health",
      question: "Is any stablecoin in my book showing depeg stress?",
      apis: ["/api/platform/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health"],
      render: renderStablecoins,
    },
    arbitrage: {
      title: "Arbitrage Scanner",
      question: "Which arb opportunities survive real costs?",
      apis: ["/api/platform/intelligence-ledger/unified-arbitrage/market-radar"],
      render: renderArbitrage,
    },
    brief: {
      title: "Daily Market Brief",
      question: "What changed, why, and what risks today?",
      apis: ["/api/platform/intelligence-ledger/daily-market-brief"],
      render: renderBrief,
    },
    whales: {
      title: "Whale Tracker",
      question: "Are whales accumulating or distributing?",
      apis: [
        "/api/platform/intelligence-ledger/onchain-layer/smart-money-flow?asset=BTC",
        "/api/platform/intelligence-ledger/onchain-layer/smart-money-flow?asset=ETH",
      ],
      render: renderWhales,
    },
  };

  const cfg = CONFIG[cap];
  if (!cfg) {
    root.innerHTML = '<div class="cap-err">Unknown capability.</div>';
    return;
  }

  document.getElementById("capDecisionQ").textContent = cfg.question;

  async function init() {
    root.innerHTML = '<div class="cap-loading">Loading decision surface…</div>';
    try {
      const payloads = await Promise.all(cfg.apis.map((u) => fetchJson(u)));
      const data = payloads.length === 1 ? payloads[0] : { items: payloads };
      root.innerHTML = cfg.render(data, payloads);
      bindProvPopovers(root);
      loadDecisionCard(data);
    } catch (e) {
      root.innerHTML = `<div class="cap-err">Failed to load: ${esc(e.message)}</div>`;
    }
  }

  function renderExchanges(data) {
    const grades = data.grades || data.exchanges || [];
    const list = Array.isArray(grades) ? grades : Object.values(grades);
    let html = `<div class="cap-grid"><div class="cap-card"><h2>Grade Cards (A+ → F)</h2><h3>What</h3><p>Venue health from reserves, outflows, incidents.</p>
      <h3>Why it matters</h3><p>Counterparty risk is the silent killer in crypto.</p><h3>Risks</h3><p>Low-grade venue + high exposure = concentration risk.</p></div>
      <div class="cap-card"><h2>Live Grades</h2>`;
    if (!list.length) {
      html += `<p>No grade data — showing panel summary.</p><pre style="font-size:.7rem;overflow:auto">${esc(JSON.stringify(data, null, 2).slice(0, 800))}</pre>`;
    }
    list.forEach((ex) => {
      const g = ex.health_grade || ex.grade || "B";
      html += `<div class="grade-card"><div class="grade-badge ${gradeClass(g)}">${esc(g)}</div>
        <div class="grade-meta"><div class="name">${esc(ex.exchange || ex.name || ex.venue)}${provBadge({ source: "exchange_health_monitor", version: data.methodology_version })}</div>
        <div class="detail">${esc(ex.display || ex.health_status || "")}</div></div></div>`;
    });
    return html + "</div></div>";
  }

  function renderStablecoins(data) {
    const items = data.analyses || [];
    let html = `<div class="cap-grid"><div class="cap-card"><h2>De-Peg Monitor</h2>
      <h3>What</h3><p>Price deviation, redemption pressure, collateral, funding, social panic.</p>
      <h3>Action</h3><p>Reduce exposure if grade drops below BBB and portfolio &gt;30%.</p></div>
      <div class="cap-card"><h2>Stablecoin Grades</h2>`;
    items.forEach((sc) => {
      html += `<div class="grade-card"><div class="grade-badge ${gradeClass(sc.stablecoin_grade)}">${esc(sc.stablecoin_grade)}</div>
        <div class="grade-meta"><div class="name">${esc(sc.symbol)}${provBadge({ source: "stablecoin_health_monitor" })}</div>
        <div class="detail">Depeg ${esc((sc.depeg_probability * 100).toFixed(1))}% · ${esc(sc.display)}</div></div></div>`;
    });
    return html + "</div></div>";
  }

  function renderArbitrage(data) {
    const opps = data.top_opportunities || data.opportunities || [];
    let html = `<div class="cap-card"><h2>Net-Edge Score + Cost Breakdown</h2>
      <p>Ranked by executable net edge USDT — simulation only.</p>`;
    opps.slice(0, 10).forEach((o) => {
      const truth = o.net_edge_truth || {};
      const score = truth.truth_score ?? 0;
      html += `<div class="arb-opp ${o.signal_rejected ? "rejected" : ""}">
        <strong>${esc(o.asset || o.pair)}</strong> ${provBadge({ source: "net_edge_truth", formula: truth.formula_version })}
        <div>Truth ${esc(score)} · Net ${esc(o.net_edge_usdt)} USDT · ${esc(o.opportunity_type)}</div>
        <div class="truth-bar"><div class="truth-fill" style="width:${Math.min(100, score)}%"></div></div>
        <div style="font-size:.72rem;color:var(--cap-muted)">Fees/slippage in truth layer — not gross spread.</div></div>`;
    });
    return html + "</div>";
  }

  function renderBrief(data) {
    const sections = [["What Changed", data.what_changed], ["Why", data.why], ["Risks", data.risks]];
    let html = `<div class="cap-card"><h2>3-Point Narrative</h2>`;
    sections.forEach(([title, items]) => {
      html += `<h3>${esc(title)}</h3>`;
      (items || []).forEach((it) => {
        html += `<div class="narrative-item">${esc(it.text)}<a class="ev-link" href="${esc(it.evidence_link || "#")}">Evidence ↗</a></div>`;
      });
    });
    return html + provBadge({ source: "daily_market_brief", version: data.methodology_version }) + "</div>";
  }

  function renderWhales(data, payloads) {
    const items = payloads || [data];
    let html = `<div class="cap-grid"><div class="cap-card"><h2>Accumulation / Distribution</h2>
      <p>Smart money flow + dormancy spikes — on-chain only.</p></div><div class="cap-card"><h2>Assets</h2>`;
    items.forEach((d) => {
      const a = d.asset || (d.analysis && d.analysis.asset) || "—";
      const score = d.dormancy_score ?? d.analysis?.dormancy_score ?? "—";
      const label = d.whale_label ?? d.analysis?.whale_label ?? "";
      const bars = [30, 50, 40, 75, 55, 90, 45].map((h) => `<span style="height:${h}%"></span>`).join("");
      html += `<div style="margin-bottom:1rem"><strong>${esc(a)}</strong> · Score ${esc(score)} ${provBadge({ source: "smart_money_flow" })}
        <div class="whale-bar">${bars}</div><div style="font-size:.78rem;color:var(--cap-muted)">${esc(label)}</div></div>`;
    });
    return html + "</div></div>";
  }

  init();
})();
