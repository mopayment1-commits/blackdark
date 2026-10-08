import { chromium } from "playwright";

const pageUrl = process.argv[2];
const inpMaxMs = Number(process.argv[3] || 200);

const results = { buttons: [], error: null };

async function scrollPage(page) {
  const scrollHeight = await page.evaluate(() => document.body.scrollHeight);
  const steps = Math.min(6, Math.max(1, Math.ceil(scrollHeight / 1000)));
  for (let s = 0; s < steps; s += 1) {
    await page.evaluate((y) => window.scrollTo(0, y), Math.floor((scrollHeight * s) / steps));
    await page.waitForTimeout(80);
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(100);
}

async function collectTargets(page) {
  return page.evaluate(() => {
    const sel =
      "button, [role='button'], input[type='submit'], input[type='button'], a[href^='#'][class*='btn']";
    const seen = new Set();
    const out = [];
    for (const el of document.querySelectorAll(sel)) {
      const style = window.getComputedStyle(el);
      const rect = el.getBoundingClientRect();
      const visible =
        style.visibility !== "hidden" &&
        style.display !== "none" &&
        rect.width > 0 &&
        rect.height > 0 &&
        !el.disabled &&
        !el.hasAttribute("hidden");
      if (!visible) continue;
      const label = (
        el.innerText ||
        el.value ||
        el.getAttribute("aria-label") ||
        el.id ||
        "control"
      )
        .trim()
        .replace(/\s+/g, " ")
        .slice(0, 80);
      if (!label || seen.has(label)) continue;
      seen.add(label);
      out.push({ label, tag: el.tagName.toLowerCase() });
    }
    return out;
  });
}

async function measureClick(page, label, tag) {
  return page.evaluate(
    async ({ label, tag }) => {
      const sel =
        "button, [role='button'], input[type='submit'], input[type='button'], a[href^='#'][class*='btn']";
      const norm = (s) => (s || "").trim().replace(/\s+/g, " ");
      let target = null;
      for (const el of document.querySelectorAll(sel)) {
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        const visible =
          style.visibility !== "hidden" &&
          style.display !== "none" &&
          rect.width > 0 &&
          rect.height > 0 &&
          !el.disabled;
        if (!visible) continue;
        const text = norm(el.innerText || el.value || el.getAttribute("aria-label") || "");
        if (text !== norm(label)) continue;
        if (tag && el.tagName.toLowerCase() !== tag) continue;
        target = el;
        break;
      }
      if (!target) return { inp_ms: null, error: "control not found" };
      const start = performance.now();
      target.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, view: window }));
      await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      return { inp_ms: Math.round(performance.now() - start), error: null };
    },
    { label, tag },
  );
}

try {
  const browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
  const page = await browser.newPage();
  await page.goto(pageUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
  await scrollPage(page);
  const targets = await collectTargets(page);

  for (const target of targets) {
    await page.goto(pageUrl, { waitUntil: "domcontentloaded", timeout: 60000 });
    await scrollPage(page);
    const measured = await measureClick(page, target.label, target.tag);
    results.buttons.push({
      label: target.label,
      inp_ms: measured.inp_ms,
      over: measured.inp_ms != null && measured.inp_ms > inpMaxMs,
      error: measured.error,
    });
  }
  await browser.close();
} catch (e) {
  results.error = String(e);
}

console.log(JSON.stringify(results));
