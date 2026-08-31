(function () {
  "use strict";
  const { esc } = window.BDDomSafe || { esc: (s) => String(s ?? "") };

  async function load() {
    const [hubRes, stdRes] = await Promise.all([
      fetch("/api/intelligence-ledger/hub"),
      fetch("/api/institutional-standards/status"),
    ]);
    const hub = await hubRes.json();
    const std = await stdRes.json().catch(() => ({}));
    const readiness = hub.launch_readiness || {};
    const journeys = hub.user_journeys || std.user_journeys || [];

    const eng = readiness.engineering_verdict || "NOT_READY";
    const verdictEl = document.getElementById("verdict");
    verdictEl.textContent = eng === "ENGINEERING_READY"
      ? "جاهز هندسياً — المستخدم يمكنه استخدام المنصة"
      : "قيد الإكمال الهندسي";
    verdictEl.className = "verdict " + (eng === "ENGINEERING_READY" ? "ok" : "warn");

    renderLiveStrip(hub.live_market_strip);
    renderJourneys(journeys);
    renderChecks(readiness.checks || []);
  }

  function renderLiveStrip(strip) {
    const el = document.getElementById("liveStrip");
    if (!strip || !strip.assets) {
      el.innerHTML = '<div class="live-item"><div class="label">السوق</div><div class="val">غير متوفر</div></div>';
      return;
    }
    el.innerHTML = strip.assets.map((a) => {
      const price = a.price_usd != null ? "$" + Number(a.price_usd).toLocaleString() : "غير متوفر";
      const chg = a.change_24h_pct != null ? a.change_24h_pct.toFixed(2) + "%" : "";
      return `<div class="live-item"><div class="label">${esc(a.asset)} LIVE</div><div class="val">${esc(price)} ${chg ? esc(chg) : ""}</div></div>`;
    }).join("");
  }

  function renderJourneys(journeys) {
    const el = document.getElementById("journeys");
    el.innerHTML = journeys.map((j) =>
      `<a class="card" href="${esc(j.path)}"><h3>${esc(j.title)}</h3><p>${esc(j.description)}</p></a>`
    ).join("");
  }

  function renderChecks(checks) {
    const internal = document.getElementById("internalChecks");
    const external = document.getElementById("externalChecks");
    internal.innerHTML = "";
    external.innerHTML = "";
    checks.forEach((c) => {
      const row = document.createElement("div");
      row.className = "check";
      const status = c.passed
        ? '<span class="pass">✓ PASS</span>'
        : (c.external ? '<span class="ext">○ EXTERNAL</span>' : '<span class="fail">✗ FAIL</span>');
      row.innerHTML = `<span>${esc(c.label)}</span>${status}`;
      (c.external ? external : internal).appendChild(row);
    });
  }

  load().catch(() => {
    document.getElementById("verdict").textContent = "فشل تحميل حالة الإطلاق";
  });
})();
