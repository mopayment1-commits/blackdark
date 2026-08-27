/**
 * BLACKDARK — Capability pages (17 routes + P0/P1 renderers)
 */
(function () {
  "use strict";

  const root = document.getElementById("capRoot");
  if (!root) return;

  const cap = root.dataset.capability;
  const thesisAsset = root.dataset.thesisAsset || new URLSearchParams(location.search).get("asset") || "BTC";
  const { esc, gradeClass, provBadge, bindProvPopovers, fetchJson, loadDecisionCard } = window.BDCapability;

  const CONFIG = {
    exchanges: {
      question: "Are my venues trustworthy enough to hold exposure?",
      apis: ["/api/platform/intelligence-ledger/portfolio-ai/exchange-health/grades"],
      render: renderExchanges,
    },
    stablecoins: {
      question: "Is any stablecoin in my book showing depeg stress?",
      apis: ["/api/platform/intelligence-ledger/portfolio-ai/capital-awareness/stablecoin-health"],
      render: renderStablecoins,
    },
    arbitrage: {
      question: "Which arb opportunities survive real costs?",
      apis: ["/api/platform/intelligence-ledger/unified-arbitrage/market-radar"],
      render: renderArbitrage,
    },
    brief: {
      question: "What changed, why, and what risks today?",
      apis: ["/api/platform/intelligence-ledger/daily-market-brief"],
      render: renderBrief,
    },
    whales: {
      question: "Are whales accumulating or distributing?",
      apis: [
        "/api/platform/intelligence-ledger/onchain-layer/smart-money-flow?asset=BTC",
        "/api/platform/intelligence-ledger/onchain-layer/smart-money-flow?asset=ETH",
      ],
      render: renderWhales,
    },
    liquidity: {
      question: "Can I fill this size without unacceptable slippage?",
      apis: ["/api/platform/intelligence-ledger/fill-feasibility/heatmap"],
      render: renderLiquidity,
    },
    defi: {
      question: "Which DeFi yields survive risk adjustment?",
      apis: ["/api/platform/intelligence-ledger/unified-arbitrage/defi"],
      render: renderDefi,
    },
    unlocks: {
      question: "Which unlocks threaten my holdings this month?",
      apis: ["/api/platform/intelligence-ledger/token-unlock/calendar"],
      render: renderUnlocks,
    },
    correlation: {
      question: "How correlated is my book — contagion risk?",
      apis: ["/api/platform/intelligence-ledger/portfolio-ai/capital-awareness/correlation-matrix"],
      render: renderCorrelation,
    },
    "stress-test": {
      question: "What happens to my portfolio under stress?",
      apis: ["/api/platform/intelligence-ledger/portfolio-ai/capital-awareness/stress-test"],
      render: renderStress,
    },
    thesis: {
      question: `How strong is the ${thesisAsset} investment thesis?`,
      apis: [`/api/platform/intelligence-ledger/investment-thesis?asset=${thesisAsset}`],
      render: renderThesis,
    },
    sopr: {
      question: "Are holders in profit or loss regime?",
      apis: ["/api/platform/onchain/advanced?asset=BTC"],
      render: renderSopr,
    },
    dormancy: {
      question: "Are dormant coins waking up (whale spikes)?",
      apis: ["/api/platform/intelligence-ledger/onchain-layer/smart-money-flow?asset=BTC"],
      render: renderDormancy,
    },
    clusters: {
      question: "Which wallet clusters matter for this flow?",
      apis: ["/api/platform/wallet/clusters?address=0x0000000000000000000000000000000000000000"],
      render: renderClusters,
    },
    "dex-screener": {
      question: "Which pools have yield with acceptable risk flags?",
      apis: ["/api/platform/intelligence-ledger/unified-arbitrage/defi/dex-screener"],
      render: renderDexScreener,
    },
    treasuries: {
      question: "How healthy are protocol treasuries?",
      apis: ["/api/platform/defi/raises"],
      render: renderTreasuries,
    },
    metrics: {
      question: "What metric should I trust — and how is it computed?",
      apis: ["/api/platform/intelligence-ledger/onchain-layer/metrics-library?asset=BTC"],
      render: renderMetrics,
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
      loadDecisionCard({ ...data, display: data.display, page: cap });
    } catch (e) {
      root.innerHTML = `<div class="cap-err">Failed to load: ${esc(e.message)}</div>`;
    }
  }

  function shell(what, why, risk, body) {
    return `<div class="cap-grid"><div class="cap-card"><h2>Decision Surface</h2>
      <h3>What</h3><p>${esc(what)}</p><h3>Why</h3><p>${esc(why)}</p><h3>Risks</h3><p>${esc(risk)}</p></div>
      <div class="cap-card">${body}</div></div>`;
  }

  function renderExchanges(data) {
    const list = data.grades || [];
    let body = "<h2>Grade Cards</h2>";
    (Array.isArray(list) ? list : Object.values(list)).forEach((ex) => {
      const g = ex.health_grade || ex.grade || "B";
      body += `<div class="grade-card"><div class="grade-badge ${gradeClass(g)}">${esc(g)}</div>
        <div class="grade-meta"><div class="name">${esc(ex.exchange || ex.name)}${provBadge({ source: "exchange_health" })}</div>
        <div class="detail">${esc(ex.display || "")}</div></div></div>`;
    });
    return shell("Venue health grades.", "Counterparty risk.", "Low-grade + high exposure.", body);
  }

  function renderStablecoins(data) {
    let body = "<h2>Stablecoin Grades</h2>";
    (data.analyses || []).forEach((sc) => {
      body += `<div class="grade-card"><div class="grade-badge ${gradeClass(sc.stablecoin_grade)}">${esc(sc.stablecoin_grade)}</div>
        <div class="grade-meta"><div class="name">${esc(sc.symbol)}${provBadge({ source: "stablecoin_health" })}</div>
        <div class="detail">Depeg ${esc((sc.depeg_probability * 100).toFixed(1))}%</div></div></div>`;
    });
    return shell("Peg health monitor.", "Depeg early warning.", "Concentration in threatened stables.", body);
  }

  function renderArbitrage(data) {
    let body = "";
    (data.top_opportunities || []).slice(0, 8).forEach((o) => {
      const t = (o.net_edge_truth || {}).truth_score ?? 0;
      body += `<div class="arb-opp"><strong>${esc(o.asset)}</strong> Truth ${esc(t)}${provBadge({ source: "net_edge" })}
        <div class="truth-bar"><div class="truth-fill" style="width:${Math.min(100, t)}%"></div></div></div>`;
    });
    return shell("Executable arb after costs.", "Avoid fake spread.", "Fill + venue risk.", body);
  }

  function renderBrief(data) {
    let body = "";
    [["What Changed", data.what_changed], ["Why", data.why], ["Risks", data.risks]].forEach(([t, items]) => {
      body += `<h3>${esc(t)}</h3>`;
      (items || []).forEach((it) => {
        body += `<div class="narrative-item">${esc(it.text)}</div>`;
      });
    });
    return shell("Daily narrative.", "Regime context.", "Event + vol risks.", body);
  }

  function renderWhales(data, payloads) {
    let body = "";
    (payloads || [data]).forEach((d) => {
      const bars = [30, 55, 40, 75, 60, 90].map((h) => `<span style="height:${h}%"></span>`).join("");
      body += `<div><strong>${esc(d.asset || "BTC")}</strong> · ${esc(d.dormancy_score ?? "—")}
        <div class="whale-bar">${bars}</div></div>`;
    });
    return shell("Whale accumulation.", "Smart money signal.", "False spikes.", body);
  }

  function renderLiquidity(data) {
    const cells = data.heatmap || data.cells || data.pairs || [];
    let body = "<h2>Slippage Heatmap</h2>";
    if (Array.isArray(cells) && cells.length) {
      cells.slice(0, 12).forEach((c) => {
        body += `<div class="narrative-item">${esc(c.pair || c.symbol)} · slippage ${esc(c.slippage_bps ?? c.score ?? "—")} bps</div>`;
      });
    } else {
      body += `<pre style="font-size:.7rem;overflow:auto">${esc(JSON.stringify(data, null, 2).slice(0, 1200))}</pre>`;
    }
    return shell("Fill feasibility.", "Size vs depth.", "Illiquid fills.", body);
  }

  function renderDefi(data) {
    const opps = data.opportunities || data.pools || [];
    let body = "";
    opps.slice(0, 10).forEach((p) => {
      body += `<div class="arb-opp">${esc(p.protocol || p.pair)} · APY ${esc(p.apy || p.risk_adjusted_apy || "—")}
        · Grade ${esc(p.protocol_grade || p.collateral_grade_462 || "—")}</div>`;
    });
    return shell("DeFi yield opportunities.", "Risk-adjusted APY.", "Smart contract risk.", body);
  }

  function renderUnlocks(data) {
    const events = data.events || data.calendar || data.upcoming || [];
    let body = "";
    (Array.isArray(events) ? events : []).slice(0, 12).forEach((ev) => {
      body += `<div class="narrative-item"><strong>${esc(ev.asset || ev.symbol)}</strong> ${esc(ev.date || ev.unlock_date)}
        · ${esc(ev.severity || ev.impact || "—")}</div>`;
    });
    return shell("Unlock calendar.", "Supply shocks.", "High-severity unlocks.", body);
  }

  function renderCorrelation(data) {
    const assets = data.assets || Object.keys(data.matrix || {}).slice(0, 5);
    const matrix = data.matrix || data.correlation_matrix || {};
    let body = "<table style='width:100%;font-size:.75rem'><tr><th></th>";
    assets.forEach((a) => { body += `<th>${esc(a)}</th>`; });
    body += "</tr>";
    assets.forEach((row) => {
      body += `<tr><th>${esc(row)}</th>`;
      assets.forEach((col) => {
        const v = (matrix[row] && matrix[row][col]) ?? (row === col ? 1 : 0.5);
        body += `<td style="background:rgba(34,211,238,${Math.abs(v)})">${esc(Math.round(v * 100))}</td>`;
      });
      body += "</tr>";
    });
    body += "</table>";
    return shell("Correlation heatmap.", "Contagion risk.", "Correlation → 1.0 stress.", body);
  }

  function renderStress(data) {
    const scenarios = data.scenarios || (data.metrics && data.scenario_results) || [];
    let body = "";
    (Array.isArray(scenarios) ? scenarios : Object.values(scenarios)).slice(0, 5).forEach((s) => {
      body += `<div class="narrative-item">${esc(s.display || s.name || s.scenario_type)} · loss ${esc(s.estimated_loss_pct ?? "—")}%</div>`;
    });
    return shell("5 stress scenarios.", "Tail risk.", "Uncontrolled blast radius.", body);
  }

  function renderThesis(data) {
    const scores = data.scores || (data.thesis_score ? [data] : []);
    let body = "";
    scores.forEach((t) => {
      body += `<div class="grade-card"><div class="grade-badge ${gradeClass(t.thesis_grade)}">${esc(t.thesis_grade)}</div>
        <div class="grade-meta"><div class="name">${esc(t.asset)} ${esc(t.thesis_score)}/100</div>
        <div class="detail">Not price probability</div></div></div>`;
    });
    return shell("6-dimension thesis rubric.", "Fundamental conviction.", "Not price prediction.", body);
  }

  function renderSopr(data) {
    const sopr = data.sopr_proxy || data.sopr || {};
    const body = `<div class="cap-card"><h2>SOPR Proxy</h2>
      <div class="display-line">Ratio ${esc(sopr.ratio ?? sopr)} · Regime ${esc(sopr.regime || data.regime || "—")}</div></div>`;
    return shell("Spent output profit ratio.", "Holder P/L regime.", "Lag vs spot.", body);
  }

  function renderDormancy(data) {
    const a = data.analysis || data;
    const body = `<div>Dormancy ${esc(a.dormancy_score)} · ${esc(a.whale_label || "")}
      <div class="whale-bar">${[20, 60, 40, 90, 30].map((h) => `<span style="height:${h}%"></span>`).join("")}</div></div>`;
    return shell("Age consumed spikes.", "Ancient whale awakening.", "False positives.", body);
  }

  function renderClusters(data) {
    const body = `<pre style="font-size:.72rem;overflow:auto;max-height:320px">${esc(JSON.stringify(data, null, 2).slice(0, 2000))}</pre>`;
    return shell("Wallet clusters.", "Entity resolution.", "Incomplete labels.", body);
  }

  function renderDexScreener(data) {
    const pools = data.pools || data.opportunities || [];
    let body = "";
    pools.slice(0, 10).forEach((p) => {
      body += `<div class="arb-opp">${esc(p.pair || p.protocol)} · liq ${esc(p.liquidity_usd || "—")}</div>`;
    });
    return shell("DEX pools.", "On-chain liquidity.", "Rug + IL risk.", body);
  }

  function renderTreasuries(data) {
    const rounds = data.rounds || data.data || (Array.isArray(data) ? data : []);
    let body = "";
    (Array.isArray(rounds) ? rounds : []).slice(0, 10).forEach((r) => {
      body += `<div class="narrative-item">${esc(r.name || r.project)} · ${esc(r.amount || r.raised || "—")}</div>`;
    });
    if (!body) body = `<pre style="font-size:.7rem">${esc(JSON.stringify(data, null, 2).slice(0, 1000))}</pre>`;
    return shell("Protocol treasuries / raises.", "Runway context.", "Stale funding data.", body);
  }

  function renderMetrics(data) {
    const metrics = data.metrics || data.catalog || [];
    let body = "";
    (Array.isArray(metrics) ? metrics : []).slice(0, 15).forEach((m) => {
      body += `<div class="narrative-item"><strong>${esc(m.id || m.metric_id)}</strong> — ${esc(m.formula || m.description || "")}</div>`;
    });
    if (!body) body = `<pre style="font-size:.7rem">${esc(JSON.stringify(data, null, 2).slice(0, 1200))}</pre>`;
    return shell("Metrics catalog.", "Formula transparency.", "Version drift.", body);
  }

  init();
})();
