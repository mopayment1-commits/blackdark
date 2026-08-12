/**
 * BLACKDARK — coin detail page (executable JS kept out of Jinja templates
 * so Sonar/JS parsers analyze real source; boot via data-coin-id).
 */
(function () {
  "use strict";

  function bootCoinId() {
    const root = document.getElementById("coinPage");
    if (!root) return "";
    return root.getAttribute("data-coin-id") || "";
  }

  const coinId = bootCoinId();
  const fmt = (n, d = 2) =>
    n == null ? "—" : Number(n).toLocaleString(undefined, { maximumFractionDigits: d });

  /** Plain text only via textContent — never regex strip / never assign untrusted HTML. */
  function plainText(s, maxLen) {
    const el = document.createElement("div");
    el.textContent = String(s ?? "");
    const t = el.textContent || "";
    return maxLen ? t.slice(0, maxLen) : t;
  }

  let chart, series;

  async function load() {
    const res = await fetch(`/api/platform/market/coin/${encodeURIComponent(coinId)}`);
    const c = await res.json();
    if (!c.available) {
      const head = document.getElementById("head");
      head.textContent = "";
      const miss = document.createElement("div");
      miss.className = "loading";
      miss.textContent = "Coin not found";
      head.appendChild(miss);
      return;
    }
    const name = plainText(c.name, 80);
    const symbol = plainText(c.symbol, 24);
    document.title = `BLACKDARK — ${name} (${symbol})`;
    const head = document.getElementById("head");
    head.textContent = "";
    const h1 = document.createElement("h1");
    h1.appendChild(document.createTextNode(name + " "));
    const symSpan = document.createElement("span");
    symSpan.style.color = "var(--muted)";
    symSpan.textContent = symbol;
    h1.appendChild(symSpan);
    const p = document.createElement("p");
    p.style.color = "var(--muted)";
    p.style.marginTop = ".25rem";
    p.textContent = `$${fmt(c.price_usd)} · MCap $${fmt(c.market_cap_usd, 0)}`;
    head.appendChild(h1);
    head.appendChild(p);
    document.getElementById("desc").textContent = plainText(c.description, 600);
    const ch = c.change_24h_pct || 0;
    const statsEl = document.getElementById("stats");
    statsEl.textContent = "";
    [
      ["24h", `${fmt(ch)}%`, ch >= 0 ? "pos" : "neg"],
      ["7d", `${fmt(c.change_7d_pct)}%`, (c.change_7d_pct || 0) >= 0 ? "pos" : "neg"],
      ["30d", `${fmt(c.change_30d_pct)}%`, (c.change_30d_pct || 0) >= 0 ? "pos" : "neg"],
      ["Vol 24h", `$${fmt(c.volume_24h_usd, 0)}`, ""],
      ["ATH", `$${fmt(c.ath_usd)}`, ""],
      ["Circulating", fmt(c.circulating_supply, 0), ""],
    ].forEach(([l, v, cls]) => {
      const box = document.createElement("div");
      box.className = "stat";
      const lab = document.createElement("label");
      lab.textContent = l;
      const strong = document.createElement("strong");
      if (cls) strong.className = cls;
      strong.textContent = v;
      box.appendChild(lab);
      box.appendChild(strong);
      statsEl.appendChild(box);
    });

    const el = document.getElementById("chart");
    chart = LightweightCharts.createChart(el, {
      layout: { background: { color: "#111118" }, textColor: "#a1a1aa" },
      grid: { vertLines: { color: "#2a2a35" }, horzLines: { color: "#2a2a35" } },
    });
    series = chart.addAreaSeries({
      lineColor: "#22d3ee",
      topColor: "rgba(34,211,238,.25)",
      bottomColor: "rgba(34,211,238,0)",
    });
    const spark = c.sparkline_7d || [];
    if (spark.length) {
      const now = Math.floor(Date.now() / 1000);
      const step = 3600;
      series.setData(
        spark.map((pt, i) => ({ time: now - (spark.length - i) * step, value: pt }))
      );
      chart.timeScale().fitContent();
    } else {
      const sym = c.symbol;
      const k = await fetch(
        `/api/market/klines?symbol=${encodeURIComponent(sym)}&interval=1h&limit=120`
      );
      const payload = await k.json();
      const rows = payload.klines || [];
      series.setData(rows.map((r) => ({ time: Math.floor(r[0] / 1000), value: +r[4] })));
      chart.timeScale().fitContent();
    }
  }

  if (coinId) {
    load();
  }
})();
