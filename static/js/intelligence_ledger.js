(function () {
  "use strict";
  const { esc } = window.BDDomSafe || { esc: (s) => String(s ?? "") };

  let catalog = [];
  let layers = [];
  let activeLayer = "all";
  let selectedModule = null;
  let activeView = "formatted";

  const moduleList = document.getElementById("moduleList");
  const layerTabs = document.getElementById("layerTabs");
  const searchInput = document.getElementById("searchInput");
  const panelHeader = document.getElementById("panelHeader");
  const panelTitle = document.getElementById("panelTitle");
  const panelMeta = document.getElementById("panelMeta");
  const paramToolbar = document.getElementById("paramToolbar");
  const panelBody = document.getElementById("panelBody");
  const readinessEl = document.getElementById("readiness");

  function setPanelState(html, cls) {
    panelBody.innerHTML = html;
    panelBody.className = "panel-body state" + (cls ? " " + cls : "");
  }

  function evidenceBadge(cls) {
    return `<span class="evidence ${esc(cls)}">${esc(cls)}</span>`;
  }

  function formatValue(v) {
    if (v === null || v === undefined) return '<span style="color:var(--muted)">غير متوفر</span>';
    if (typeof v === "boolean") return v ? "نعم" : "لا";
    if (typeof v === "number") return esc(v.toLocaleString());
    if (typeof v === "object") return esc(JSON.stringify(v));
    return esc(String(v));
  }

  function renderKeyValues(obj, depth) {
    if (!obj || typeof obj !== "object" || depth > 2) return "";
    const skip = new Set(["ok", "timestamp", "latency_ms", "routes", "sub_modules"]);
    let html = '<div class="kv">';
    Object.entries(obj).forEach(([k, v]) => {
      if (skip.has(k)) return;
      if (typeof v === "object" && v !== null && !Array.isArray(v) && depth < 2) {
        html += `<div class="kv-item" style="grid-column:1/-1"><div class="k">${esc(k)}</div>${renderKeyValues(v, depth + 1)}</div>`;
      } else {
        html += `<div class="kv-item"><div class="k">${esc(k)}</div><div class="v">${formatValue(v)}</div></div>`;
      }
    });
    html += "</div>";
    return html;
  }

  function renderFormatted(data) {
    const ev = data.evidence_class || data.evidence_metadata?.class || "BACKTESTED";
    let html = `<div class="card"><h3>النتيجة ${evidenceBadge(ev)}</h3>`;

    const display =
      data.display ||
      data.analysis?.display ||
      data.hub?.title ||
      (data.ok === false ? (data.user_message || data.error) : null);

    if (display) {
      html += `<div class="display-line">${esc(display)}</div>`;
    }

    if (data.disclaimer || data.compliance_footer?.legal) {
      html += `<div class="disclaimer">${esc(data.disclaimer || data.compliance_footer?.legal)}</div>`;
    }

    if (data.sub_modules) {
      Object.entries(data.sub_modules).forEach(([key, mod]) => {
        if (key === "tasks_not_tickets" || !mod || typeof mod !== "object") return;
        html += `<div class="card"><h3>${esc(key.replace(/_/g, " "))}</h3>`;
        if (mod.display) html += `<div class="display-line">${esc(mod.display)}</div>`;
        html += renderKeyValues(mod, 0);
        html += "</div>";
      });
    } else if (data.analysis) {
      html += renderKeyValues(data.analysis, 0);
    } else if (data.factor_alignment_indicators) {
      data.factor_alignment_indicators.forEach((lens) => {
        html += `<div class="card"><h3>${esc(lens.lens)}</h3><div class="display-line">${esc(lens.display || "")}</div></div>`;
      });
      if (data.observed_conditions?.display) {
        html += `<div class="card"><h3>الظروف الملاحظة</h3><div class="display-line">${esc(data.observed_conditions.display)}</div></div>`;
      }
    } else if (data.exposure_metrics) {
      html += renderKeyValues(data.exposure_metrics, 0);
      if (data.pnl?.pnl_disclaimer) {
        html += `<div class="disclaimer">${esc(data.pnl.pnl_disclaimer)}</div>`;
      }
    } else {
      html += renderKeyValues(data, 0);
    }

    html += "</div>";
    if (data.ok === false) {
      html = `<div class="card" style="border-color:var(--err)"><h3>غير متوفر</h3><div class="display-line">${esc(data.user_message || data.error || "البيانات غير متوفرة")}</div></div>` + html;
    }
    return html;
  }

  function filteredCatalog() {
    const q = (searchInput.value || "").toLowerCase().trim();
    return catalog.filter((m) => {
      if (activeLayer !== "all" && m.layer !== activeLayer) return false;
      if (!q) return true;
      return (
        m.title.toLowerCase().includes(q) ||
        m.module_id.toLowerCase().includes(q) ||
        (m.layer_label || "").toLowerCase().includes(q)
      );
    });
  }

  function renderLayers() {
    layerTabs.innerHTML = "";
    const allBtn = document.createElement("button");
    allBtn.className = "layer-btn" + (activeLayer === "all" ? " active" : "");
    allBtn.textContent = "الكل";
    allBtn.onclick = () => { activeLayer = "all"; renderLayers(); renderModuleList(); };
    layerTabs.appendChild(allBtn);

    layers.forEach((l) => {
      const b = document.createElement("button");
      b.className = "layer-btn" + (activeLayer === l.layer ? " active" : "");
      b.textContent = `${l.label} (${l.module_count})`;
      b.onclick = () => { activeLayer = l.layer; renderLayers(); renderModuleList(); };
      layerTabs.appendChild(b);
    });
  }

  function renderModuleList() {
    const items = filteredCatalog();
    if (!items.length) {
      moduleList.innerHTML = '<div class="state empty">لا توجد وحدات مطابقة.</div>';
      return;
    }
    moduleList.innerHTML = "";
    items.forEach((m) => {
      const div = document.createElement("div");
      div.className = "module-item" + (selectedModule?.module_id === m.module_id ? " active" : "");
      div.innerHTML = `<div class="title">${esc(m.title)}</div><div class="meta">${esc(m.layer_label)} · ${esc(m.data_source)}</div>`;
      div.onclick = () => selectModule(m);
      moduleList.appendChild(div);
    });
  }

  function buildQueryString(mod) {
    const params = mod.query_params || [];
    const parts = [];
    params.forEach((p) => {
      const el = document.getElementById("param_" + p.name);
      const val = el ? el.value : p.default;
      if (val) parts.push(encodeURIComponent(p.name) + "=" + encodeURIComponent(val));
    });
    return parts.length ? "?" + parts.join("&") : "";
  }

  function renderParams(mod) {
    paramToolbar.innerHTML = "";
    (mod.query_params || []).forEach((p) => {
      const label = document.createElement("label");
      label.textContent = p.label || p.name;
      label.style.fontSize = ".75rem";
      label.style.color = "var(--muted)";
      const input = document.createElement("input");
      input.id = "param_" + p.name;
      input.value = p.default || "";
      input.placeholder = p.label || p.name;
      paramToolbar.appendChild(label);
      paramToolbar.appendChild(input);
    });
    const loadBtn = document.createElement("button");
    loadBtn.className = "btn";
    loadBtn.textContent = "تحميل البيانات";
    loadBtn.onclick = () => loadPanel(mod);
    paramToolbar.appendChild(loadBtn);
    if (mod.status_path) {
      const stBtn = document.createElement("button");
      stBtn.className = "btn secondary";
      stBtn.textContent = "الحالة";
      stBtn.onclick = () => fetchPath(mod.status_path, mod);
      paramToolbar.appendChild(stBtn);
    }
  }

  async function fetchPath(path, mod) {
    setPanelState('<div class="state"><span class="spinner"></span> جاري التحميل…</div>');
    try {
      const url = path + (path === mod.panel_path ? buildQueryString(mod) : "");
      const res = await fetch(url);
      const data = await res.json();
      renderPanelData(data, mod);
    } catch (e) {
      setPanelState('<div class="state error">فشل الاتصال بالخادم. حاول مرة أخرى.</div>', "error");
    }
  }

  function loadPanel(mod) {
    if (!mod.panel_path) {
      setPanelState('<div class="state error">لا يوجد مسار عرض لهذه الوحدة.</div>', "error");
      return;
    }
    fetchPath(mod.panel_path, mod);
  }

  function renderPanelData(data, mod) {
    panelBody.className = "panel-body";
    if (activeView === "raw") {
      panelBody.innerHTML = `<pre class="raw">${esc(JSON.stringify(data, null, 2))}</pre>`;
      return;
    }
    panelBody.innerHTML = renderFormatted(data);
  }

  function selectModule(mod) {
    selectedModule = mod;
    renderModuleList();
    panelHeader.hidden = false;
    panelTitle.textContent = mod.title;
    panelMeta.innerHTML = `${esc(mod.layer_label)} · ${esc(mod.module_id)} · ${evidenceBadge(mod.evidence_class_default)}`;
    renderParams(mod);
    loadPanel(mod);
  }

  async function loadHub() {
    try {
      const res = await fetch("/api/intelligence-ledger/hub");
      const data = await res.json();
      catalog = data.catalog || [];
      layers = data.layers || [];
      renderReadiness(data.launch_readiness);
      renderLayers();
      renderModuleList();
    } catch (e) {
      moduleList.innerHTML = '<div class="state error">فشل تحميل الكتالوج.</div>';
    }
  }

  function renderReadiness(r) {
    if (!r) return;
    readinessEl.innerHTML = "";
    const verdict = r.verdict || "NOT READY";
    const chip = document.createElement("div");
    chip.className = "chip " + (verdict === "VERIFIED COMPLETE" ? "ok" : "warn");
    chip.textContent = `جاهزية الإطلاق: ${verdict}`;
    readinessEl.appendChild(chip);

    const modChip = document.createElement("div");
    modChip.className = "chip ok";
    modChip.textContent = `${r.intelligence_ledger?.module_count || 0} وحدة ذكاء`;
    readinessEl.appendChild(modChip);

    if (r.summary) {
      const userChip = document.createElement("div");
      userChip.className = "chip " + (r.summary.user_can_use_intelligence_ledger ? "ok" : "warn");
      userChip.textContent = r.summary.user_can_use_intelligence_ledger ? "واجهة المستخدم جاهزة" : "واجهة غير جاهزة";
      readinessEl.appendChild(userChip);
    }
  }

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.onclick = () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      activeView = tab.dataset.view;
      if (selectedModule) loadPanel(selectedModule);
    };
  });

  searchInput.addEventListener("input", renderModuleList);
  loadHub();
})();
