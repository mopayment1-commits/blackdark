(function () {
  const { esc } = window.BDDomSafe || { esc: (s) => String(s ?? "") };
  const waves = [
    { id: "A", label: "Wave A — Foundations" },
    { id: "B", label: "Wave B — Alerts & Domains" },
    { id: "C", label: "Wave C — Market depth" },
    { id: "D", label: "Wave D — Remaining internal" },
  ];
  let catalog = [];
  let activeWave = "A";
  let selectedId = null;

  const tabsEl = document.getElementById("tabs");
  const listEl = document.getElementById("capList");
  const listState = document.getElementById("listState");
  const detailTitle = document.getElementById("detailTitle");
  const detailState = document.getElementById("detailState");
  const detailOut = document.getElementById("detailOut");
  const execBtn = document.getElementById("execBtn");
  const waveDod = document.getElementById("waveDod");

  function setListState(msg, cls) {
    listState.textContent = msg;
    listState.className = "state" + (cls ? " " + cls : "");
  }

  function setDetailState(msg, cls) {
    detailState.textContent = msg;
    detailState.className = "state" + (cls ? " " + cls : "");
    detailOut.hidden = true;
  }

  function renderTabs() {
    tabsEl.innerHTML = "";
    waves.forEach((w) => {
      const b = document.createElement("button");
      b.className = "tab" + (w.id === activeWave ? " active" : "");
      b.textContent = w.label;
      b.onclick = () => {
        activeWave = w.id;
        renderTabs();
        loadWaveDod();
        renderList();
      };
      tabsEl.appendChild(b);
    });
  }

  function waveIds() {
    return fetch("/api/cap646/wave/" + activeWave + "/ids")
      .then((r) => r.json())
      .then((d) => d.ids || []);
  }

  async function loadCatalog() {
    setListState("Loading catalog…");
    try {
      const r = await fetch("/api/cap646/catalog?limit=646");
      const d = await r.json();
      catalog = d.items || [];
      setListState("");
      renderTabs();
      await loadWaveDod();
      renderList();
    } catch (e) {
      setListState("Failed to load catalog.", "error");
    }
  }

  async function renderList() {
    listEl.innerHTML = "";
    let ids = [];
    try {
      ids = await waveIds();
    } catch (e) {
      setListState("Failed to load wave IDs.", "error");
      return;
    }
    if (!ids.length) {
      setListState("No capabilities in this wave.", "empty");
      return;
    }
    setListState("");
    const map = Object.fromEntries(catalog.map((c) => [c.id, c]));
    ids.forEach((id) => {
      const row = map[id] || { id, capability: "Unknown", track: "?" };
      const div = document.createElement("div");
      div.className = "item" + (id === selectedId ? " active" : "");
      div.innerHTML =
        `<span>#${esc(id)}</span> ${esc(row.capability)}` +
        `<span class="badge">${esc(row.track || "")}</span>`;
      div.onclick = () => selectCapability(id, row);
      listEl.appendChild(div);
    });
  }

  function selectCapability(id, row) {
    selectedId = id;
    detailTitle.textContent = `#${id} — ${row.capability || ""}`;
    setDetailState("Ready to execute with backend entitlements + evidence footer.");
    execBtn.disabled = false;
    renderList();
  }

  execBtn.onclick = async () => {
    if (!selectedId) return;
    execBtn.disabled = true;
    setDetailState("Executing…");
    detailOut.hidden = true;
    try {
      const r = await fetch(`/api/cap646/${selectedId}?symbol=BTC`);
      const d = await r.json();
      if (!r.ok || d.success === false) {
        setDetailState(d.error || d.entitlement?.reason || "Execution failed.", "error");
      } else {
        setDetailState("VERIFIED response received.");
      }
      detailOut.hidden = false;
      detailOut.textContent = JSON.stringify(d, null, 2);
    } catch (e) {
      setDetailState("Network error during execution.", "error");
    } finally {
      execBtn.disabled = false;
    }
  };

  async function loadWaveDod() {
    waveDod.textContent = "Loading DoD…";
    try {
      const r = await fetch("/api/cap646/wave/" + activeWave + "/dod");
      const d = await r.json();
      waveDod.textContent = JSON.stringify(d, null, 2);
    } catch (e) {
      waveDod.textContent = "DoD API unavailable";
    }
  }

  loadCatalog();
})();
