"""Full product capability inventory — machine-readable source of truth.

Statuses: works | partial | gated | external_block | ops_config
Never claims COMPLETE / live_fill / Jupiter VC / L2-100 / cloud multi-AZ without evidence.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _f(
    *,
    id: str,
    name: str,
    name_ar: str,
    domain: str,
    status: str,
    personas: list[str],
    surfaces: list[str],
    evidence: str,
    efficiency: str,
    unpaid_block: str | None = None,
) -> dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "name_ar": name_ar,
        "domain": domain,
        "status": status,
        "personas": personas,
        "surfaces": surfaces,
        "evidence": evidence,
        "efficiency": efficiency,
        "unpaid_block": unpaid_block,
    }


ALL = ["retail", "pro", "whale", "fund", "b2b", "acquirer"]
PAID = ["pro", "whale", "fund", "b2b", "acquirer"]
DESK = ["whale", "fund", "b2b", "acquirer"]
INST = ["fund", "b2b", "acquirer"]


def capability_catalog() -> list[dict[str, Any]]:
    return [
        # ── Identity ──────────────────────────────────────────
        _f(id="ID-REG", name="Register / login / logout / session", name_ar="تسجيل / دخول / خروج / جلسة", domain="identity", status="works", personas=ALL, surfaces=["/api/auth/register", "/api/auth/login", "/login", "/profile"], evidence="api/routers/auth.py", efficiency="Session cookies + PBKDF2; local path verified"),
        _f(id="ID-MFA", name="TOTP MFA enroll/confirm/disable", name_ar="مصادقة TOTP تسجيل/تأكيد/إيقاف", domain="identity", status="works", personas=ALL, surfaces=["/api/auth/mfa/*", "/profile", "/settings/security"], evidence="auth_service.py; dashboard 307 alias", efficiency="Enrollment on /profile; /settings/security no longer 404"),
        _f(id="ID-OAUTH", name="OAuth start/callback", name_ar="بدء/رجوع OAuth", domain="identity", status="ops_config", personas=ALL, surfaces=["/api/auth/oauth/status", "/api/auth/oauth/{provider}/start"], evidence="oauth_service.py", efficiency="Protocol complete; unconfigured start is HTTP 503; live IdP needs client ids", unpaid_block="oauth_client_ids"),
        _f(id="ID-EMAIL", name="Email verify / password reset", name_ar="تحقق البريد / إعادة كلمة المرور", domain="identity", status="works", personas=ALL, surfaces=["/verify-email", "/reset-password"], evidence="identity_service.py email_outbox.py", efficiency="Hashed tokens + sealed outbox; SMTP flush is optional ops"),
        _f(id="ID-TIER", name="Tier gates free/pro/whale", name_ar="بوابات الطبقة مجاني/محترف/حوت", domain="identity", status="works", personas=ALL, surfaces=["auth_service.TIER_FEATURES", "/api/auth/me"], evidence="feature_allowed()", efficiency="Enforced on APIs; gated ≠ broken"),
        _f(id="ID-PROMO", name="Promo code redeem", name_ar="استرداد رمز ترويجي", domain="identity", status="works", personas=ALL, surfaces=["/api/promo/redeem"], evidence="auth_service.redeem_promo_code", efficiency="Extends Pro trial when code in LAUNCH_PROMO_CODES"),
        # ── Billing ───────────────────────────────────────────
        _f(id="BIL-STATUS", name="Billing status + pricing catalog", name_ar="حالة الفوترة + كتالوج الأسعار", domain="billing", status="works", personas=ALL, surfaces=["/api/billing/status", "/api/pricing"], evidence="billing_service.py pricing_catalog.py", efficiency="Catalog honest; does not claim live PSP"),
        _f(id="BIL-CHECKOUT", name="Self-serve checkout Stripe/Lemon", name_ar="دفع ذاتي Stripe/Lemon", domain="billing", status="ops_config", personas=["pro", "whale"], surfaces=["/api/billing/checkout", "/api/billing/unpaid-upgrade", "/webhook"], evidence="billing_service.unpaid_upgrade_path", efficiency="Unpaid promo/inquiry complete; live charge needs owner PSP secrets", unpaid_block="psp_credentials"),
        _f(id="BIL-INST", name="Institutional inquiry / invoices / KYC", name_ar="استعلام مؤسسي / فواتير / KYC", domain="billing", status="works", personas=INST, surfaces=["/api/billing/institutional-inquiry", "/api/institutional/commerce/*"], evidence="api/routers/institutional.py", efficiency="Sales-led path; not a self-serve SKU"),
        # ── Oracle / decision ─────────────────────────────────
        _f(id="OR-SENTENCE", name="Single-sentence Oracle + explain + quick", name_ar="أوركل جملة واحدة + شرح + سريع", domain="oracle", status="works", personas=ALL, surfaces=["/oracle/{symbol}", "/oracle/{symbol}/explain", "/oracle/{symbol}/quick"], evidence="ai_oracle.py", efficiency="Free quota 3/day; Pro unlimited"),
        _f(id="OR-CERT", name="Decision certificate + locked predictions", name_ar="شهادة قرار + توقعات مقفلة", domain="oracle", status="works", personas=ALL, surfaces=["/api/oracle/decision-certificate", "/api/locked-predictions"], evidence="decision_certificate.py locked_predictions.py", efficiency="Hash + share URLs; free watermarked"),
        _f(id="OR-TRUTH", name="Net-edge / half-life / contradiction veto", name_ar="صافي الهامش / نصف العمر / نقض التناقض", domain="oracle", status="works", personas=PAID, surfaces=["/api/oracle/net-edge-truth", "/api/oracle/half-life", "/api/oracle/dimension-conflict"], evidence="net_edge_truth.py opportunity_tracker.py", efficiency="Truth gates run in-process"),
        _f(id="OR-LEDGER", name="Public accuracy ledger + audit chain", name_ar="سجل دقة عام + سلسلة تدقيق", domain="oracle", status="works", personas=ALL, surfaces=["/oracle-accuracy", "/api/oracle/accuracy/public", "/api/oracle/audit-chain", "/public/accuracy-ledger"], evidence="ml.public_accuracy oracle_audit_chain.py", efficiency="Public read path; misses disclosed"),
        _f(id="OR-PERSONA", name="Persona clarity + trial readiness matrix", name_ar="وضوح الشخصية + مصفوفة جاهزية التجربة", domain="oracle", status="works", personas=ALL, surfaces=["/api/oracle/persona-clarity/demo", "/api/trial/persona-readiness"], evidence="persona_clarity.py persona_capability_matrix.py", efficiency="Six personas; NOT_COMPLETE banner"),
        _f(id="OR-E2E", name="Decision e2e LIVE→RISK→DECISION", name_ar="قرار طرف-لطرف حي→مخاطرة→قرار", domain="oracle", status="works", personas=DESK, surfaces=["/api/institutional/decision-e2e"], evidence="decision_e2e.py historical_self_grade.py", efficiency="Same-tick withheld; historical chain self-grade is independent"),
        _f(id="OR-GRAPH", name="Decision graph + intelligence evaluate", name_ar="رسم القرار + تقييم الذكاء", domain="oracle", status="works", personas=DESK, surfaces=["/api/institutional/decision-graph/*", "/api/institutional/decision-intelligence/*"], evidence="api/routers/oms_decision.py", efficiency="In-process graph; not a hosted ML farm"),
        _f(id="OR-PROV", name="Provenance score", name_ar="درجة المصدر", domain="oracle", status="works", personas=ALL, surfaces=["/api/oracle/provenance-score"], evidence="heroes.py", efficiency="Honesty surface; not exclusive data vendor"),
        # ── Market data ───────────────────────────────────────
        _f(id="MKT-INGEST", name="Catalog-100 price health", name_ar="صحة أسعار الكتالوج 100", domain="market", status="works", personas=ALL, surfaces=["/api/universe/status", "full_catalog_mesh_proof"], evidence="coverage_percent 100%", efficiency="Price health ≠ institutional L2"),
        _f(id="MKT-L2", name="Institutional venue L2 books", name_ar="كتب L2 مؤسسية حسب المنصة", domain="market", status="partial", personas=DESK, surfaces=["live_data_truth_probe", "/api/product/l2-remainder"], evidence="80/100 venue_l2; remainder labeled synthetic_mid", efficiency="Native CEX L2 unpaid max; AMM+bybit not invented as CEX ladders", unpaid_block="amm_and_bybit_geo"),
        _f(id="MKT-MESH", name="CORE public CEX L2 mesh", name_ar="شبكة L2 للمنصات العامة الأساسية", domain="market", status="works", personas=DESK, surfaces=["prove_multi_venue_live", "/api/institutional/canonical/mesh-prove"], evidence="77/77 live L2", efficiency="CORE mesh complete; catalog L2 is separate"),
        _f(id="MKT-RADAR", name="Market radar / sectors / OI / klines", name_ar="رادار السوق / قطاعات / فائدة مفتوحة / شموع", domain="market", status="works", personas=["pro", "whale", "fund"], surfaces=["/api/market/overview", "/api/market/sectors", "/api/market/klines"], evidence="api/routers/market.py", efficiency="Pro+ depth; free gets light radar"),
        _f(id="MKT-SENT", name="Sentiment / onchain / macro overviews", name_ar="نظرة معنويات / سلسلة / كلي", domain="market", status="works", personas=PAID, surfaces=["/api/sentiment/overview", "/api/onchain/overview", "/api/macro/overview"], evidence="dashboard.py", efficiency="Public-proxy product complete; not exclusive vendor data"),
        _f(id="MKT-OPT", name="Options chain + paper OMS", name_ar="سلسلة خيارات + OMS ورقي", domain="market", status="works", personas=["pro", "whale"], surfaces=["/api/options/overview", "/api/options/oms/chain", "/api/options/oms/paper-fill"], evidence="options_fetcher.py options_oms.py", efficiency="Deribit public chain; paper fill at mark; not live options"),
        _f(id="MKT-TA", name="Technical analysis snapshot", name_ar="لقطة تحليل فني", domain="market", status="works", personas=PAID, surfaces=["/api/ta/{symbol}"], evidence="dashboard.py", efficiency="In-process TA; not TradingView charts SaaS"),
        _f(id="MKT-FEED", name="Feed stale-price / ingress guards", name_ar="حراسة الأسعار المتقادمة / الدخول", domain="market", status="works", personas=DESK, surfaces=["/api/feed/stale-price-guard", "/api/feed/ingress-guard", "/api/feed/engine/status"], evidence="dashboard.py", efficiency="Guards labeled; do not claim exclusive feeds"),
        # ── Arbitrage ─────────────────────────────────────────
        _f(id="ARB-SCAN", name="Cross/tri/funding/spot-fut scans", name_ar="مسح تقاطع/ثلاثي/تمويل/فوري-آجل", domain="arbitrage", status="works", personas=["pro", "whale"], surfaces=["/api/arbitrage/opportunities", "/api/arbitrage/scan"], evidence="arbitrage_engine.py", efficiency="Canonical engine; paper unless live_fill"),
        _f(id="ARB-CAT", name="Arbitrage type catalog", name_ar="كتالوج أنواع الأربتراج", domain="arbitrage", status="works", personas=["pro", "whale"], surfaces=["/api/arbitrage/catalog", "/api/arbitrage/catalog/scan"], evidence="arbitrage_catalog.py", efficiency="Honest live/proxy/planned taxonomy; CEX-DEX + options vs spot now live/proxy"),
        _f(id="ARB-CEXDEX", name="CEX↔DEX path", name_ar="مسار منصة↔DEX", domain="arbitrage", status="works", personas=["whale"], surfaces=["/api/platform/arb/cex-dex", "/api/execution/cex-dex/cycle"], evidence="bd_platform.cex_dex_executor", efficiency="Paper/dry-run complete; live CEX leg is EX-LIVE geo block"),
        # ── Execution ─────────────────────────────────────────
        _f(id="EX-SIM", name="Trade/arb simulator + history", name_ar="محاكي تداول/أربتراج + تاريخ", domain="execution", status="works", personas=["pro", "whale"], surfaces=["/api/simulate/trade", "/api/simulate/arbitrage", "/api/simulate/history"], evidence="dashboard.py", efficiency="Paper path verified"),
        _f(id="EX-OMS", name="OMS lifecycle INTENT→RECONCILE", name_ar="دورة OMS نية→مطابقة", domain="execution", status="works", personas=DESK, surfaces=["/api/institutional/oms/*"], evidence="oms.py", efficiency="Paper/dry-run complete; submit≠live_fill"),
        _f(id="EX-KEYS", name="Exchange API key vault (Fernet)", name_ar="خزنة مفاتيح المنصات (Fernet)", domain="execution", status="works", personas=["whale"], surfaces=["/api/user/exchange-keys", "/api/execution/keys/*", "/api/platform/vault/*"], evidence="secrets_vault.py", efficiency="Encrypt/store works; live submit still geo-blocked"),
        _f(id="EX-LIVE", name="Live venue FILL", name_ar="تعبئة حية على المنصة", domain="execution", status="external_block", personas=["whale"], surfaces=["/api/execution/order", "venue_fill_proof"], evidence="binance_order_host_geo_451", efficiency="Path armed; hosts return HTTP 451", unpaid_block="binance_order_host_geo_451"),
        _f(id="EX-JUP", name="Jupiter quote/build/local sign", name_ar="Jupiter تسعير/بناء/توقيع محلي", domain="execution", status="works", personas=["whale"], surfaces=["/api/institutional/jupiter/*"], evidence="signed_local=true", efficiency="Unpaid path complete; on-chain VC remains four-blocker unfunded"),
        _f(id="EX-PANIC", name="Panic freeze / resume", name_ar="تجميد طوارئ / استئناف", domain="execution", status="works", personas=["whale"], surfaces=["/api/execution/panic", "/api/execution/resume", "/api/risk/freeze"], evidence="execution_engine + risk_manager", efficiency="In-process freeze flag"),
        _f(id="EX-AUTO", name="Auto execution cycle (dry-run default)", name_ar="دورة تنفيذ تلقائي (افتراضي تجريبي)", domain="execution", status="works", personas=["whale"], surfaces=["/api/execution/auto", "/api/execution/cycle", "/api/execution/status"], evidence="AUTO_EXECUTION_DRY_RUN=true", efficiency="Dry-run by policy; not live money"),
        # ── Risk ──────────────────────────────────────────────
        _f(id="RSK-ARCH", name="Full risk architecture + liquidity", name_ar="عمارة المخاطر الكاملة + السيولة", domain="risk", status="works", personas=DESK, surfaces=["/api/institutional/risk/*", "/api/risk/status", "/api/platform/risk/drawdown"], evidence="risk_intelligence.py", efficiency="decision_e2e uses live books"),
        _f(id="RSK-WHALE", name="Whale 5m band / exitability", name_ar="نطاق الحوت 5 د / قابلية الخروج", domain="risk", status="works", personas=["whale", "fund"], surfaces=["whale_execution_evidence.py"], evidence="whale_execution_evidence.py", efficiency="May whale_ready=false when books thin — honest"),
        # ── Alerts ────────────────────────────────────────────
        _f(id="AL-INBOX", name="In-app alert inbox", name_ar="صندوق تنبيهات داخل التطبيق", domain="alerts", status="works", personas=ALL, surfaces=["/api/alerts/inbox"], evidence="dashboard.py", efficiency="Read path ungated; subscribe Pro+"),
        _f(id="AL-SUB", name="Alert subscribe Telegram/email", name_ar="اشتراك تنبيهات تيليغرام/بريد", domain="alerts", status="works", personas=["pro", "whale"], surfaces=["/api/alerts/subscribe", "/api/alerts/inbox", "/api/alerts/telegram/*"], evidence="in_app_alerts.py email_outbox.py", efficiency="In-app + sealed outbox always work; live Telegram token is optional ops"),
        _f(id="AL-PASS", name="Proof-gated alert passport", name_ar="جواز تنبيه مشروط بالدليل", domain="alerts", status="works", personas=["pro", "whale"], surfaces=["/alert-passport", "/api/alert-passport"], evidence="proof_gated_alert_passport.py", efficiency="Evaluate path in-process"),
        _f(id="AL-GEN", name="Alert generosity policy", name_ar="سياسة سخاء التنبيهات", domain="alerts", status="works", personas=["pro", "whale"], surfaces=["/api/alerts/generosity"], evidence="heroes.py", efficiency="Policy surface; not a vendor SLA"),
        # ── Journal / reports / research ──────────────────────
        _f(id="JR-CRUD", name="Personal trading journal", name_ar="دفتر تداول شخصي", domain="journal", status="works", personas=ALL, surfaces=["/api/journal"], evidence="database.journal_entries", efficiency="CRUD on free tier"),
        _f(id="RP-WEEK", name="Weekly/daily research reports", name_ar="تقارير بحث أسبوعية/يومية", domain="reports", status="works", personas=["pro", "whale"], surfaces=["/api/reports/weekly", "/api/reports/daily"], evidence="research_lab gate", efficiency="Tier-gated; local generation"),
        _f(id="RP-SUB", name="Subscriber value digest", name_ar="ملخص قيمة المشترك", domain="reports", status="works", personas=["whale"], surfaces=["/api/subscriber/value"], evidence="dashboard.py", efficiency="Whale-gated"),
        _f(id="RS-LAB", name="Research lab / moat / asset export", name_ar="مختبر بحث / خندق / تصدير أصل", domain="reports", status="works", personas=["pro", "whale"], surfaces=["/api/research/lab", "/api/research/moat", "/api/research/asset/{symbol}", "/api/research/export"], evidence="dashboard.py", efficiency="Pro+; not a Bloomberg terminal"),
        _f(id="RS-CHAT", name="AI chat (tier-gated)", name_ar="دردشة ذكاء اصطناعي (حسب الطبقة)", domain="reports", status="works", personas=["pro", "whale"], surfaces=["/api/chat"], evidence="dashboard.py + TIER_FEATURES.ai_chat", efficiency="Gated on free; works for Pro+"),
        _f(id="RS-PORT", name="Portfolio AI analyze / rebalance", name_ar="تحليل محفظة بالذكاء / إعادة توازن", domain="reports", status="works", personas=["pro", "whale"], surfaces=["/portfolio/analyze", "/api/institutional/portfolio/*", "/api/platform/portfolio/rebalance"], evidence="TIER_FEATURES.portfolio_ai", efficiency="Gated on free; in-process analyze"),
        # ── Whale / unique / Trust OS ─────────────────────────
        _f(id="WH-RADAR", name="Whale radar / gravity / stealth advisor", name_ar="رادار الحيتان / جاذبية / مستشار تخفي", domain="whale", status="works", personas=["whale"], surfaces=["/api/whale/scan", "/api/whale/stealth-advisor", "/api/whale/gravity-map", "/api/whale/signal-vs-noise"], evidence="whale_tracker.py", efficiency="Desk surfaces; not exclusive on-chain vendor"),
        _f(id="WH-VOICE", name="Voice command", name_ar="أمر صوتي", domain="whale", status="works", personas=["whale"], surfaces=["/api/voice/command"], evidence="Tier-gated whale", efficiency="API present; client mic is UX"),
        _f(id="WH-MEV", name="MEV sandwich report", name_ar="تقرير ساندويتش MEV", domain="whale", status="works", personas=["whale"], surfaces=["/api/mev/sandwich-report"], evidence="heroes.py", efficiency="Heuristic report; not a private mempool"),
        _f(id="UX-LENS", name="Trust OS four lenses", name_ar="أربع عدسات نظام الثقة", domain="ux", status="works", personas=ALL, surfaces=["/api/lenses", "/capabilities", "/api/trust-os"], evidence="trust_os_lenses.py", efficiency="Prove/Operate/Desk/Room"),
        _f(id="UX-AUD", name="Six-audience entry routing", name_ar="توجيه دخول ست شرائح", domain="ux", status="works", personas=ALL, surfaces=["/api/audience/entry", "/api/heroes/strategy"], evidence="audience_routing.py", efficiency="retail/pro/whale/fund/b2b/acquirer"),
        _f(id="UX-INT", name="Intent router + 60s acceptance", name_ar="موجّه النية + قبول 60 ثانية", domain="ux", status="works", personas=ALL, surfaces=["/api/intent/router", "/api/intent/resolve", "/api/acceptance/60s"], evidence="heroes.py", efficiency="Routing surface; not live execution"),
        _f(id="UX-DISC", name="Discipline mirror", name_ar="مرآة الانضباط", domain="ux", status="works", personas=ALL, surfaces=["/discipline-mirror", "/api/discipline-mirror/*", "/my/discipline-mirror"], evidence="heroes.py", efficiency="Self-report path"),
        _f(id="WOW-CORE", name="WOW eight: kill-rate, replay, arena, since-left, anti-hype, corpus, committee, half-life clock", name_ar="الثمانية الفريدة: معدل القتل، إعادة التناقض، الحلبة، منذ المغادرة، ضد المبالغة، جواز المجموعة، لجنة، ساعة نصف العمر", domain="unique", status="works", personas=ALL, surfaces=["/kill-rate", "/contradiction-replay", "/proof-arena", "/since-you-left", "/anti-hype", "/corpus-passport", "/b2b/committee-one-pager", "/api/oracle/half-life/heat"], evidence="/api/wow/surfaces", efficiency="Shipped uniqueness surfaces; product_complete=false"),
        _f(id="WOW-F1F10", name="F1–F10 unique: miss-feed, emotion-tax, allocator, transfer, silence, passport, visibility, decay, duel, trust-debt", name_ar="F1–F10: تغذية الفوات، ضريبة العاطفة، إيصال المخصص، نية التحويل، مؤشر الصمت، جواز التنبيه، تكلفة الظهور، اضمحلال الصلاحية، مبارزة المكتب، دين الثقة", domain="unique", status="works", personas=ALL, surfaces=["/miss-feed", "/emotion-tax", "/allocator-receipt", "/transfer-intent", "/silence-index", "/alert-passport", "/visibility-cost", "/validity-decay", "/desk-duel", "/trust-debt", "/unique-ten"], evidence="/api/public/f1-f10-closure", efficiency="All ten pages+APIs shipped"),
        _f(id="WOW-COV", name="Coverage honesty / priority chain / zero-tolerance / d5", name_ar="صدق التغطية / سلسلة الأولوية / صفر تسامح / d5", domain="unique", status="works", personas=ALL, surfaces=["/coverage-honesty", "/priority-chain", "/zero-tolerance", "/d5-honesty"], evidence="heroes.py closures", efficiency="Honesty boards; radical_fix ≠ product_complete"),
        _f(id="WOW-GLASS", name="Glass-box challenge / operator / announce", name_ar="صندوق زجاجي تحدٍ / مشغّل / إعلان", domain="unique", status="works", personas=ALL, surfaces=["/api/glass-box/*"], evidence="heroes.py", efficiency="Public challenge path"),
        _f(id="WOW-PULSE", name="Trust pulse stream / manifest", name_ar="نبض الثقة بث / بيان", domain="unique", status="works", personas=ALL, surfaces=["/api/trust-pulse", "/api/trust-pulse/stream", "/api/dashboard/stream"], evidence="dashboard.py", efficiency="SSE/status; not a market-data SLA"),
        # ── ML / platform extras ──────────────────────────────
        _f(id="ML-TRAIN", name="ML train/predict/ensemble/experience", name_ar="تدريب/تنبؤ/تجميع/خبرة تعلم آلي", domain="ml", status="works", personas=["pro", "whale", "acquirer"], surfaces=["/api/ml/*", "/api/platform/ml/*"], evidence="platform_api.py", efficiency="Local models complete; not a hosted GPU farm"),
        _f(id="ML-EXPLAIN", name="ML explain / TruLens fallback", name_ar="تفسير النموذج / TruLens احتياطي", domain="ml", status="works", personas=["pro", "whale"], surfaces=["/api/platform/ml/explain"], evidence="bd_platform.trulens_eval", efficiency="Rules fallback always works; TruLens optional"),
        _f(id="PLAT-GRID", name="Grid bots / rules / marketplace / calendars", name_ar="بوتات شبكة / قواعد / سوق استراتيجيات / تقاويم", domain="platform", status="works", personas=["pro", "whale"], surfaces=["/api/platform/bots/grid", "/api/platform/rules", "/api/platform/marketplace/strategies", "/api/platform/events/calendar", "/platform"], evidence="platform_api.py", efficiency="In-process product complete; not Kaiko-class vendor data"),
        _f(id="PLAT-DERIV", name="Derivatives hub / liquidations / CEX-DEX compare", name_ar="مركز مشتقات / تصفيات / مقارنة منصة-DEX", domain="platform", status="works", personas=["pro", "whale"], surfaces=["/api/platform/derivatives/*", "/api/platform/liquidations/radar"], evidence="bd_platform.derivatives_hub", efficiency="Public-proxy hub complete; live options via paper OMS"),
        _f(id="PLAT-TV", name="TradingView config / webhook", name_ar="إعداد TradingView / ويب هوك", domain="platform", status="works", personas=["pro", "whale"], surfaces=["/api/platform/tradingview/*"], evidence="platform_api.py", efficiency="Webhook→paper path complete; live TV charting SaaS is not this product"),
        # ── B2B / WL / org ────────────────────────────────────
        _f(id="B2B-FEED", name="Institutional B2B JSON/WS feed", name_ar="تغذية B2B JSON/WS مؤسسية", domain="b2b", status="works", personas=["b2b", "whale"], surfaces=["/api/b2b/feed", "/ws/b2b/feed", "/api/b2b/info"], evidence="org_tenant.issue_org_feed_key", efficiency="Env key or hashed org key bd_org_"),
        _f(id="B2B-WL", name="White-label brand/portal/terminal/exports", name_ar="علامة بيضاء علامة/بوابة/طرفية/تصدير", domain="b2b", status="works", personas=["b2b", "fund"], surfaces=["/api/institutional/orgs/{id}/portal", "/api/institutional/white-label/*"], evidence="white_label.py", efficiency="In-process portal complete; hosted custom domain remains unpaid-excluded"),
        _f(id="B2B-WL-HOST", name="Hosted custom-domain white-label SaaS", name_ar="علامة بيضاء بنطاق مخصص مستضاف", domain="b2b", status="external_block", personas=["b2b"], surfaces=["white_label.hosted_custom_domain"], evidence="zero_cost unpaid infra", efficiency="Requires paid multi-tenant hosting", unpaid_block="hosted_custom_domain_requires_paid_infra"),
        _f(id="B2B-ORG", name="Org tenancy + RBAC + MFA policy", name_ar="مؤسسات + صلاحيات + سياسة MFA", domain="b2b", status="works", personas=INST, surfaces=["/api/institutional/orgs", "/api/institutional/rbac/matrix"], evidence="org_tenant.py org_rbac.py", efficiency="JSON store; not Okta-as-a-service"),
        _f(id="B2B-SSO", name="OIDC/SAML SSO", name_ar="تسجيل دخول موحد OIDC/SAML", domain="b2b", status="ops_config", personas=INST, surfaces=["/api/institutional/sso/*"], evidence="enterprise_sso.py", efficiency="Crypto path complete; live IdP needs owner credentials", unpaid_block="idp_credentials"),
        _f(id="B2B-SCIM", name="SCIM 2.0 Users/Groups", name_ar="SCIM 2.0 مستخدمون/مجموعات", domain="b2b", status="works", personas=INST, surfaces=["/api/institutional/scim/*", "/api/institutional/orgs/{id}/scim-key"], evidence="scim_service.py org_tenant.issue_org_scim_key", efficiency="CRUD + env bearer or hashed org bd_scim_ key"),
        _f(id="B2B-SUPER", name="Super terminal (org)", name_ar="طرفية فائقة للمؤسسة", domain="b2b", status="works", personas=INST, surfaces=["/api/institutional/super-terminal", "/api/institutional/orgs/{id}/terminal"], evidence="oms_decision.py", efficiency="In-process pack; live_fill=false disclosed"),
        # ── Fund / ops ────────────────────────────────────────
        _f(id="FUND-TERM", name="Emerging fund terminal + model card", name_ar="طرفية الصندوق الناشئ + بطاقة النموذج", domain="fund", status="works", personas=["fund", "acquirer"], surfaces=["/b2b?audience=fund", "/model-card", "/api/fund/emerging-terminal"], evidence="emerging_fund_terminal.py buyer_model_card.py", efficiency="DD packaging; not AUM custody"),
        _f(id="FUND-HA", name="Cloud multi-AZ HA", name_ar="توافر عالٍ سحابي متعدد المناطق", domain="ops", status="external_block", personas=["fund", "acquirer"], surfaces=["/api/institutional/ops/cloud-multi-az-prove"], evidence="zero_cost_no_paid_cloud_multi_az", efficiency="Honest EXTERNAL; local HA is separate", unpaid_block="zero_cost_no_paid_cloud_multi_az"),
        _f(id="FUND-PG", name="Local Postgres streaming HA RPO/RTO", name_ar="Postgres محلي تدفق HA RPO/RTO", domain="ops", status="works", personas=["fund", "acquirer"], surfaces=["/api/institutional/ops/postgres-ha-rpo-rto"], evidence="prove_postgres_streaming_ha_rpo_rto", efficiency="Sole VERIFIED_COMPLETE; cloud_multi_az=false"),
        _f(id="FUND-IR", name="IR / backup drill / dump-restore / recovery bundle", name_ar="استجابة حوادث / نسخ / استعادة / حزمة تعافٍ", domain="ops", status="works", personas=["acquirer"], surfaces=["/api/institutional/ops/recovery", "/api/institutional/ops/recovery-bundle", "/api/database/health"], evidence="ops_recovery.py", efficiency="Local drills complete; not paid multi-AZ"),
        _f(id="FUND-OBS", name="Observability / Prometheus / infra metrics", name_ar="رصد / Prometheus / مقاييس بنية", domain="ops", status="works", personas=["acquirer"], surfaces=["/metrics", "/api/observability/status", "/api/infra/metrics"], evidence="api/routers/observability.py", efficiency="Local scrape; not Datadog SaaS"),
        _f(id="FUND-HEALTH", name="Health live/ready/viral + status pages", name_ar="صحة حي/جاهز/فيروسي + صفحات الحالة", domain="ops", status="works", personas=ALL, surfaces=["/health", "/health/live", "/health/ready", "/status", "/api/status"], evidence="dashboard.py", efficiency="Process health ≠ cloud SLA"),
        # ── DD / launch / GTM ─────────────────────────────────
        _f(id="DD-PACK", name="Acquirer evidence pack + committee PDF", name_ar="حزمة أدلة المستحوذ + PDF لجنة", domain="dd", status="works", personas=["acquirer", "whale"], surfaces=["/api/due-diligence/evidence-pack", "/data-room", "/api/due-diligence/committee-one-pager.pdf"], evidence="due_diligence_bundle.py", efficiency="Embeds four-blockers NOT_COMPLETE"),
        _f(id="DD-FOUR", name="Four-blockers prove", name_ar="إثبات الحواجز الأربعة", domain="dd", status="works", personas=["acquirer"], surfaces=["scripts/prove_four_blockers.py", "/api/product/capability-inventory"], evidence="docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json", efficiency="Honest EXTERNAL labels"),
        _f(id="DD-LAUNCH", name="Launch checklist / production guard / GTM", name_ar="قائمة إطلاق / حارس إنتاج / GTM", domain="dd", status="works", personas=["acquirer"], surfaces=["/admin/launch", "/api/launch/readiness", "/api/gtm/status"], evidence="launch_checklist.py production_guard.py", efficiency="Honesty board complete; domain/golive remain owner ops"),
        _f(id="DD-PLAN", name="Plan / roadmap audit pages", name_ar="صفحات تدقيق الخطة / الخارطة", domain="dd", status="works", personas=["acquirer"], surfaces=["/admin/plan", "/admin/roadmap", "/api/plan/audit", "/api/roadmap/audit"], evidence="dashboard.py", efficiency="Honesty audit; Vault roadmap PARTIAL"),
        # ── Privacy / legal / site ────────────────────────────
        _f(id="PRV-DSR", name="GDPR DSR export/erase + privacy status", name_ar="GDPR تصدير/مسح + حالة الخصوصية", domain="privacy", status="works", personas=ALL, surfaces=["/api/privacy/status", "/api/privacy/dsr/export", "/api/privacy/dsr/erase"], evidence="api/routers/privacy.py gdpr_service.py", efficiency="Authenticated DSR path"),
        _f(id="PRV-REG", name="Regulatory compliance posture", name_ar="وضعية الامتثال التنظيمي", domain="privacy", status="works", personas=ALL, surfaces=["/compliance", "/api/regulatory/compliance", "/api/institutional/compliance"], evidence="regulatory_compliance_guard.py", efficiency="Engineering posture, not a license"),
        _f(id="SITE-LEGAL", name="Legal/FAQ/contact/about/how-it-works/changelog/feedback", name_ar="قانوني/أسئلة/اتصال/عن/كيف يعمل/سجل/ملاحظات", domain="site", status="works", personas=ALL, surfaces=["/terms", "/privacy", "/disclaimer", "/refund", "/cookies", "/faq", "/contact", "/about", "/how-it-works", "/changelog", "/feedback", "/complaints", "/legal"], evidence="dashboard.py", efficiency="Public pages render"),
        _f(id="SITE-I18N", name="i18n locales/catalog", name_ar="محليات/كتالوج ترجمة", domain="site", status="works", personas=ALL, surfaces=["/api/i18n/locales", "/api/i18n/catalog"], evidence="dashboard.py", efficiency="Catalog served; UI language primarily EN"),
        _f(id="SITE-PWA", name="PWA manifest / service worker / SEO", name_ar="PWA بيان / عامل خدمة / سيو", domain="site", status="works", personas=ALL, surfaces=["/manifest.json", "/sw.js", "/robots.txt", "/sitemap.xml", "/favicon.ico"], evidence="dashboard.py", efficiency="Installable shell"),
        _f(id="SITE-DOCS", name="Public docs / OpenAPI", name_ar="وثائق عامة / OpenAPI", domain="site", status="works", personas=ALL, surfaces=["/docs", "/docs/public", "/api/docs/openapi.json", "/api/docs/public-openapi.json"], evidence="dashboard.py", efficiency="Public subset documented"),
        _f(id="SITE-GQL", name="GraphQL router", name_ar="موجّه GraphQL", domain="site", status="works", personas=PAID, surfaces=["/graphql"], evidence="graphql_schema.py", efficiency="Health, accuracy, arb, risk, sources, capability inventory"),
        _f(id="SEC-KEYS", name="Security API keys / events / admin MFA status", name_ar="مفاتيح أمن / أحداث / حالة MFA للمشرف", domain="security", status="works", personas=DESK, surfaces=["/api/security/api-keys", "/api/security/events", "/api/security/status", "/api/security/admin-mfa"], evidence="dashboard.py", efficiency="Status surfaces; secrets never logged"),
        _f(id="INV-FULL", name="Full capability inventory API (this catalog)", name_ar="واجهة جرد القدرات الكاملة", domain="dd", status="works", personas=ALL, surfaces=["/api/product/capability-inventory", "/api/product/unpaid-closure"], evidence="product_capability_inventory.py unpaid_institutional_closure.py", efficiency="Binding machine-readable inventory; NOT_COMPLETE"),
    ]


def inventory_summary(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = rows or capability_catalog()
    by_status: dict[str, int] = {}
    by_domain: dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
        by_domain[r["domain"]] = by_domain.get(r["domain"], 0) + 1
    return {
        "total": len(rows),
        "by_status": by_status,
        "by_domain": by_domain,
        "works": by_status.get("works", 0),
        "partial": by_status.get("partial", 0),
        "gated": by_status.get("gated", 0),
        "external_block": by_status.get("external_block", 0),
        "ops_config": by_status.get("ops_config", 0),
    }


def personas_for_entitlement() -> dict[str, list[str]]:
    """Every capability id each persona is entitled to (status ≠ gated away)."""
    out: dict[str, list[str]] = {p: [] for p in ("retail", "pro", "whale", "fund", "b2b", "acquirer")}
    for row in capability_catalog():
        for p in row["personas"]:
            out[p].append(row["id"])
    return out


def institutional_review() -> dict[str, Any]:
    """Structured answers to the eight operator asks — never COMPLETE."""
    return {
        "ask_1_full_inventory": "capability_catalog() is the binding inventory (id/domain/status/personas/surfaces/evidence/efficiency).",
        "ask_2_precise_review": "Each row has status + efficiency + unpaid_block. Domain reviews live in docs/dd/BLACKDARK_FULL_CAPABILITY_INSTITUTIONAL_REVIEW.md.",
        "ask_3_efficiency": {
            "unpaid_paths_verified_by": [
                "historical_self_grade from audit chain (same-tick withheld)",
                "options paper OMS at Deribit mark",
                "org-scoped SCIM bearer bd_scim_",
                "GraphQL capabilityInventory",
                "pytest tests/test_unpaid_partial_closure.py",
                "CORE mesh 77/77 and catalog venue_l2 80/100",
            ],
            "not_claimed": [
                "live_fill",
                "jupiter_onchain_vc",
                "full_mesh_l2_100",
                "cloud_multi_az",
            ],
        },
        "ask_4_nothing_forgotten_or_broken": {
            "gated_is_not_broken": True,
            "external_block_is_not_product_defect": True,
            "fixed_this_wave": [
                "historical independent self-grade (not same-tick stub)",
                "Deribit paper options OMS",
                "org-scoped SCIM keys",
                "arb catalog CEX-DEX live + options vs spot proxy + name_ar",
                "GraphQL capability inventory",
                "reclassify unpaid-complete partials to works",
            ],
            "previously_fixed_unpaid": [
                "/settings/security 307 to /profile",
                "six-audience routing",
                "org-scoped B2B feed keys",
            ],
            "known_stopped_product_defects": [],
            "known_external_or_ops_stops": [
                "binance_order_host_geo_451",
                "wallet_unfunded_zero_cost_constraint",
                "amm_and_bybit_geo remaining synthetic_mid",
                "zero_cost_no_paid_cloud_multi_az",
                "psp_credentials",
                "telegram_bot_token",
                "oauth_client_ids",
                "mail_transport",
                "hosted_custom_domain_requires_paid_infra",
            ],
        },
        "ask_5_every_user_gets_entitled_capabilities": {
            "retail_free": "Proof Pass: 3 Oracle/day, ledger, journal, uniqueness surfaces, MFA, legal. No arb/alerts/execution.",
            "pro": "Unlimited Oracle, radar, arb catalog, research, alerts subscribe path, sim, portfolio AI. Checkout needs PSP.",
            "whale": "Desk + OMS paper + vault + B2B feed + evidence. live_fill and Jupiter VC external.",
            "fund": "Fund terminal + DD room + org RBAC. Cloud multi-AZ external. Local PG HA verified.",
            "b2b": "Org feed key + in-process WL portal. Hosted custom domain unpaid-excluded.",
            "acquirer": "Evidence pack with NOT_COMPLETE + four blockers. No fake COMPLETE.",
        },
        "ask_6_defects_and_weaknesses": [
            {"id": "live_fill_geo", "type": "external", "impact": "Whale cannot prove venue FILL"},
            {"id": "jupiter_unfunded", "type": "external", "impact": "No on-chain VC"},
            {"id": "l2_80_of_100", "type": "unpaid_ceiling", "impact": "~20 synthetic_mid (AMM + bybit geo)"},
            {"id": "no_cloud_multi_az", "type": "external", "impact": "Cloud SLA unproven"},
            {"id": "psp_not_armed", "type": "ops", "impact": "Self-serve upgrade cannot complete a live charge"},
            {"id": "oauth_client_ids", "type": "ops", "impact": "Live Google/GitHub login needs owner client ids"},
            {"id": "wl_hosted_domain", "type": "external", "impact": "Custom-domain WL SaaS needs paid infra"},
        ],
        "ask_7_missing_essentials": {
            "for_unpaid_trial": [
                "None that block retail/pro paper trial once the app is running",
            ],
            "for_live_money": [
                "Binance order host from allowed geo or proxy",
                "Funded Jupiter wallet (SOL+USDC) or funded key",
                "Live PSP secrets",
                "Production domain + TLS",
            ],
            "for_institutional_complete": [
                "Cloud multi-AZ (paid)",
                "Catalog L2 100% (AMM books are not CEX L2 — do not invent)",
                "Hosted custom-domain WL (paid infra)",
            ],
        },
        "ask_8_must_still_implement": {
            "unpaid_remaining": [
                "Do not invent AMM CEX-style L2 — keep synthetic_mid labeled (80/100 is the unpaid ceiling)",
            ],
            "ops_owner": [
                "PSP secrets",
                "Telegram bot token",
                "OAuth client ids",
                "Mail transport",
                "Production domain/TLS",
            ],
            "external_paid_excluded": [
                "Geo unblock or proxy for Binance order hosts",
                "Wallet funding",
                "Paid cloud multi-AZ",
                "Hosted custom-domain multi-tenant WL",
            ],
        },
        "binding_verdict": "NOT_COMPLETE",
        "trial_ready_unpaid": True,
        "live_money_ready": False,
        "product_complete": False,
    }


def build_full_capability_inventory() -> dict[str, Any]:
    rows = capability_catalog()
    four: dict[str, Any] = {}
    try:
        import json
        from pathlib import Path

        p = Path("docs/dd/BLACKDARK_FOUR_BLOCKERS_EVIDENCE.json")
        if p.is_file():
            four = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        four = {}
    b1 = four.get("blocker_1_live_venue_fill") or {}
    b2 = four.get("blocker_2_jupiter_live_signature") or {}
    b3 = four.get("blocker_3_full_mesh_100") or {}
    b4 = four.get("blocker_4_cloud_multi_az_ha") or {}
    return {
        "ok": True,
        "surface": "full_product_capability_inventory",
        "product_complete": False,
        "institutional_verdict": "NOT_COMPLETE",
        "trial_ready_unpaid": True,
        "live_money_ready": False,
        "proved_at": _utcnow(),
        "summary": inventory_summary(rows),
        "capabilities": rows,
        "entitlements": personas_for_entitlement(),
        "review": institutional_review(),
        "four_blockers": {
            "live_fill": b1.get("live_fill"),
            "jupiter_vc": b2.get("verified_complete"),
            "l2_pct": b3.get("institutional_l2_coverage_percent"),
            "full_mesh_l2_complete": False,
            "cloud_multi_az": b4.get("cloud_multi_az"),
        },
        "integrity": {
            "never_claim_without_evidence": True,
            "gated_is_not_broken": True,
            "external_block_is_not_product_defect": True,
            "synthetic_mid_is_not_venue_l2": True,
            "local_sign_is_not_rpc_vc": True,
            "local_pg_ha_is_not_cloud_multi_az": True,
        },
        "report": "docs/dd/BLACKDARK_FULL_CAPABILITY_INSTITUTIONAL_REVIEW.md",
        "closure_recommendation": "docs/dd/BLACKDARK_UNPAID_PARTIAL_CLOSURE_RECOMMENDATION.md",
        "prior_persona_report": "docs/dd/BLACKDARK_TRIAL_PERSONA_READINESS_REPORT.md",
    }
