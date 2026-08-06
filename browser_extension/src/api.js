/** Shared defaults for BLACKDARK Oracle extension. */
export const DEFAULT_API_BASE = "https://blackdark-production.up.railway.app";

export async function getApiBase() {
  const stored = await chrome.storage.sync.get(["apiBase"]);
  const base = (stored.apiBase || DEFAULT_API_BASE).replace(/\/$/, "");
  return base;
}

export function normalizeSymbol(raw) {
  if (!raw) return "BTC";
  let s = String(raw).toUpperCase().trim();
  s = s.replace(/[^A-Z0-9]/g, "");
  s = s.replace(/USDT$|USD$|BUSD$|PERP$/g, "");
  return s || "BTC";
}

function mapOraclePayload(data, asset, base) {
  const action = String(
    data.decision_action || data.verdict || data.action || "WAIT"
  ).toUpperCase();
  // Prefer short public decision; fall back to action_line / action text
  const sentence =
    data.decision_sentence ||
    data.oracle ||
    data.action_line ||
    (typeof data.action === "string" && data.action.length > 20 ? data.action : null) ||
    data.explanation?.summary ||
    "No decision sentence available.";
  return {
    asset,
    action: action.includes("WAIT") || action.includes("NEUTRAL") || action.includes("HOLD")
      ? "WAIT"
      : action.includes("BUY") || action.includes("BULL") || action.includes("ACT")
        ? "ACT"
        : action.slice(0, 12),
    sentence,
    score: data.opportunity_score,
    predictionId: data.prediction_id,
    chainHash: data.chain_hash,
    compliance: data.compliance_footer || null,
    apiBase: base,
    raw: data,
  };
}

export async function fetchOracle(symbol) {
  const base = await getApiBase();
  const asset = normalizeSymbol(symbol);
  const headers = { Accept: "application/json" };
  const urls = [
    `${base}/oracle/${encodeURIComponent(asset)}?ux_mode=beginner&lang=en`,
    `${base}/oracle/${encodeURIComponent(asset)}/quick?ux_mode=beginner&lang=en`,
  ];
  let lastErr = null;
  for (const url of urls) {
    try {
      const res = await fetch(url, { headers });
      if (!res.ok) {
        lastErr = new Error(`Oracle HTTP ${res.status}`);
        continue;
      }
      const text = await res.text();
      if (!text || text.trim().startsWith("<") || text.includes("Internal Server Error")) {
        lastErr = new Error("Oracle HTML/error response");
        continue;
      }
      const data = JSON.parse(text);
      return mapOraclePayload(data, asset, base);
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr || new Error("Oracle unavailable");
}
