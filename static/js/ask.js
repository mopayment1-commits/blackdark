(function () {
  "use strict";
  const { esc } = window.BDDomSafe || { esc: (s) => String(s ?? "") };

  const EXAMPLES = [
    "What is Bitcoin's exchange flow?",
    "Show market conditions context",
    "Bitcoin on-chain metrics",
    "Latest Bitcoin news",
    "Should I buy Bitcoin?",
  ];

  function intentBadge(intent) {
    const map = {
      analytical: "ok",
      advisory_blocked: "warn",
      ambiguous: "warn",
      permission_denied: "err",
      unsupported: "err",
    };
    const cls = map[intent] || "warn";
    return `<span class="badge ${cls}">${esc(intent || "unknown")}</span>`;
  }

  function renderResult(data) {
    const el = document.getElementById("result");
    if (!data) {
      el.innerHTML = '<span class="meta">No response.</span>';
      return;
    }
    const intent = data.intent_type || "unknown";
    let html = intentBadge(intent);
    html += `<div class="meta">Query: ${esc(data.interpreted_query || "")}</div>`;
    if (data.redirect_message) {
      html += `<p>${esc(data.redirect_message)}</p>`;
    }
    if (data.message) {
      html += `<p>${esc(data.message)}</p>`;
    }
    if (data.tool_id) {
      html += `<div class="meta">Routed to: ${esc(data.tool_id)} (confidence: ${esc(data.routing_confidence)})</div>`;
    }
    if (data.display) {
      html += `<p><strong>${esc(data.display)}</strong></p>`;
    }
    html += `<pre>${esc(JSON.stringify(data, null, 2))}</pre>`;
    el.innerHTML = html;
  }

  async function ask(query) {
    const el = document.getElementById("result");
    el.innerHTML = '<span class="meta">Loading…</span>';
    const url = "/api/platform/intelligence-ledger/ux-layer/natural-language?query="
      + encodeURIComponent(query);
    const res = await fetch(url);
    const data = await res.json();
    renderResult(data);
  }

  function init() {
    const input = document.getElementById("queryInput");
    const btn = document.getElementById("askBtn");
    const examples = document.getElementById("examples");

    examples.innerHTML = EXAMPLES.map((q) =>
      `<button type="button" data-q="${esc(q)}">${esc(q)}</button>`
    ).join("");

    examples.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-q]");
      if (!btn) return;
      const q = btn.getAttribute("data-q");
      input.value = q;
      ask(q);
    });

    btn.addEventListener("click", () => {
      const q = input.value.trim();
      if (q) ask(q);
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const q = input.value.trim();
        if (q) ask(q);
      }
    });
  }

  init();
})();
