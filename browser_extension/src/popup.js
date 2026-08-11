import { getApiBase } from "./api.js";

const out = document.getElementById("out");
const symbolEl = document.getElementById("symbol");

async function ask() {
  const symbol = symbolEl.value || "BTC";
  out.innerHTML = '<span class="sub">Asking Oracle…</span>';
  try {
    const res = await chrome.runtime.sendMessage({ type: "ORACLE_LOOKUP", symbol });
    if (!res?.ok) throw new Error(res?.error || "lookup failed");
    const p = res.payload;
    const action = String(p.action || "WAIT").toUpperCase();
    out.innerHTML = `
      <div class="verdict ${action}">${action}</div>
      <div class="sentence">${escapeHtml(p.sentence)}</div>
      <div class="meta">Score ${p.score ?? "—"} · ${p.asset}
        ${p.predictionId != null ? ` · id ${p.predictionId}` : ""}</div>
    `;
  } catch (err) {
    out.innerHTML = `<div class="err">${escapeHtml(String(err.message || err))}</div>`;
  }
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll(""", "&quot;");
}

document.getElementById("ask").addEventListener("click", ask);
symbolEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") ask();
});
document.getElementById("openLedger").addEventListener("click", async () => {
  const base = await getApiBase();
  chrome.tabs.create({ url: `${base}/oracle-accuracy` });
});
document.getElementById("openOptions").addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});

await ask();
