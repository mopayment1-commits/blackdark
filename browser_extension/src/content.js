(() => {
  const PANEL_ID = "blackdark-oqs-overlay";

  function detectSymbol() {
    const path = location.pathname + location.search + " " + document.title;
    const patterns = [
      /\b([A-Z]{2,10})[-_/]?(USDT|USD|PERP)\b/i,
      /\/trade\/([A-Z0-9]{2,12})/i,
      /symbol=([A-Z0-9]{2,12})/i,
      /\b(BTC|ETH|SOL|BNB|XRP|DOGE|ADA|AVAX|LINK|DOT)\b/i,
    ];
    let m = null;
    for (const re of patterns) {
      m = re.exec(path);
      if (m) break;
    }
    return (m && (m[1] || m[0])) || "BTC";
  }

  function ensurePanel() {
    let el = document.getElementById(PANEL_ID);
    if (el) return el;
    el = document.createElement("div");
    el.id = PANEL_ID;
    el.innerHTML = `
      <div class="bd-head">
        <strong>BLACKDARK</strong>
        <button type="button" class="bd-refresh" title="Refresh">↻</button>
        <button type="button" class="bd-close" title="Close">×</button>
      </div>
      <div class="bd-body">Loading…</div>
      <div class="bd-foot">Not financial advice · Public Accuracy Ledger</div>
    `;
    document.documentElement.appendChild(el);
    el.querySelector(".bd-close").addEventListener("click", () => el.remove());
    el.querySelector(".bd-refresh").addEventListener("click", () => refresh());
    return el;
  }

  function render(payload, error) {
    const el = ensurePanel();
    const body = el.querySelector(".bd-body");
    if (error) {
      body.innerHTML = `<div class="bd-err">${escapeHtml(error)}</div>`;
      return;
    }
    const action = String(payload.action || "WAIT").toUpperCase();
    body.innerHTML = `
      <div class="bd-action ${action}">${escapeHtml(action)}</div>
      <div class="bd-sentence">${escapeHtml(payload.sentence || "")}</div>
      <div class="bd-meta">${escapeHtml(payload.asset || "")} · score ${payload.score ?? "—"}
        ${payload.predictionId != null ? ` · id ${payload.predictionId}` : ""}</div>
    `;
  }

  function escapeHtml(s) {
    return String(s)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll(""", "&quot;");
  }

  async function refresh() {
    const symbol = detectSymbol();
    render({ action: "…", sentence: `Asking Oracle for ${symbol}…`, asset: symbol, score: "—" });
    try {
      const res = await chrome.runtime.sendMessage({ type: "ORACLE_LOOKUP", symbol });
      if (!res?.ok) throw new Error(res?.error || "lookup failed");
      render(res.payload);
    } catch (err) {
      render(null, String(err.message || err));
    }
  }

  // Boot once per page
  if (!window.__bdOracleBooted) {
    window.__bdOracleBooted = true;
    refresh();
    // Soft refresh when URL changes (SPA)
    let last = location.href;
    setInterval(() => {
      if (location.href !== last) {
        last = location.href;
        refresh();
      }
    }, 2500);
  }
})();
