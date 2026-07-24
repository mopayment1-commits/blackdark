"""Legal page content for BLACKDARK launch."""

LEGAL_PAGES: dict[str, dict[str, str]] = {
    "terms": {
        "title": "Terms of Service",
        "title_ar": "شروط الاستخدام",
        "updated": "July 24, 2026",
        "html": """
<h2>1. Acceptance</h2>
<p>By accessing BLACKDARK ("the Platform"), you agree to these Terms. If you disagree, do not use the Platform.</p>
<h2>2. Service Description</h2>
<p>BLACKDARK provides AI-assisted crypto market intelligence, analytics, and alerts. We do not execute trades on your behalf unless you explicitly enable live execution with your own exchange API keys.</p>
<h2>3. Accounts & Subscriptions</h2>
<p>Free, Pro, and Whale tiers are described on our pricing page. Trials convert to paid subscriptions unless cancelled. Refunds follow Stripe policy and applicable law.</p>
<h2>4. Acceptable Use</h2>
<p>You may not scrape, resell, or redistribute our proprietary feeds without a B2B agreement. Automated abuse, credential sharing, or reverse engineering is prohibited.</p>
<h2>5. Intellectual Property</h2>
<p>CVVD, SII, Oracle scoring, and aggregated datasets are proprietary. B2B clients receive licensed access per contract only.</p>
<h2>6. Limitation of Liability</h2>
<p>The Platform is provided "as is." We are not liable for trading losses, missed alerts, or data delays. Maximum liability is limited to fees paid in the prior 12 months.</p>
<h2>7. Governing Law</h2>
<p>These Terms are governed by applicable international commercial law. Disputes should first be resolved via support@blackdark.io.</p>
""",
    },
    "privacy": {
        "title": "Privacy Policy",
        "title_ar": "سياسة الخصوصية",
        "updated": "July 24, 2026",
        "html": """
<h2>1. Data We Collect</h2>
<p>Email, name (optional), password hash, subscription status, usage metrics (Oracle queries, dashboard views), journal entries, and alert preferences (Telegram chat ID if provided).</p>
<h2>2. How We Use Data</h2>
<p>To authenticate you, deliver features, improve models, send alerts you opt into, and process payments via Stripe. We do not sell personal data.</p>
<h2>3. Payment Data</h2>
<p>Card details are handled entirely by Stripe. We store subscription tier and Stripe customer/subscription IDs only.</p>
<h2>4. Cookies & Local Storage</h2>
<p>Session tokens are stored in your browser localStorage for dashboard auth. Analytics counters are aggregated server-side.</p>
<h2>5. Data Retention</h2>
<p>Account data is kept while active. Market telemetry may be retained in anonymized form for model training and B2B feeds.</p>
<h2>6. Your Rights</h2>
<p>Request access, correction, or deletion via support@blackdark.io. EU/UK users may exercise GDPR rights subject to verification.</p>
<h2>7. Security</h2>
<p>Passwords use PBKDF2-SHA256. B2B feeds are HMAC-signed. Use strong passwords and enable 2FA on linked services (Telegram, Stripe).</p>
""",
    },
    "disclaimer": {
        "title": "Risk Disclaimer",
        "title_ar": "إخلاء المسؤولية",
        "updated": "July 24, 2026",
        "html": """
<h2>Not Financial Advice</h2>
<p>BLACKDARK outputs — Oracle verdicts, arbitrage signals, whale alerts, research metrics, and AI chat — are <strong>informational only</strong>. They are not investment, tax, or legal advice.</p>
<h2>Trading Risks</h2>
<p>Cryptocurrency markets are highly volatile. Past performance of signals or simulations does not guarantee future results. You may lose some or all of your capital.</p>
<h2>Data Accuracy</h2>
<p>We aggregate live exchange APIs, on-chain proxies, and NLP sentiment. Delays, outages, or exchange discrepancies can occur. Always verify prices before trading.</p>
<h2>Simulations & Paper Trading</h2>
<p>Trade simulator and dry-run execution ignore slippage, partial fills, and market impact unless explicitly modeled. Results are illustrative.</p>
<h2>Do Your Own Research (DYOR)</h2>
<p>Consult a licensed financial advisor before making investment decisions. You alone are responsible for your trades and compliance with local regulations.</p>
<h2>B2B Clients</h2>
<p>Institutional feeds are licensed data products. Redistribution without authorization violates our Terms and may breach exchange ToS.</p>
""",
    },
}
