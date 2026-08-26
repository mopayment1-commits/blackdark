(function () {
  "use strict";
  const { esc } = window.BDDomSafe || { esc: (s) => String(s ?? "") };

  const EXAMPLES = [
    { q: "Show market conditions context", tier: "guest" },
    { q: "Bitcoin on-chain metrics", tier: "guest" },
    { q: "Latest Bitcoin news", tier: "guest" },
    { q: "What is Bitcoin's exchange flow?", tier: "authenticated" },
    { q: "Should I buy Bitcoin?", tier: "guest" },
  ];

  let busy = false;

  function intentBadge(intent) {
    const map = {
      analytical: "ok",
      advisory_blocked: "warn",
      ambiguous: "warn",
      permission_denied: "err",
      unsupported: "err",
      empty_query: "warn",
    };
    const cls = map[intent] || "warn";
    const labels = {
      analytical: "تحليلي",
      advisory_blocked: "نصيحة محظورة",
      ambiguous: "غامض",
      permission_denied: "صلاحية مطلوبة",
      empty_query: "استعلام فارغ",
    };
    return `<span class="badge ${cls}">${esc(labels[intent] || intent || "unknown")}</span>`;
  }

  function formatValue(v) {
    if (v === null || v === undefined) return '<span style="color:var(--muted)">غير متوفر</span>';
    if (typeof v === "boolean") return v ? "نعم" : "لا";
    if (typeof v === "number") return esc(v.toLocaleString());
    if (typeof v === "object") return esc(JSON.stringify(v));
    return esc(String(v));
  }

  function renderNewsArticles(articles) {
    if (!articles || !articles.length) {
      return '<div class="meta">لا توجد أخبار متاحة حالياً.</div>';
    }
    return articles.map((a) => {
      const link = a.source_url
        ? `<a href="${esc(a.source_url)}" target="_blank" rel="noopener noreferrer">${esc(a.headline)}</a>`
        : esc(a.headline);
      const tags = (a.tags || []).map((t) => `<span class="tag">${esc(t)}</span>`).join("");
      return `<div class="news-item">${link}<div class="meta">${esc(a.source || "")} · ${esc(a.published_at || "")}</div><div class="display-line">${esc(a.summary || "")}</div>${tags}</div>`;
    }).join("");
  }

  function renderAnalyticalResult(data) {
    const result = data.analytical_result || {};
    const tool = data.tool_id || "";
    let html = `<div class="card"><h3>نتيجة التحليل — ${esc(tool)}</h3>`;
    html += `<div class="display-line">${esc(result.display || data.display || "تم التوجيه بنجاح")}</div>`;

    if (result.articles) {
      html += renderNewsArticles(result.articles);
    } else if (result.sub_modules) {
      const lib = result.sub_modules["574_network_data_pro_api"];
      if (lib && lib.network_metrics) {
        html += '<div class="kv">';
        lib.network_metrics.slice(0, 6).forEach((m) => {
          html += `<div class="kv-item"><div class="k">${esc(m.name || m.metric_id)}</div><div class="v">${formatValue(m.value)}</div></div>`;
        });
        html += "</div>";
      } else if (result.factor_alignment_indicators) {
        result.factor_alignment_indicators.forEach((lens) => {
          html += `<div class="meta">${esc(lens.lens)}: ${esc(lens.display || "")}</div>`;
        });
      } else if (result.observed_conditions) {
        html += `<div class="meta">${esc(result.observed_conditions.display || "")}</div>`;
      }
    } else if (result.data_redirect) {
      html += `<div class="meta">${esc(result.data_redirect.display || "بيانات التدفق")}</div>`;
    }

    if (data.evidence_metadata || data.evidence_class) {
      const ev = data.evidence_class || data.evidence_metadata?.class || "BACKTESTED";
      html += `<div class="meta">Evidence: ${esc(ev)}</div>`;
    }
    html += "</div>";
    return html;
  }

  function renderResult(data) {
    const el = document.getElementById("result");
    if (!data) {
      el.innerHTML = '<div class="error-box">لا توجد استجابة.</div>';
      return;
    }

    const intent = data.intent_type || "unknown";
    let html = intentBadge(intent);
    html += `<div class="meta">الاستعلام: ${esc(data.interpreted_query || "")}</div>`;

    if (intent === "advisory_blocked") {
      html += `<div class="card"><h3>إعادة توجيه — بيانات فقط</h3>`;
      html += `<div class="display-line">${esc(data.redirect_message || "")}</div>`;
      html += `<div class="meta">${esc(data.display || "")}</div></div>`;
    } else if (intent === "permission_denied") {
      html += `<div class="error-box">${esc(data.message || "هذا التحليل يتطلب تسجيل الدخول.")}</div>`;
      html += `<div class="meta"><a href="/login" style="color:var(--accent)">تسجيل الدخول</a> للوصول إلى ${esc(data.tool_id || "هذا التحليل")}</div>`;
    } else if (data.safe_fallback) {
      html += `<div class="card"><h3>توضيح مطلوب</h3><div class="display-line">${esc(data.display || data.message || "")}</div></div>`;
      if (data.suggested_tools && data.suggested_tools.length) {
        html += `<div class="meta">جرّب: ${esc(data.suggested_tools.join(", "))}</div>`;
      }
    } else if (intent === "analytical") {
      html += renderAnalyticalResult(data);
      if (data.routing_confidence != null) {
        html += `<div class="meta">ثقة التوجيه: ${esc(data.routing_confidence)}</div>`;
      }
    } else if (data.display || data.message) {
      html += `<div class="display-line">${esc(data.display || data.message)}</div>`;
    }

    if (data.disclaimer || data.compliance_footer?.legal) {
      html += `<div class="disclaimer">${esc(data.disclaimer || data.compliance_footer.legal)}</div>`;
    }

    html += `<details><summary>تفاصيل تقنية (JSON)</summary><pre>${esc(JSON.stringify(data, null, 2))}</pre></details>`;
    el.innerHTML = html;
  }

  function setLoading(on) {
    busy = on;
    const el = document.getElementById("result");
    const btn = document.getElementById("askBtn");
    const input = document.getElementById("queryInput");
    btn.disabled = on;
    input.disabled = on;
    if (on) {
      el.innerHTML = '<div class="spinner"></div><div class="meta" style="text-align:center">جاري التحليل…</div>';
    }
  }

  async function ask(query, userTier) {
    if (busy || !query) return;
    setLoading(true);
    try {
      const url = "/api/platform/intelligence-ledger/ux-layer/natural-language?query="
        + encodeURIComponent(query) + "&user_tier=" + encodeURIComponent(userTier || "guest");
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error("HTTP " + res.status);
      }
      const data = await res.json();
      renderResult(data);
    } catch (err) {
      document.getElementById("result").innerHTML =
        `<div class="error-box">تعذر تحميل النتيجة. حاول مرة أخرى.<br><span class="meta">${esc(err.message || "network_error")}</span></div>`;
    } finally {
      setLoading(false);
    }
  }

  async function loadLiveStrip() {
    const el = document.getElementById("liveStrip");
    try {
      const res = await fetch("/api/live-market/strip");
      const strip = await res.json();
      if (!strip.assets || !strip.assets.length) {
        el.innerHTML = '<div class="live-item"><div class="label">السوق</div><div class="val">غير متوفر</div></div>';
        return;
      }
      el.innerHTML = strip.assets.map((a) => {
        const price = a.price_usd != null && a.available !== false
          ? "$" + Number(a.price_usd).toLocaleString()
          : "غير متوفر";
        const chg = a.change_24h_pct != null ? Number(a.change_24h_pct).toFixed(2) + "%" : "";
        return `<div class="live-item"><div class="label">${esc(a.asset)} LIVE</div><div class="val">${esc(price)} ${chg ? esc(chg) : ""}</div></div>`;
      }).join("");
    } catch {
      el.innerHTML = '<div class="live-item"><div class="label">السوق</div><div class="val">غير متوفر</div></div>';
    }
  }

  function init() {
    const input = document.getElementById("queryInput");
    const btn = document.getElementById("askBtn");
    const examples = document.getElementById("examples");

    examples.innerHTML = EXAMPLES.map((ex) =>
      `<button type="button" data-q="${esc(ex.q)}" data-tier="${esc(ex.tier)}">${esc(ex.q)}</button>`
    ).join("");

    examples.addEventListener("click", (e) => {
      const target = e.target.closest("button[data-q]");
      if (!target) return;
      const q = target.getAttribute("data-q");
      const tier = target.getAttribute("data-tier") || "guest";
      input.value = q;
      ask(q, tier);
    });

    btn.addEventListener("click", () => {
      const q = input.value.trim();
      if (q) ask(q, "guest");
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const q = input.value.trim();
        if (q) ask(q, "guest");
      }
    });

    loadLiveStrip();
  }

  init();
})();
