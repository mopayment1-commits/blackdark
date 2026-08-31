/**
 * Intelligence Hub — typed renderers (no generic JSON dump for mapped modules).
 */
(function (global) {
  "use strict";

  const { esc, gradeClass, provBadge, bindProvPopovers } = global.BDCapability || {};

  function rendererForModule(mod) {
    const id = (mod && mod.module_id) || "";
    if (id.includes("exchange-health")) return renderExchangeGrades;
    if (id.includes("stablecoin-health")) return renderStablecoinHealth;
    if (id.includes("unified-arbitrage") || id.includes("fill-feasibility")) return renderArbitrageTruth;
    if (id.includes("smart-money-flow") || id.includes("whale-flow")) return renderWhaleAccumulation;
    if (id.includes("token-unlock")) return renderUnlockCalendar;
    if (id.includes("investment-thesis")) return renderThesisScore;
    if (id.includes("daily-market-brief")) return renderDailyNarrative;
    if (id.includes("correlation")) return renderCorrelationHeatmap;
    if (id.includes("stress-test") || id.includes("capital-awareness")) return renderStressScenarios;
    if (id.includes("dex-screener")) return renderDexPools;
    if (id.includes("metrics-library")) return renderMetricsCatalog;
    return null;
  }

  function renderExchangeGrades(data) {
    const grades = data.grades || data.exchanges || (data.analyses ? data.analyses : []);
    const list = Array.isArray(grades) ? grades : Object.entries(grades).map(([k, v]) => ({ exchange: k, ...v }));
    let html = `<div class="card"><h3>Exchange Health — Grade Cards</h3><p class="display-line">What: venue trust grades. Why: counterparty risk. Risk: low-health exposure.</p>`;
    list.slice(0, 12).forEach((ex) => {
      const g = ex.health_grade || ex.grade || ex.overall_grade || "—";
      html += `<div class="grade-card"><div class="grade-badge ${gradeClass(g)}">${esc(g)}</div>
        <div class="grade-meta"><div class="name">${esc(ex.exchange || ex.name || ex.venue)}${provBadge({ source: "exchange_health_monitor", version: data.methodology_version })}</div>
        <div class="detail">${esc(ex.display || ex.health_status || "")}</div></div></div>`;
    });
    return html + "</div>";
  }

  function renderStablecoinHealth(data) {
    const items = data.analyses || [];
    let html = `<div class="card"><h3>Stablecoin Health Monitor</h3><p class="display-line">What: peg health. Why: depeg early warning. Risk: portfolio stablecoin concentration.</p>`;
    items.forEach((sc) => {
      html += `<div class="grade-card"><div class="grade-badge ${gradeClass(sc.stablecoin_grade)}">${esc(sc.stablecoin_grade)}</div>
        <div class="grade-meta"><div class="name">${esc(sc.symbol)} — depeg ${esc((sc.depeg_probability * 100).toFixed(1))}%${provBadge({ source: "stablecoin_health_monitor", version: data.methodology_version })}</div>
        <div class="detail">${esc(sc.display)}</div></div></div>`;
    });
    return html + "</div>";
  }

  function renderArbitrageTruth(data) {
    const opps = data.opportunities || data.top_opportunities || [];
    let html = `<div class="card"><h3>Arbitrage — Net-Edge Truth</h3><p class="display-line">What: executable spread after costs. Why: avoid fake arb. Risk: fill + venue health.</p>`;
    opps.slice(0, 8).forEach((o) => {
      const truth = (o.net_edge_truth || {});
      const score = truth.truth_score ?? o.confidence * 100 ?? 0;
      const rej = o.signal_rejected ? "arb-opp rejected" : "";
      html += `<div class="arb-opp ${rej}"><strong>${esc(o.asset || o.pair)}</strong> · ${esc(o.opportunity_type || "arb")}
        ${provBadge({ source: "net_edge_truth_layer", formula: truth.formula_version, version: data.methodology_version })}
        <div>Truth ${esc(score)} · Edge ${esc(o.net_edge_bps || "—")} bps</div>
        <div class="truth-bar"><div class="truth-fill" style="width:${Math.min(100, score)}%"></div></div></div>`;
    });
    return html + "</div>";
  }

  function renderWhaleAccumulation(data) {
    const score = data.dormancy_score ?? data.accumulation_score ?? 50;
    const bars = [40, 55, 35, 70, 60, 80, 45].map((h, i) => `<span style="height:${h}%"></span>`).join("");
    return `<div class="card"><h3>Whale Flow — Accumulation / Distribution</h3>
      <p class="display-line">What: large-holder activity. Why: smart money signal. Risk: false spikes.</p>
      <div class="whale-bar">${bars}</div>
      <div>Score ${esc(score)} · ${esc(data.whale_label || data.display || "")}${provBadge({ source: "smart_money_flow_tracker", version: data.methodology_version })}</div></div>`;
  }

  function renderUnlockCalendar(data) {
    const events = data.calendar || data.events || data.upcoming || [];
    let html = `<div class="card"><h3>Token Unlock Calendar</h3><p class="display-line">What: vesting schedule. Why: supply shock risk. Risk: high-severity unlocks.</p>`;
    (Array.isArray(events) ? events : []).slice(0, 10).forEach((ev) => {
      html += `<div class="narrative-item"><strong>${esc(ev.asset || ev.symbol)}</strong> — ${esc(ev.date || ev.unlock_date)}
        · Severity ${esc(ev.severity || ev.impact || "—")}${provBadge({ source: "token_unlock_intelligence" })}</div>`;
    });
    return html + "</div>";
  }

  function renderThesisScore(data) {
    const scores = data.scores || (data.thesis_score ? [data] : []);
    let html = `<div class="card"><h3>Investment Thesis — 6 Dimensions</h3><p class="display-line">Not price probability — fundamental conviction rubric.</p>`;
    scores.forEach((t) => {
      html += `<div class="grade-card"><div class="grade-badge ${gradeClass(t.thesis_grade)}">${esc(t.thesis_grade)}</div>
        <div class="grade-meta"><div class="name">${esc(t.asset)} — ${esc(t.thesis_score)}/100${provBadge({ source: "investment_thesis_scoring", version: t.rubric_version })}</div>
        <div class="detail">${esc(t.display)}</div></div></div>`;
    });
    return html + "</div>";
  }

  function renderDailyNarrative(data) {
    const sections = [
      ["What Changed", data.what_changed],
      ["Why", data.why],
      ["Risks", data.risks],
    ];
    let html = `<div class="card"><h3>Daily Market Brief</h3>`;
    sections.forEach(([title, items]) => {
      html += `<h3>${esc(title)}</h3>`;
      (items || []).forEach((it) => {
        html += `<div class="narrative-item">${esc(it.text)}<a class="ev-link" href="${esc(it.evidence_link || "#")}">Evidence ↗</a></div>`;
      });
    });
    return html + provBadge({ source: "daily_market_brief", version: data.methodology_version }) + "</div>";
  }

  function renderCorrelationHeatmap(data) {
    const matrix = data.matrix || data.correlation_matrix || {};
    const assets = data.assets || Object.keys(matrix).slice(0, 6);
    let html = `<div class="card"><h3>Correlation Heatmap</h3><table style="width:100%;font-size:.75rem"><tr><th></th>`;
    assets.forEach((a) => { html += `<th>${esc(a)}</th>`; });
    html += "</tr>";
    assets.forEach((row) => {
      html += `<tr><th>${esc(row)}</th>`;
      assets.forEach((col) => {
        const v = (matrix[row] && matrix[row][col]) ?? (row === col ? 1 : 0.5);
        const pct = Math.round(Number(v) * 100);
        const bg = `rgba(34,211,238,${Math.abs(v)})`;
        html += `<td style="background:${bg};text-align:center">${esc(pct)}</td>`;
      });
      html += "</tr>";
    });
    return html + "</table></div>";
  }

  function renderStressScenarios(data) {
    const scenarios = (data.scenario_stress && data.scenario_stress.scenarios) || data.scenarios || [];
    let html = `<div class="card"><h3>Scenario Stress — 5 Mandatory</h3>`;
    scenarios.forEach((s) => {
      html += `<div class="narrative-item">${esc(s.display || s.name || s.scenario_type)} — Impact ${esc(s.estimated_loss_pct ?? "—")}%</div>`;
    });
    return html + "</div>";
  }

  function renderDexPools(data) {
    const pools = data.pools || data.opportunities || [];
    let html = `<div class="card"><h3>DEX Screener</h3>`;
    pools.slice(0, 8).forEach((p) => {
      html += `<div class="arb-opp">${esc(p.pair || p.protocol)} · APY ${esc(p.apy || p.risk_adjusted_apy || "—")}</div>`;
    });
    return html + "</div>";
  }

  function renderMetricsCatalog(data) {
    const metrics = data.metrics || data.catalog || [];
    let html = `<div class="card"><h3>On-Chain Metrics Library</h3>`;
    (Array.isArray(metrics) ? metrics : []).slice(0, 12).forEach((m) => {
      html += `<div class="narrative-item"><strong>${esc(m.id || m.metric_id)}</strong> — ${esc(m.formula || m.description || "")}</div>`;
    });
    return html + "</div>";
  }

  function renderTyped(data, mod) {
    const fn = rendererForModule(mod);
    if (!fn) return null;
    const html = fn(data);
    setTimeout(() => bindProvPopovers && bindProvPopovers(document.getElementById("panelBody")), 0);
    return html;
  }

  global.BDHubRenderers = { rendererForModule, renderTyped };
})(typeof window !== "undefined" ? window : globalThis);
