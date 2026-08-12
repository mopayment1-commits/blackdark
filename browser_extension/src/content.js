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

  function setText(el, value) {
    if (!el) return;
    el.textContent = value == null ? "" : String(value);
  }

  function ensurePanel() {
    let el = document.getElementById(PANEL_ID);
    if (el) return el;
    el = document.createElement("div");
    el.id = PANEL_ID;

    const head = document.createElement("div");
    head.className = "bd-head";
    const title = document.createElement("strong");
    setText(title, "BLACKDARK");
    const refreshBtn = document.createElement("button");
    refreshBtn.type = "button";
    refreshBtn.className = "bd-refresh";
    refreshBtn.title = "Refresh";
    setText(refreshBtn, "↻");
    const closeBtn = document.createElement("button");
    closeBtn.type = "button";
    closeBtn.className = "bd-close";
    closeBtn.title = "Close";
    setText(closeBtn, "×");
    head.append(title, refreshBtn, closeBtn);

    const body = document.createElement("div");
    body.className = "bd-body";
    setText(body, "Loading…");

    const foot = document.createElement("div");
    foot.className = "bd-foot";
    setText(foot, "Not financial advice · Public Accuracy Ledger");

    el.append(head, body, foot);
    document.documentElement.appendChild(el);
    closeBtn.addEventListener("click", () => el.remove());
    refreshBtn.addEventListener("click", () => refresh());
    return el;
  }

  function render(payload, error) {
    const el = ensurePanel();
    const body = el.querySelector(".bd-body");
    body.replaceChildren();
    if (error) {
      const err = document.createElement("div");
      err.className = "bd-err";
      setText(err, error);
      body.append(err);
      return;
    }
    const action = String(payload.action || "WAIT").toUpperCase();
    const actionEl = document.createElement("div");
    actionEl.className = `bd-action ${/^[A-Z_.…]{1,16}$/.test(action) ? action : "WAIT"}`;
    setText(actionEl, action);
    const sentence = document.createElement("div");
    sentence.className = "bd-sentence";
    setText(sentence, payload.sentence || "");
    const meta = document.createElement("div");
    meta.className = "bd-meta";
    const pid = payload.predictionId != null ? ` · id ${payload.predictionId}` : "";
    setText(meta, `${payload.asset || ""} · score ${payload.score ?? "—"}${pid}`);
    body.append(actionEl, sentence, meta);
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

  if (!window.__bdOracleBooted) {
    window.__bdOracleBooted = true;
    refresh();
    let last = location.href;
    setInterval(() => {
      if (location.href !== last) {
        last = location.href;
        refresh();
      }
    }, 2500);
  }
})();
