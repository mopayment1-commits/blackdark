"""Legal page content for BLACKDARK launch."""

# Sonar S1192: duplicated string literals
STR_JULY_24_2026 = 'July 24, 2026'

LEGAL_PAGES: dict[str, dict[str, str]] = {
    "terms": {
        "title": "Terms of Service",
        "title_ar": "شروط الاستخدام",
        "updated": STR_JULY_24_2026,
        "html": """
<h2>0. Four-layer legal shield (binding)</h2>
<p>BLACKDARK publishes a four-layer protective shield on every decision surface:</p>
<ol>
<li><strong>Product classification</strong> — Decision-support / Trust OS evidence tooling. Not a bank, broker, exchange, custodian, or investment adviser.</li>
<li><strong>Not financial advice</strong> — Outputs are probabilistic and evidence-bound. They are not recommendations to buy, sell, hold, or transfer any asset.</li>
<li><strong>No liability for market outcomes</strong> — You alone decide and you alone bear market, operational, and regulatory risk. BLACKDARK is not liable for trading losses or opportunity cost.</li>
<li><strong>Terms acknowledgement gate</strong> — Registration requires Terms/Privacy/Risk acceptance; continued use of oracle/system surfaces may require <code>bd_terms_ack</code>.</li>
</ol>
<h2>1. Acceptance</h2>
<p>By accessing BLACKDARK ("the Platform"), you agree to these Terms. If you disagree, do not use the Platform.</p>
<h2>2. Service Description</h2>
<p>BLACKDARK provides AI-assisted crypto market intelligence, analytics, and alerts. We do not execute trades on your behalf unless you explicitly enable live execution with your own exchange API keys.</p>
<h2>3. Accounts & Subscriptions</h2>
<p>Proof Pass (Free), Decision Pro, Decision Desk, and Institutional are described on our pricing page. Prices for self-serve plans are in <strong>USD</strong>. Decision Pro trials convert to paid USD subscriptions unless cancelled before trial end. Refunds follow our <a href="/refund">Refund Policy</a> and applicable law. Card data is processed by Lemon Squeezy or Stripe — never stored on BLACKDARK servers.</p>
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
        "updated": STR_JULY_24_2026,
        "html": """
<h2>1. Data We Collect</h2>
<p>Email, display name, optional public username, optional avatar image, password hash, email verification status, subscription status, usage metrics (Oracle queries, dashboard views), journal entries, UI preferences (language / UX mode / timezone), OAuth provider ids when linked, MFA secrets (encrypted), and alert preferences (Telegram chat ID if provided).</p>
<h2>2. How We Use Data</h2>
<p>To authenticate you, deliver features, improve models, send alerts you opt into, and process payments via Stripe. We do not sell personal data.</p>
<h2>3. Payment Data</h2>
<p>Card numbers, CVV, and full bank account details for retail checkout are handled entirely by Lemon Squeezy and/or Stripe (PCI DSS Level 1 processors). BLACKDARK stores only subscription tier, status, and provider customer/subscription IDs. We do not store PAN, CVV, or full retail IBAN. Currency for self-serve billing is USD.</p>
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
        "updated": STR_JULY_24_2026,
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
    "refund": {
        "title": "Refund Policy",
        "title_ar": "سياسة الاسترداد",
        "updated": "August 8, 2026",
        "html": """
<h2>Currency</h2>
<p>Self-serve subscriptions (Decision Pro, Decision Desk) are priced and charged in <strong>USD</strong>.</p>
<h2>Trials</h2>
<p>Decision Pro may include a 7-day trial. Cancel before the trial ends to avoid the first USD charge. Manage billing via the customer portal provided by Stripe or Lemon Squeezy.</p>
<h2>Paid periods</h2>
<p>Monthly USD fees are generally non-refundable once a paid billing period has started, except where required by law or in the case of a clear billing error (duplicate charge, wrong plan).</p>
<h2>How to request</h2>
<p>Email support with your account email and checkout/order reference. Do <strong>not</strong> send card numbers. Refunds are executed by the payment processor.</p>
<h2>Institutional</h2>
<p>Custom contracts (from $3,000/mo USD) use invoice and wire terms in the signed agreement — not this self-serve policy.</p>
<h2>Not investment returns</h2>
<p>Subscription fees pay for software access and decision intelligence tools. We do not guarantee trading profits. See the Risk Disclaimer.</p>
""",
    },
    "cookies": {
        "title": "Cookies & Local Storage",
        "title_ar": "ملفات تعريف الارتباط",
        "updated": "August 8, 2026",
        "html": """
<h2>1. What we use</h2>
<p>BLACKDARK uses browser <strong>localStorage</strong> for session tokens (dashboard auth), UI preferences (language / UX mode), and optional in-browser portfolio drafts. We do not run invasive third-party ad trackers on core Trust OS surfaces.</p>
<h2>2. Essential vs optional</h2>
<p><strong>Essential:</strong> auth token storage so you stay signed in; CSRF/OAuth state during login flows; security-related cookies if your browser session uses HTTP-only session cookies in future deployments.</p>
<p><strong>Optional / product:</strong> local draft holdings for Portfolio AI (stay on-device until you analyze); theme or lens preference if saved client-side.</p>
<h2>3. Analytics</h2>
<p>Aggregated counters (e.g. Oracle usage) may be recorded server-side for product integrity and rate limits. They are not sold as advertising profiles.</p>
<h2>4. Payments</h2>
<p>Checkout is hosted by Lemon Squeezy or Stripe. Those processors may set their own cookies on their domains during payment — see their policies. BLACKDARK never stores card PAN/CVV.</p>
<h2>5. Your controls</h2>
<p>Clear site data in your browser to remove localStorage tokens (you will need to log in again). For account deletion requests, email support. Full privacy details: <a href="/privacy">Privacy Policy</a>.</p>
<h2>6. Contact</h2>
<p>Questions about cookies or storage: <a href="/contact">Contact</a> · Legal hub: <a href="/legal">/legal</a>.</p>
""",
    },
    "sla": {
        "title": "Service Level Agreement",
        "title_ar": "اتفاقية مستوى الخدمة",
        "updated": "1 January 2025",
        "html": """
<p><strong>Legal status:</strong> APPROVED FOR PUBLICATION · <strong>Effective:</strong> 1 January 2025</p>
<p>This SLA is issued by <strong>شركة أم أو لتصميم البرامج (MO Software Design LLC)</strong> for the BLACKDARK platform.</p>
<h2>1. Scope</h2>
<p>Applies to paid Pro, Elite, Quant, and institutional tiers that reference this SLA. Free/demo access is best-effort unless agreed in writing.</p>
<h2>2. Availability targets</h2>
<ul>
<li><strong>Pro:</strong> 99.5% monthly uptime</li>
<li><strong>Elite / Quant:</strong> 99.7% monthly uptime</li>
<li><strong>Institutional:</strong> 99.9% monthly uptime (contractual; signed HA evidence required)</li>
</ul>
<h2>3. Support response</h2>
<p>P1 platform-down: 4h (Pro), 2h (Elite/Quant), 1h (Institutional). Support: <a href="mailto:mopayment1@gmail.com">mopayment1@gmail.com</a>, 10:00 AM – 10:00 PM Cairo Time daily. Urgent: subject prefix <code>URGENT</code>.</p>
<h2>4. Governing law</h2>
<p>This SLA is governed by the <strong>Laws of the Arab Republic of Egypt</strong>.</p>
<h2>5. Dispute resolution</h2>
<p>Good-faith negotiation via published support channels within 30 days; then exclusive jurisdiction of the competent courts in <strong>Cairo, Egypt</strong>.</p>
<p>Published at <a href="/sla">/sla</a> · Legal hub: <a href="/legal">/legal</a></p>
""",
    },
    "msa": {
        "title": "Master Service Agreement",
        "title_ar": "اتفاقية الخدمات الرئيسية",
        "updated": "22 August 2026",
        "html": """
<p><strong>Version:</strong> 1.0-FINAL · <strong>Status:</strong> APPROVED FOR PUBLICATION / COMMERCIAL USE</p>
<p><strong>Provider:</strong> AMO Software Design LLC (BLACKDARK trade name)</p>
<p><strong>Effective Date:</strong> Upon mutual signature</p>
<h2>Governing law</h2>
<p>Laws of the <strong>Arab Republic of Egypt</strong>.</p>
<h2>Dispute resolution</h2>
<p>Binding arbitration under the <strong>Cairo Regional Centre for International Commercial Arbitration (CRCICA)</strong>, seat Cairo, English language.</p>
<h2>Schedules</h2>
<ul>
<li><strong>Schedule A</strong> — Data Processing Agreement (DPA)</li>
<li><strong>Schedule B</strong> — Service Level Agreement (SLA)</li>
<li><strong>Schedule C</strong> — Acceptable Use Policy (AUP)</li>
</ul>
<p>Full approved text: published at <a href="/msa">/msa</a> · repository path <code>docs/legal/MSA.md</code></p>
""",
    },
}


# Convenience alias for binding tests / external importers
TERMS_OF_SERVICE = LEGAL_PAGES["terms"]["html"]
