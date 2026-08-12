import { getApiBase } from "./api.js";

const out = document.getElementById("out");
const symbolEl = document.getElementById("symbol");

function setText(el, value) {
  if (!el) return;
  el.textContent = value == null ? "" : String(value);
}

function renderOracle(payload) {
  out.replaceChildren();
  const action = String(payload.action || "WAIT").toUpperCase();
  const verdict = document.createElement("div");
  verdict.className = `verdict ${/^[A-Z_]{2,16}$/.test(action) ? action : "WAIT"}`;
  setText(verdict, action);
  const sentence = document.createElement("div");
  sentence.className = "sentence";
  setText(sentence, payload.sentence || "");
  const meta = document.createElement("div");
  meta.className = "meta";
  const score = payload.score ?? "—";
  const asset = payload.asset ?? "";
  const pid = payload.predictionId != null ? ` · id ${payload.predictionId}` : "";
  setText(meta, `Score ${score} · ${asset}${pid}`);
  out.append(verdict, sentence, meta);
}

function renderError(message) {
  out.replaceChildren();
  const err = document.createElement("div");
  err.className = "err";
  setText(err, message);
  out.append(err);
}

async function ask() {
  const symbol = symbolEl.value || "BTC";
  out.replaceChildren();
  const loading = document.createElement("span");
  loading.className = "sub";
  setText(loading, "Asking Oracle…");
  out.append(loading);
  try {
    const res = await chrome.runtime.sendMessage({ type: "ORACLE_LOOKUP", symbol });
    if (!res?.ok) throw new Error(res?.error || "lookup failed");
    renderOracle(res.payload);
  } catch (err) {
    renderError(String(err.message || err));
  }
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
