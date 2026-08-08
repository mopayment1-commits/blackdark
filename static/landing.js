function _secureRandomId(len){const a=new Uint8Array(Math.max(4,len||8));crypto.getRandomValues(a);return Array.from(a,b=>b.toString(16).padStart(2,'0')).join('').slice(0,len||8);}

        window.lastOracleResult = null;

        function buildSharePayload(result) {
            const url = window.location.origin + '/';
            if (!result) {
                return {
                    url,
                    text: 'BLACKDARK Oracle — AI crypto signals in 30 seconds 🔮',
                };
            }
            const price = result.price != null ? `$${Number(result.price).toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '';
            const text = [
                `BLACKDARK Oracle: ${result.verdict} ${result.symbol}${price ? ' @ ' + price : ''}`,
                `Score: ${result.opportunity_score}/100 · Confidence: ${result.confidence || '—'}%`,
                (result.narrative || result.oracle || '').slice(0, 160),
            ].filter(Boolean).join('\n');
            return { url, text };
        }

        function updateShareLinks(result) {
            window.lastOracleResult = result;
            const { url, text } = buildSharePayload(result);
            const full = `${text}\n${url}`;

            const xBtn = document.getElementById('shareXBtn');
            const fbBtn = document.getElementById('shareFacebookBtn');
            const waBtn = document.getElementById('shareWhatsappBtn');
            const tgBtn = document.getElementById('shareTelegramBtn');
            const rdBtn = document.getElementById('shareRedditBtn');

            if (xBtn) xBtn.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`;
            if (fbBtn) fbBtn.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}&quote=${encodeURIComponent(text)}`;
            if (waBtn) waBtn.href = `https://wa.me/?text=${encodeURIComponent(full)}`;
            if (tgBtn) tgBtn.href = `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`;
            if (rdBtn) rdBtn.href = `https://www.reddit.com/submit?url=${encodeURIComponent(url)}&title=${encodeURIComponent(text)}`;

            const igBtn = document.getElementById('shareInstagramBtn');
            if (igBtn) {
                igBtn.onclick = function(e) {
                    e.preventDefault();
                    navigator.clipboard.writeText(full).then(() => {
                        igBtn.textContent = 'Copied!';
                        setTimeout(() => { igBtn.textContent = 'Instagram'; }, 2000);
                    });
                };
            }

            const copyBtn = document.getElementById('shareCopyBtn');
            if (copyBtn) {
                copyBtn.onclick = function(e) {
                    e.preventDefault();
                    navigator.clipboard.writeText(full).then(() => {
                        copyBtn.textContent = 'Copied!';
                        copyBtn.classList.add('copied');
                        setTimeout(() => {
                            copyBtn.textContent = 'Copy Link';
                            copyBtn.classList.remove('copied');
                        }, 2000);
                    });
                };
            }
        }

        async function consultOracle() {
            const symbol = document.getElementById('symbolInput').value.toUpperCase();
            const mode = document.getElementById('landingUxMode').value || 'beginner';
            const lang = 'en';
            const resultDiv = document.getElementById('oracleResult');
            const symbolEl = document.getElementById('resultSymbol');
            const scoreEl = document.getElementById('resultScore');
            const verdictEl = document.getElementById('resultVerdict');
            const oracleEl = document.getElementById('resultOracle');
            const proMeta = document.getElementById('landingProMeta');
            const upgradeEl = document.getElementById('landingUpgrade');
            
            resultDiv.classList.add('active');
            localStorage.setItem('bd_ux_mode', mode);
            localStorage.setItem('bd_lang', lang);
            oracleEl.textContent = 'Getting your decision…';
            proMeta.style.display = 'none';
            upgradeEl.style.display = 'none';
            
            try {
                let response = await fetch(`/oracle/${encodeURIComponent(symbol)}?ux_mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`, { headers: { Accept: 'application/json' } });
                let rawText = await response.text();
                let data = null;
                try { data = rawText && !rawText.trim().startsWith('<') && !rawText.includes('Internal Server Error') ? JSON.parse(rawText) : null; } catch (e) { data = null; }
                if (!data || !response.ok) {
                    // Production fallback when full Oracle path errors
                    response = await fetch(`/oracle/${encodeURIComponent(symbol)}/quick?ux_mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`, { headers: { Accept: 'application/json' } });
                    rawText = await response.text();
                    try { data = JSON.parse(rawText); } catch (e) { data = null; }
                }
                if (!data) {
                    oracleEl.textContent = 'Could not get a decision right now. Try again.';
                    verdictEl.textContent = 'WAIT';
                    verdictEl.className = 'result-verdict verdict-wait';
                    return;
                }
                if (!response.ok) {
                    const detail = data.detail || {};
                    const msg = detail.message || 'Daily quota exceeded — upgrade';
                    oracleEl.textContent = msg;
                    if (detail.upgrade_url || detail.error === 'quota_exceeded') {
                        upgradeEl.style.display = 'block';
                        upgradeEl.innerHTML = `<a class="btn-primary" href="${detail.upgrade_url || '/create-checkout-session?tier=pro'}">Upgrade to Pro</a>`;
                    }
                    return;
                }
                
                symbolEl.textContent = data.symbol || symbol;
                scoreEl.textContent = data.opportunity_score ?? '--';
                
                const rawAction = String(data.decision_action || data.verdict || data.action || 'WAIT').toUpperCase();
                const action = (rawAction === 'ACT' || rawAction.includes('BUY') || rawAction.includes('BULL'))
                    ? 'ACT'
                    : 'WAIT';
                const verdict = data.verdict || action;
                verdictEl.textContent = action;
                verdictEl.className = 'result-verdict';
                const v = String(verdict).toUpperCase();
                if (action === 'ACT' || v.includes('BUY')) verdictEl.classList.add('verdict-buy');
                else if (v.includes('SELL')) verdictEl.classList.add('verdict-sell');
                else verdictEl.classList.add('verdict-wait');
                
                let sentence = data.decision_sentence || data.narrative || data.oracle || data.action_line || '';
                if (!sentence || /meditat|consulting the oracle/i.test(sentence)) {
                    sentence = typeof data.action === 'string' && data.action.length > 12
                        ? data.action
                        : (action === 'ACT'
                            ? `ACT on ${data.symbol || symbol} — score ${data.opportunity_score ?? '—'}.`
                            : `WAIT on ${data.symbol || symbol} — score ${data.opportunity_score ?? '—'}.`);
                }
                oracleEl.textContent = sentence;
                if (mode === 'pro') {
                    const truth = data.net_edge_truth || {};
                    const half = data.opportunity_half_life || {};
                    const conflict = data.dimension_conflict || {};
                    let line = `Truth ${truth.truth_score ?? '—'} · Half-life ${half.remaining_seconds ?? '—'}s · Regime ${data.market_regime || '—'}`;
                    if (conflict.veto || conflict.abstain || (conflict.severity && conflict.severity !== 'none')) {
                        line += ` · Contradiction Veto: ${conflict.veto ? 'WAIT' : 'Abstain'}${conflict.severity ? ' (' + conflict.severity + ')' : ''}`;
                    }
                    if (data.prediction_id) {
                        line += ` · Proof #${data.prediction_id}`;
                    }
                    proMeta.style.display = 'block';
                    proMeta.innerHTML = line + (data.prediction_id
                        ? ` · <a href="/oracle-accuracy" style="color:var(--accent)">accuracy</a>`
                        : '');
                } else if (data.prediction_id) {
                    proMeta.style.display = 'block';
                    proMeta.innerHTML = `Proof · prediction_id <code>${data.prediction_id}</code> · <a href="/oracle-accuracy" style="color:var(--accent)">Public accuracy</a>`;
                }
                if (data.upgrade_hint) {
                    const teaser = data.upgrade_hint.teaser || {};
                    const teaserLine = [
                        teaser.truth_score != null ? `Truth teaser ${teaser.truth_score}` : null,
                        teaser.remaining_seconds != null ? `Half-life ~${teaser.remaining_seconds}s` : null,
                        teaser.regime ? `Regime ${teaser.regime}` : null,
                    ].filter(Boolean).join(' · ');
                    upgradeEl.style.display = 'block';
                    upgradeEl.innerHTML =
                        `<div style="color:var(--text-muted);font-size:.85rem;margin-bottom:.5rem">${data.upgrade_hint.message || ''}` +
                        (teaserLine ? `<br>${teaserLine}` : '') +
                        `</div><button type="button" class="btn-secondary" id="switchProBtn">Switch to Pro</button>`;
                    document.getElementById('switchProBtn')?.addEventListener('click', () => {
                        const sel = document.getElementById('landingUxMode');
                        if (sel) sel.value = 'pro';
                        consultOracle();
                    });
                }
                const certEl = document.getElementById('landingCert');
                const cert = data.decision_certificate || {};
                if (cert.certificate_hash || data.prediction_id) {
                    certEl.style.display = 'block';
                    certEl.innerHTML =
                        `Decision Certificate · <code>${cert.certificate_hash ? String(cert.certificate_hash).slice(0,16)+'…' : 'pending'}</code>` +
                        `<div style="margin-top:.35rem">` +
                        (cert.share_text ? `<button type="button" class="btn-secondary" id="copyCertBtn">Copy certificate</button> ` : '') +
                        `<button type="button" class="btn-secondary" id="dlCertBtn">Download JSON</button></div>`;
                    document.getElementById('copyCertBtn')?.addEventListener('click', () => {
                        navigator.clipboard.writeText(cert.share_text || '');
                    });
                    document.getElementById('dlCertBtn')?.addEventListener('click', () => {
                        const blob = new Blob([JSON.stringify(cert, null, 2)], {type:'application/json'});
                        const a = document.createElement('a');
                        a.href = URL.createObjectURL(blob);
                        a.download = `blackdark-certificate-${(data.symbol||'asset').toLowerCase()}.json`;
                        a.click();
                        URL.revokeObjectURL(a.href);
                    });
                } else {
                    certEl.style.display = 'none';
                }

                const factors = (data.explanation && data.explanation.top_3_factors) || data.top_3_factors || [];
                let whyEl = document.getElementById('landingWhy');
                if (!whyEl) {
                    whyEl = document.createElement('div');
                    whyEl.id = 'landingWhy';
                    whyEl.style.cssText = 'margin-top:.75rem;font-size:.85rem;color:var(--text-muted);text-align:left';
                    oracleEl.parentNode.insertBefore(whyEl, oracleEl.nextSibling);
                }
                if (factors.length) {
                    whyEl.innerHTML = '<strong style="color:var(--text)">Why (Top-3)</strong><ol style="margin:.35rem 0 0 1.1rem">' +
                        factors.slice(0,3).map(f => {
                            const label = f.factor || f.label || f.name || f;
                            const src = f.source ? ` <span style="opacity:.7">· ${f.source}</span>` : '';
                            return `<li>${label}${src}</li>`;
                        }).join('') + '</ol>';
                } else {
                    whyEl.innerHTML = '';
                }

                const disc = document.getElementById('landingDiscipline');
                const systemAction = data.decision_action || data.verdict || action || 'WAIT';
                disc.style.display = 'block';
                disc.innerHTML =
                    `<div style="font-size:.85rem;color:var(--text-muted);margin-bottom:.4rem">Discipline Mirror (private) — did you follow this signal? <a href="/discipline-mirror" style="color:var(--accent)">Open my page</a></div>` +
                    `<button type="button" class="btn-secondary" id="followedYes">Yes, I followed</button> ` +
                    `<button type="button" class="btn-secondary" id="followedNo">No, I overrode</button>` +
                    `<div id="disciplineMsg" style="margin-top:.4rem;font-size:.78rem;color:var(--text-muted)"></div>`;
                const sendFollow = async (followed) => {
                    const key = localStorage.getItem('bd_user_key') || ('anon_' + _secureRandomId(8));
                    localStorage.setItem('bd_user_key', key);
                    try {
                        await fetch('/api/discipline-mirror/answer', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                user_key: key,
                                asset: data.symbol || symbol,
                                system_action: systemAction,
                                followed,
                                prediction_id: data.prediction_id,
                                opportunity_score: data.opportunity_score,
                            }),
                        });
                        document.getElementById('disciplineMsg').textContent = 'Saved privately — only you can see your Discipline Mirror.';
                    } catch (e) {
                        document.getElementById('disciplineMsg').textContent = 'Could not save answer.';
                    }
                };
                document.getElementById('followedYes')?.addEventListener('click', () => sendFollow(true));
                document.getElementById('followedNo')?.addEventListener('click', () => sendFollow(false));

                const foot = data.compliance_footer || {};
                const comp = document.getElementById('landingCompliance');
                if (foot.disclaimer) {
                    comp.style.display = 'block';
                    comp.innerHTML = `<strong>Anti-Hype</strong> · Source: ${foot.data_source || '—'} · Trust: ${foot.trust_basis || '—'}<br>${foot.disclaimer}`;
                }

                updateShareLinks(data);
            } catch (error) {
                oracleEl.textContent = 'Oracle unavailable — try BTC or ETH.';
            }
        }

        async function applyAudience() {
            const aud = document.getElementById('landingAudience')?.value || 'retail';
            localStorage.setItem('bd_audience', aud);
            try {
                const res = await fetch('/api/audience/entry?audience=' + encodeURIComponent(aud));
                const d = await res.json();
                const cta = document.getElementById('audienceCta');
                if (cta) cta.textContent = d.cta || '';
                const mode = document.getElementById('landingUxMode');
                if (mode && d.ux_mode_default) mode.value = d.ux_mode_default;
                if (aud === 'fund' && d.entry_path) {
                    window.location.href = d.entry_path;
                } else if ((aud === 'whale' || aud === 'pro') && d.entry_path) {
                    window.location.href = d.entry_path;
                }
            } catch (e) { /* ignore */ }
        }
        
        async function joinWaitlist(e) {
            e.preventDefault();
            const email = document.getElementById('waitlistEmail').value;
            const msg = document.getElementById('waitlistMessage');
            
            try {
                const response = await fetch('/join-waitlist', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                const data = await response.json();
                if (!response.ok) {
                    msg.textContent = data.detail || data.message || 'Something went wrong.';
                    msg.style.color = response.status === 409 ? 'var(--warning)' : 'var(--danger)';
                } else {
                    msg.textContent = data.message || `Welcome! You are #${data.position} on the waitlist.`;
                    msg.style.color = 'var(--success)';
                    document.getElementById('waitlistEmail').value = '';
                }
                msg.style.display = 'block';
            } catch (error) {
                msg.textContent = 'Something went wrong. Try again.';
                msg.style.color = 'var(--danger)';
                msg.style.display = 'block';
            }
        }
        
        async function loadLandingAnalytics() {
            try {
                await fetch('/api/analytics/view', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ page: 'landing' })
                });
                const [analyticsRes, usersRes, telegramRes] = await Promise.all([
                    fetch('/api/analytics/stats'),
                    fetch('/api/platform/stats'),
                    fetch('/api/telegram/free/status'),
                ]);
                const analytics = await analyticsRes.json();
                const users = await usersRes.json();
                const telegram = await telegramRes.json();
                document.getElementById('landingViews').textContent =
                    (analytics.landing_views || 0).toLocaleString();
                document.getElementById('landingUsers').textContent =
                    (users.registered_users || 0).toLocaleString();
                document.getElementById('landingSubs').textContent =
                    (users.paid_subscribers || analytics.subscriber_count || 0).toLocaleString();
                document.getElementById('landingTelegram').textContent =
                    (telegram.active_subscribers || users.telegram_free_subscribers || 0).toLocaleString();
                document.getElementById('landingWaitlist').textContent =
                    (analytics.waitlist_count || 0).toLocaleString();
            } catch (e) {}
        }

        async function loadTelegramBotLink() {
            try {
                const res = await fetch('/api/telegram/free/status');
                const data = await res.json();
                const link = document.getElementById('telegramBotLink');
                if (!link) return;
                const username = (data.bot_username || '').replace('@', '');
                if (username) {
                    link.href = `https://t.me/${username}`;
                    link.textContent = `@${username} — Start Free`;
                }
            } catch (e) {}
        }

        function whenIdle(fn, timeout) {
            if ('requestIdleCallback' in window) {
                requestIdleCallback(fn, { timeout: timeout || 2000 });
            } else {
                setTimeout(fn, 1);
            }
        }

        function bootLanding() {
            updateShareLinks(null);
            whenIdle(() => {
                loadLandingAnalytics();
                loadTelegramBotLink();
            }, 2500);
            const oracleEl = document.getElementById('oracle');
            let oracleBooted = false;
            const bootOracle = () => {
                if (oracleBooted) return;
                oracleBooted = true;
                whenIdle(() => { consultOracle(); }, 1500);
            };
            if (oracleEl && 'IntersectionObserver' in window) {
                const io = new IntersectionObserver((entries) => {
                    if (entries.some((e) => e.isIntersecting)) {
                        bootOracle();
                        io.disconnect();
                    }
                }, { rootMargin: '120px' });
                io.observe(oracleEl);
            } else {
                whenIdle(bootOracle, 2000);
            }
            if ('serviceWorker' in navigator) {
                whenIdle(() => { navigator.serviceWorker.register('/sw.js').catch(() => {}); }, 4000);
            }
        }
        if (document.readyState === 'complete') bootLanding();
        else window.addEventListener('load', bootLanding);
