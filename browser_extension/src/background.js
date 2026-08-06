import { fetchOracle, normalizeSymbol } from "./api.js";

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "ORACLE_LOOKUP") {
    fetchOracle(msg.symbol || "BTC")
      .then((payload) => sendResponse({ ok: true, payload }))
      .catch((err) => sendResponse({ ok: false, error: String(err.message || err) }));
    return true;
  }
  if (msg?.type === "NORMALIZE_SYMBOL") {
    sendResponse({ ok: true, symbol: normalizeSymbol(msg.symbol) });
    return false;
  }
  return false;
});
