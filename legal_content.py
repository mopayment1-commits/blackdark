"""Legal page content for BLACKDARK — SEC/MiCA engineering posture (not a legal opinion)."""

LEGAL_PAGES: dict[str, dict[str, str]] = {
    "terms": {
        "title": "Terms of Service",
        "title_ar": "شروط الاستخدام",
        "updated": "March 28, 2026",
        "html": """
<h2>1. Acceptance</h2>
<p>By accessing BLACKDARK ("the Platform"), you agree to these Terms, the Risk Disclaimer, and the Privacy Policy. If you disagree, do not use the Platform. <strong>Oracle and AI features require an explicit Accept Terms action</strong> before use.</p>

<h2>2. Not Financial Advice</h2>
<ul>
    <li><strong>Not Financial Advice:</strong> BLACKDARK does not provide financial, investment, tax, legal, or trading advice.</li>
    <li><strong>Educational &amp; Analytical Only:</strong> All content is for educational and analytical purposes only.</li>
    <li><strong>No Guarantees:</strong> We do not guarantee accuracy, profitability, uptime, or any specific outcome.</li>
    <li><strong>Your Responsibility:</strong> You are solely responsible for your own trades and decisions.</li>
    <li><strong>Risk:</strong> Cryptocurrency trading involves significant risk. You may lose all your capital.</li>
</ul>

<h2>3. Service Description</h2>
<p>BLACKDARK is a <strong>decision intelligence / probabilistic analytics</strong> platform. It is not a registered investment adviser, broker-dealer, exchange, custodian, or MiCA crypto-asset service provider unless separately authorized in writing for a specific entity packaging.</p>
<p>We do not execute trades on your behalf unless you explicitly enable live execution with <em>your own</em> exchange API keys under separate risk gates.</p>

<h2>4. Accounts &amp; Subscriptions</h2>
<p>Free, Pro, and Whale tiers are described on our pricing page. Trials convert to paid subscriptions unless cancelled. Refunds follow the payment provider policy and applicable law.</p>

<h2>5. Acceptable Use</h2>
<p>You may not scrape, resell, or redistribute proprietary feeds without a B2B agreement. Automated abuse, credential sharing, reverse engineering, or using outputs as purported personalized investment advice to third parties is prohibited.</p>

<h2>6. Intellectual Property</h2>
<p>Oracle scoring, audit trails, and aggregated datasets are proprietary. B2B clients receive licensed access per contract only.</p>

<h2>7. Limitation of Liability</h2>
<p>The Platform is provided "as is." We are not liable for trading losses, missed alerts, or data delays. To the maximum extent permitted by law, aggregate liability is limited to fees paid in the prior 12 months.</p>

<h2>8. Regulatory Posture</h2>
<p>Product engineering controls (disclaimers, public accuracy ledger, terms gate, GDPR DSR) support an analytics posture. Formal SEC or MiCA authorization depends on entity packaging and external counsel — see <code>docs/SEC_MICA_COMPLIANCE_PACK.md</code>.</p>

<h2>9. Governing Law</h2>
<p>These Terms are governed by applicable international commercial law. Disputes should first be resolved via support@blackdark.io.</p>
""",
    },
    "privacy": {
        "title": "Privacy Policy",
        "title_ar": "سياسة الخصوصية",
        "updated": "March 28, 2026",
        "html": """
<h2>1. Minimal Data We Collect</h2>
<ul>
    <li><strong>Email:</strong> For account creation, authentication, and notifications.</li>
    <li><strong>Usage Data:</strong> To improve the system (aggregated / anonymized where feasible).</li>
    <li><strong>OAuth identifiers:</strong> If you use Google/GitHub login (email, name, provider subject id).</li>
    <li><strong>Security logs:</strong> Failed login / terms acceptance audit events.</li>
    <li><strong>We do NOT sell your data to third parties.</strong></li>
</ul>

<h2>2. How We Use Data</h2>
<p>To authenticate you, deliver features, improve models, send alerts you opt into, and process payments via Stripe or Lemon Squeezy.</p>

<h2>3. Payment Data</h2>
<p>Card details are handled entirely by the payment provider. We store subscription tier and provider customer/subscription IDs only.</p>

<h2>4. Cookies &amp; Local Storage</h2>
<p>Session tokens may be stored in an HttpOnly <code>bd_token</code> cookie and/or browser localStorage. Terms acceptance is stored in cookie <code>bd_terms_v</code> and (for accounts) in your user record.</p>

<h2>5. Your Rights (GDPR / CCPA)</h2>
<ul>
    <li>Request access / portable export via <code>/api/privacy/dsr/export</code> or <a href="/request-deletion">/request-deletion</a>.</li>
    <li>Request erasure via <code>/api/privacy/dsr/erase</code> or the deletion request form.</li>
    <li>You can request data deletion at any time via support@blackdark.io.</li>
    <li>California residents may request know/delete/opt-out of sale (we do not sell personal data).</li>
</ul>

<h2>6. Data Retention</h2>
<p>Account data is kept while active. Market telemetry may be retained in anonymized form for model training and B2B feeds. Auth/privacy request logs are retained for security and compliance investigations.</p>

<h2>7. Security</h2>
<p>Passwords use PBKDF2-SHA256. Admin privileged actions require TOTP MFA in production. Secrets use application-level encryption; PostgreSQL deployments enable <code>pgcrypto</code>.</p>

<h2>8. International Transfers</h2>
<p>If you access the Platform from the EEA/UK, processing may occur on cloud infrastructure outside your country with contractual and technical safeguards appropriate to an analytics SaaS.</p>
""",
    },
    "disclaimer": {
        "title": "Risk Disclaimer",
        "title_ar": "إخلاء المسؤولية",
        "updated": "March 28, 2026",
        "html": """
<h2>DISCLAIMER — Read Carefully</h2>
<p><strong>This is not financial advice.</strong> BLACKDARK is a probabilistic analysis tool. All predictions and Oracle outputs are based on historical data and market patterns. Past performance does NOT guarantee future results. You are 100% responsible for your own investment decisions. Always do your own research (DYOR) before making any trade.</p>

<h2>Classification of Outputs</h2>
<p>Every Oracle / AI surface is labeled: <strong>[Probabilistic Analysis – Not Financial Advice]</strong>.</p>

<h2>No SEC / MiCA License Claim in Product UI</h2>
<p>Engineering controls support a decision-intelligence posture. Formal SEC or MiCA authorization depends on entity packaging and external counsel — see <code>docs/SEC_MICA_COMPLIANCE_PACK.md</code>.</p>

<h2>Trading Risks</h2>
<p>Cryptocurrency markets are highly volatile. You may lose some or all of your capital.</p>

<h2>Data Accuracy</h2>
<p>Delays, outages, or exchange discrepancies can occur. Public accuracy is published at <code>/oracle-accuracy</code>.</p>

<h2>Do Your Own Research (DYOR)</h2>
<p>Consult a licensed financial advisor before making investment decisions. You alone are responsible for your trades and compliance with local regulations.</p>
""",
    },
}
