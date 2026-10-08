import { chromium } from "playwright";

const pageUrl = process.argv[2];

const browser = await chromium.launch({ headless: true, args: ["--no-sandbox"] });
const page = await browser.newPage();
let lcpMs = null;
let error = null;

try {
  await page.goto(pageUrl, { waitUntil: "load", timeout: 60000 });
  lcpMs = await page.evaluate(async () => {
    return await new Promise((resolve) => {
      let value = null;
      const done = () => resolve(value);
      try {
        const po = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          if (entries.length) {
            const last = entries[entries.length - 1];
            value = last.renderTime || last.loadTime || last.startTime;
          }
        });
        po.observe({ type: "largest-contentful-paint", buffered: true });
      } catch (e) {
        resolve(null);
        return;
      }
      setTimeout(done, 4000);
    });
  });
} catch (e) {
  error = String(e);
} finally {
  await browser.close();
}

console.log(JSON.stringify({ lcp_ms: lcpMs, error }));
