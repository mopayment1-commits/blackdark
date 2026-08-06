/* BLACKDARK — dashboard shell navigation + ⌘K + dock */
(function () {
  const body = () => document.getElementById("shellBody");
  const panes = () => document.querySelectorAll("[data-pane]");
  const railBtns = () => document.querySelectorAll("[data-nav]");

  function showPane(id) {
    panes().forEach((el) => el.classList.toggle("active", el.dataset.pane === id));
    railBtns().forEach((btn) => btn.classList.toggle("active", btn.dataset.nav === id));
    localStorage.setItem("bd_pane", id);
    document.dispatchEvent(new CustomEvent("bd:pane", { detail: { id } }));
    if (id === "markets" || id === "radar") {
      if (typeof loadMarket === "function") loadMarket();
      if (typeof loadOI === "function") loadOI();
      if (typeof loadWhales === "function") loadWhales(false);
      if (typeof loadArbitrage === "function") loadArbitrage(false);
    }
    if (id === "oracle") {
      if (typeof askOracle === "function") askOracle();
      if (typeof loadChart === "function") {
        setTimeout(() => {
          if (typeof initChart === "function" && !window.__bdChartReady) {
            initChart();
            window.__bdChartReady = true;
          }
          loadChart();
        }, 50);
      }
    }
    if (id === "alerts" && typeof loadInbox === "function") loadInbox();
    if (id === "portfolio" && typeof analyzePortfolio === "function") {
      /* keep local holdings UI */
    }
  }

  function openDock(title, html) {
    const b = body();
    const dock = document.getElementById("contextDock");
    const titleEl = document.getElementById("dockTitle");
    const bodyEl = document.getElementById("dockBody");
    if (!b || !dock) return;
    b.classList.add("dock-open");
    if (titleEl) titleEl.textContent = title || "Context";
    if (bodyEl) bodyEl.innerHTML = html || "";
  }

  function closeDock() {
    body()?.classList.remove("dock-open");
  }

  function toggleRail() {
    body()?.classList.toggle("rail-open");
  }

  function togglePrivacy() {
    document.documentElement.classList.toggle("privacy-on");
    const on = document.documentElement.classList.contains("privacy-on");
    localStorage.setItem("bd_privacy", on ? "1" : "0");
    const btn = document.getElementById("privacyBtn");
    if (btn) btn.classList.toggle("active", on);
  }

  function openCmdk() {
    document.getElementById("cmdkModal")?.classList.add("open");
    const input = document.getElementById("cmdkInput");
    if (input) {
      input.value = "";
      input.focus();
    }
  }

  function closeCmdk() {
    document.getElementById("cmdkModal")?.classList.remove("open");
  }

  function runCmdk(raw) {
    const q = (raw || "").trim();
    closeCmdk();
    if (!q) return;
    const lower = q.toLowerCase();
    const map = {
      today: "today",
      home: "today",
      markets: "markets",
      radar: "radar",
      oracle: "oracle",
      signals: "signals",
      portfolio: "portfolio",
      research: "research",
      alerts: "alerts",
      arena: "arena",
      stealth: "portfolio",
    };
    for (const [k, pane] of Object.entries(map)) {
      if (lower === k || lower === `open ${k}` || lower.startsWith(`go ${k}`)) {
        showPane(pane);
        return;
      }
    }
    const sym = (q.match(/\b([A-Z]{2,6})\b/) || [])[1];
    if (sym && typeof setSymbol === "function") {
      showPane("oracle");
      document.getElementById("symbol").value = sym;
      setSymbol(sym);
      return;
    }
    showPane("today");
    const ask = document.getElementById("askInput");
    if (ask) {
      ask.value = q;
      if (typeof askBlackdark === "function") askBlackdark();
    }
  }

  window.BDShell = { showPane, openDock, closeDock, toggleRail, togglePrivacy, openCmdk, closeCmdk, runCmdk };

  document.addEventListener("DOMContentLoaded", () => {
    railBtns().forEach((btn) => {
      btn.addEventListener("click", () => showPane(btn.dataset.nav));
    });
    document.getElementById("railToggle")?.addEventListener("click", toggleRail);
    document.getElementById("privacyBtn")?.addEventListener("click", togglePrivacy);
    document.getElementById("cmdkOpen")?.addEventListener("click", openCmdk);
    document.getElementById("dockClose")?.addEventListener("click", closeDock);
    document.getElementById("cmdkModal")?.addEventListener("click", (e) => {
      if (e.target.id === "cmdkModal") closeCmdk();
    });
    document.getElementById("cmdkForm")?.addEventListener("submit", (e) => {
      e.preventDefault();
      runCmdk(document.getElementById("cmdkInput")?.value);
    });
    document.querySelectorAll("[data-cmd]").forEach((el) => {
      el.addEventListener("click", () => runCmdk(el.dataset.cmd));
    });

    document.addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        openCmdk();
      }
      if (e.key === "Escape") {
        closeCmdk();
        closeDock();
      }
    });

    if (localStorage.getItem("bd_privacy") === "1") togglePrivacy();

    const hash = (location.hash || "").replace("#", "").toLowerCase();
    const hashMap = {
      stealth: "portfolio",
      mev: "portfolio",
      portfolio: "portfolio",
      oracle: "oracle",
      alerts: "alerts",
      today: "today",
      radar: "radar",
      markets: "markets",
      signals: "signals",
      research: "research",
      arena: "arena",
    };
    const fromHash = hashMap[hash];
    const saved = localStorage.getItem("bd_pane");
    showPane(fromHash || saved || "today");
  });
})();
