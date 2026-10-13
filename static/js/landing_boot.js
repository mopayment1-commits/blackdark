        const { escapeHtml, esc, safeUrl, setAnchorHref, assignLocationHref, openWindow } = window.BDDomSafe;

        function scheduleNonCriticalLandingWork(fn) {
            let ran = false;
            const run = () => {
                if (ran) return;
                ran = true;
                fn();
            };
            const once = { once: true, passive: true };
            ['pointerdown', 'keydown', 'touchstart', 'scroll'].forEach((ev) => {
                window.addEventListener(ev, run, once);
            });
            if (typeof requestIdleCallback === 'function') {
                requestIdleCallback(run, { timeout: 3500 });
            } else {
                setTimeout(run, 2500);
            }
        }

        function currentLang() {
            return (window.BD_I18N && window.BD_I18N.lang) || document.documentElement.lang || 'en';
        }
        function i18nT(key, vars) {
            const i18n = window.BD_I18N;
            if (i18n && typeof i18n.t === 'function') return i18n.t(key, vars || {});
            return key;
        }

function _secureRandomId(len){const a=new Uint8Array(Math.max(4,len||8));crypto.getRandomValues(a);return Array.from(a,b=>b.toString(16).padStart(2,'0')).join('').slice(0,len||8);}

        window.lastOracleResult = null;

        function buildSharePayload(result) {
            const url = window.location.origin + '/';
            if (!result) {
                return {
                    url,
                    text: 'BLACKDARK Trust Pulse — one Act/Wait decision you can verify',
                };
            }
            const price = result.price != null ? `$${Number(result.price).toLocaleString(undefined, { maximumFractionDigits: 2 })}` : '';
            const publicVerdict = window.BDPublicDecision?.mapPublicDecisionAction(
                result.decision_action || result.model_state || result.verdict || result.action
            ) || result.verdict;
            const text = [
                `BLACKDARK Oracle: ${publicVerdict} ${result.symbol}${price ? ' @ ' + price : ''}`,
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

            if (xBtn) setAnchorHref(xBtn, `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`);
            if (fbBtn) setAnchorHref(fbBtn, `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}&quote=${encodeURIComponent(text)}`);
            if (waBtn) setAnchorHref(waBtn, `https://wa.me/?text=${encodeURIComponent(full)}`);
            if (tgBtn) setAnchorHref(tgBtn, `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`);
            if (rdBtn) setAnchorHref(rdBtn, `https://www.reddit.com/submit?url=${encodeURIComponent(url)}&title=${encodeURIComponent(text)}`);

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


        async function fetchOraclePayload(symbol, mode, lang) {
            const preferQuick = mode !== 'pro';
            const primary = preferQuick
                ? `/oracle/${encodeURIComponent(symbol)}/quick?ux_mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`
                : `/oracle/${encodeURIComponent(symbol)}?ux_mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`;
            const fallback = preferQuick
                ? `/oracle/${encodeURIComponent(symbol)}?ux_mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`
                : `/oracle/${encodeURIComponent(symbol)}/quick?ux_mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`;
            let response = await fetch(primary, { headers: { Accept: 'application/json' } });
            let rawText = await response.text();
            let data = null;
            try {
                data = rawText && !rawText.trim().startsWith('<') && !rawText.includes('Internal Server Error')
                    ? JSON.parse(rawText) : null;
            } catch (error) { console.debug(error); data = null; }
            if (!data || !response.ok) {
                response = await fetch(fallback, { headers: { Accept: 'application/json' } });
                rawText = await response.text();
                try { data = JSON.parse(rawText); } catch (error) { console.debug(error); data = null; }
            }
            return { response, data };
        }
        function decideLandingAction(data) {
            const raw = data.decision_action || data.model_state || data.verdict || data.action || 'WAIT';
            const mapFn = window.BDPublicDecision?.mapPublicDecisionAction;
            if (typeof mapFn === 'function') return mapFn(raw);
            const rawAction = String(raw).toUpperCase();
            if (rawAction.includes('CONDITION') || rawAction === 'ACT' || rawAction.includes('BUY') || rawAction.includes('BULL')) {
                return 'CONDITIONS MET';
            }
            if (rawAction.includes('ABSTAIN') || rawAction.includes('SELL')) return 'ABSTAIN';
            return 'WAIT';
        }
        const BD_CONDITIONS_MET_REVIEW = "Analytical state only - the model's stated conditions are currently met. No transaction or investment action is recommended.";
        function fallbackDecisionSentence(data, symbol, action, mode) {
            if (mode === 'pro' && data.decision_sentence_pro) return data.decision_sentence_pro;
            let sentence = data.decision_sentence || data.conditions_met_review || data.narrative || data.oracle || data.action_line || '';
            if (sentence && !/meditat|consulting the oracle/i.test(sentence)) return sentence;
            if (typeof data.action === 'string' && data.action.length > 12 && !/\bBuy\b/i.test(data.action)) return data.action;
            if (action === 'CONDITIONS MET') {
                return `MODEL STATE: CONDITIONS MET — ${data.symbol || symbol}. ${BD_CONDITIONS_MET_REVIEW}`;
            }
            return `MODEL STATE: ${action} — ${data.symbol || symbol}.`;
        }
        function renderLandingCertificate(certEl, cert, data) {
            if (!(cert.certificate_hash || data.prediction_id)) {
                certEl.style.display = 'none';
                return;
            }
            certEl.style.display = 'block';
            const hashLabel = cert.certificate_hash ? String(cert.certificate_hash).slice(0,16)+'…' : 'pending';
            const copyBtn = cert.share_text ? `<button type="button" class="btn-secondary" id="copyCertBtn">Copy certificate</button>` : '';
            const txtBtn = cert.export_text ? `<button type="button" class="btn-secondary" id="dlCertTxtBtn">Download TXT</button>` : '';
            const xHref = safeUrl(cert.share_urls && cert.share_urls.x);
            const tgHref = safeUrl(cert.share_urls && cert.share_urls.telegram);
            const xBtn = xHref ? `<a class="btn-secondary" id="certShareX" href="${xHref}" target="_blank" rel="noopener">Share X</a>` : '';
            const tgBtn = tgHref ? `<a class="btn-secondary" id="certShareTg" href="${tgHref}" target="_blank" rel="noopener">Share TG</a>` : '';
            certEl.innerHTML =
                `Decision Certificate · <code>${esc(hashLabel)}</code>` +
                `<div style="margin-top:.35rem;display:flex;flex-wrap:wrap;gap:.35rem">` +
                copyBtn +
                `<button type="button" class="btn-secondary" id="dlCertBtn">Download JSON</button>` +
                txtBtn + xBtn + tgBtn + `</div>`;
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
            document.getElementById('dlCertTxtBtn')?.addEventListener('click', () => {
                const blob = new Blob([cert.export_text || ''], {type:'text/plain'});
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = `blackdark-certificate-${(data.symbol||'asset').toLowerCase()}.txt`;
                a.click();
                URL.revokeObjectURL(a.href);
            });
        }
        function renderLandingWhy(oracleEl, data, cert, latencyMs) {
            const whyBlock = data.oqs_why || {};
            const factors = whyBlock.top_3_factors
                || (data.explanation && data.explanation.top_3_factors)
                || data.top_3_factors
                || [];
            const scen = (data.scenarios && data.scenarios.scenarios) || {};
            let whyEl = document.getElementById('landingWhy');
            if (!whyEl) {
                whyEl = document.createElement('div');
                whyEl.id = 'landingWhy';
                whyEl.style.cssText = 'margin-top:.75rem;font-size:.85rem;color:var(--text-muted);text-align:left';
                oracleEl.parentNode.insertBefore(whyEl, oracleEl.nextSibling);
            }
            let scenHtml = '';
            if (scen.bull || scen.base || scen.bear) {
                const bits = ['bull','base','bear'].map(k => {
                    const s = scen[k] || {};
                    const pct = s.probability_pct != null ? s.probability_pct+'%' : '—';
                    return `${esc(s.label||k)} ${esc(pct)}`;
                }).join(' · ');
                const disc = (data.scenarios && data.scenarios.disclaimer) || '';
                scenHtml = `<div style="margin-top:.65rem"><strong style="color:var(--text)">Scenarios</strong> · ${bits}<div style="font-size:.75rem;margin-top:.25rem;opacity:.8">${esc(disc)}</div></div>`;
            }
            let whyList = '<p style="margin-top:.35rem">No factor breakdown on this response.</p>';
            if (factors.length) {
                whyList = '<ol style="margin:.35rem 0 0 1.1rem;color:var(--text)">' + factors.slice(0,3).map(f => {
                    const label = f.factor || f.label || f.name || f;
                    const detail = f.detail ? ` — ${esc(f.detail)}` : '';
                    const src = f.source ? ` <span style="opacity:.7">· ${esc(f.source)}</span>` : '';
                    return `<li>${esc(label)}${detail}${src}</li>`;
                }).join('') + '</ol>';
            }
            let certLine = '';
            if (cert.certificate_hash || data.prediction_id) {
                const hashShort = cert.certificate_hash
                    ? String(cert.certificate_hash).slice(0, 16) + '…'
                    : 'pending';
                certLine = `<div style="margin-top:.5rem;font-size:.8rem">Certificate <code>${esc(hashShort)}</code> · prediction_id <code>${esc(data.prediction_id || '—')}</code></div>`;
            }
            const whyTitle = factors.length
                ? `<div style="font-size:.78rem;color:var(--accent);margin-bottom:.35rem">${esc(whyBlock.grasp_line || 'Why (Top 3) — under five seconds')} · ${esc(latencyMs)}ms</div>`
                : '';
            whyEl.innerHTML =
                whyTitle +
                whyList +
                '<details style="margin-top:.65rem;border:1px solid var(--border,#2a2a35);border-radius:10px;padding:.65rem .85rem;background:rgba(0,0,0,.2)">' +
                '<summary style="cursor:pointer;color:var(--accent);font-weight:600">Evidence drawer · Certificate + scenarios</summary>' +
                scenHtml + certLine + '</details>';
        }


        function paintLandingVerdict(verdictEl, data, action) {
            const verdict = data.verdict || action;
            verdictEl.textContent = action;
            verdictEl.className = 'result-verdict';
            const v = String(verdict).toUpperCase();
            if (action === 'CONDITIONS MET' || v.includes('CONDITION')) verdictEl.classList.add('verdict-wait');
            else if (v.includes('SELL') || action === 'ABSTAIN') verdictEl.classList.add('verdict-sell');
            else verdictEl.classList.add('verdict-wait');
        }
        function paintLandingFreshness(data) {
            const freshChip = document.getElementById('oracleFreshnessLabel');
            const fresh = data.data_freshness || {};
            if (!freshChip) return;
            const state = String(fresh.state || fresh.status || '').toLowerCase();
            const stale = fresh.stale === true || state === 'stale';
            const knownFresh = state === 'fresh' || state === 'ok' || state === 'live';
            freshChip.textContent = stale
                ? (fresh.label || 'Stale — not live')
                : (fresh.label || (knownFresh ? 'Live' : 'Freshness unknown'));
            const wrap = document.getElementById('oracleFreshnessChip');
            if (!wrap) return;
            wrap.title = fresh.state ? `Freshness: ${fresh.state}` : 'Data freshness';
            wrap.style.opacity = stale ? '0.65' : '1';
        }
        function paintLandingProMeta(proMeta, data, mode) {
            if (mode === 'pro') {
                const truth = data.net_edge_truth || {};
                const half = data.opportunity_half_life || {};
                const conflict = data.dimension_conflict || {};
                let line = `Truth ${esc(truth.truth_score ?? '—')} · Half-life ${esc(half.remaining_seconds ?? '—')}s · Regime ${esc(data.market_regime || '—')}`;
                if (conflict.veto || conflict.abstain || (conflict.severity && conflict.severity !== 'none')) {
                    const vetoWord = conflict.veto ? 'WAIT' : 'Abstain';
                    const sevBit = conflict.severity ? ' (' + esc(conflict.severity) + ')' : '';
                    line += ` · Contradiction Veto: ${vetoWord}${sevBit}`;
                }
                if (data.prediction_id) line += ` · Proof #${esc(data.prediction_id)}`;
                proMeta.style.display = 'block';
                proMeta.innerHTML = line + (data.prediction_id
                    ? ` · <a href="/oracle-accuracy" style="color:var(--accent)">accuracy</a>`
                    : '');
                return;
            }
            if (data.prediction_id) {
                proMeta.style.display = 'block';
                proMeta.innerHTML = `Proof · prediction_id <code>${esc(data.prediction_id)}</code> · <a href="/oracle-accuracy" style="color:var(--accent)">Public accuracy</a>`;
            }
        }
        function paintLandingUpgrade(upgradeEl, data) {
            if (!data.upgrade_hint) return;
            const teaser = data.upgrade_hint.teaser || {};
            const teaserLine = [
                teaser.truth_score != null ? `Truth teaser ${esc(teaser.truth_score)}` : null,
                teaser.remaining_seconds != null ? `Half-life ~${esc(teaser.remaining_seconds)}s` : null,
                teaser.regime ? `Regime ${esc(teaser.regime)}` : null,
            ].filter(Boolean).join(' · ');
            upgradeEl.style.display = 'block';
            upgradeEl.innerHTML =
                `<div style="color:var(--text-muted);font-size:.85rem;margin-bottom:.5rem">${esc(data.upgrade_hint.message || '')}` +
                (teaserLine ? `<br>${teaserLine}` : '') +
                `</div><button type="button" class="btn-secondary" id="switchProBtn">Switch to Pro</button>`;
            document.getElementById('switchProBtn')?.addEventListener('click', () => {
                const sel = document.getElementById('landingUxMode');
                if (sel) sel.value = 'pro';
                consultOracle();
            });
        }
        function wireDisciplineMirror(disc, data, symbol, followAction) {
            disc.style.display = 'block';
            disc.innerHTML =
                `<div style="font-size:.85rem;color:var(--text-muted);margin-bottom:.4rem"><strong style="color:var(--text)">Discipline Mirror</strong> (private) — cure for Dashboard Tourism. Did you follow this model state? <a href="/discipline-mirror" class="landing-inline-link">Open my mirror</a> · <a href="/errors" class="landing-inline-link">See public misses</a></div>` +
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
                            system_action: followAction,
                            followed,
                            prediction_id: data.prediction_id,
                            opportunity_score: data.opportunity_score,
                        }),
                    });
                    document.getElementById('disciplineMsg').textContent = 'Saved privately — only you can see your Discipline Mirror.';
                } catch (error) { console.debug(error); document.getElementById('disciplineMsg').textContent = 'Could not save answer.'; }
            };
            document.getElementById('followedYes')?.addEventListener('click', () => sendFollow(true));
            document.getElementById('followedNo')?.addEventListener('click', () => sendFollow(false));
        }
        function paintLandingCompliance(data) {
            const foot = data.compliance_footer || {};
            const comp = document.getElementById('landingCompliance');
            if (!foot.disclaimer || !comp) return;
            comp.style.display = 'block';
            comp.innerHTML = `<strong>Anti-Hype</strong> · Source: ${esc(foot.data_source || '—')} · Trust: ${esc(foot.trust_basis || '—')}<br>${esc(foot.disclaimer)}`;
        }

        function tryOracleFree() {
            const oracleBlock = document.getElementById('oracle');
            if (oracleBlock) {
                oracleBlock.scrollIntoView({ behavior: 'smooth', block: 'start' });
                if (window.history && window.history.replaceState) {
                    window.history.replaceState(null, '', '#oracle');
                } else {
                    window.location.hash = 'oracle';
                }
            }
            consultOracle();
        }
        window.tryOracleFree = tryOracleFree;

        async function consultOracle() {
            const symbol = document.getElementById('symbolInput').value.toUpperCase();
            const mode = document.getElementById('landingUxMode').value || 'beginner';
            const lang = (window.BD_I18N && window.BD_I18N.lang) || document.documentElement.lang || 'en';
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
            oracleEl.textContent = i18nT('oracle.loading');
            proMeta.style.display = 'none';
            upgradeEl.style.display = 'none';
            const t0 = performance.now();
            
            try {
                const { response, data } = await fetchOraclePayload(symbol, mode, lang);
                const latencyMs = Math.round(performance.now() - t0);
                if (!data) {
                    oracleEl.textContent = i18nT('oracle.error');
                    verdictEl.textContent = 'WAIT';
                    verdictEl.className = 'result-verdict verdict-wait';
                    return;
                }
                if (!response.ok) {
                    const detail = data.detail || {};
                    const msg = detail.message || i18nT('ui.quota_exceeded');
                    oracleEl.textContent = msg;
                    if (detail.upgrade_url || detail.error === 'quota_exceeded') {
                        upgradeEl.style.display = 'block';
                        upgradeEl.innerHTML = `<a class="btn-primary" href="${esc(safeUrl(detail.upgrade_url) || '/create-checkout-session?tier=pro')}">Upgrade to Pro</a>`;
                    }
                    return;
                }

                const action = decideLandingAction(data);
                const cert = data.decision_certificate || {};
                const followAction = data.decision_action || data.verdict || action || 'WAIT';
                const paintSuccess = () => {
                    symbolEl.textContent = data.symbol || symbol;
                    scoreEl.textContent = data.opportunity_score ?? '--';
                    paintLandingVerdict(verdictEl, data, action);
                    oracleEl.textContent = fallbackDecisionSentence(data, symbol, action, mode);
                    paintLandingFreshness(data);
                    paintLandingUxHint(mode, data);
                    paintLandingProMeta(proMeta, data, mode);
                    paintLandingUpgrade(upgradeEl, data);
                    const certEl = document.getElementById('landingCert');
                    renderLandingCertificate(certEl, cert, data);
                    renderLandingWhy(oracleEl, data, cert, latencyMs);
                    wireDisciplineMirror(document.getElementById('landingDiscipline'), data, symbol, followAction);
                    paintLandingCompliance(data);
                    updateShareLinks(data);
                    syncLandingTrustPulseFromOracle(data, symbol);
                };
                if (typeof requestAnimationFrame === 'function') {
                    requestAnimationFrame(paintSuccess);
                } else {
                    paintSuccess();
                }
            } catch (error) { console.debug(error); oracleEl.textContent = i18nT('ui.oracle_unavailable'); }
        }

        const LANDING_AUDIENCE_LABEL = { retail: 'Prove', pro: 'Operate', whale: 'Desk', fund: 'Room' };

        function formatAudienceCta(aud, d) {
            const label = (d && d.lens_label) || LANDING_AUDIENCE_LABEL[aud] || 'Prove';
            const body = (d && (d.lens_promise || d.cta)) || '';
            if (body) return label + ' — ' + body;
            return 'Audience: ' + label;
        }

        function paintLandingUxHint(mode, data) {
            const hint = document.getElementById('landingUxHint');
            if (!hint) return;
            const resolved = (data && data.ux_mode) ? String(data.ux_mode) : (mode || 'beginner');
            const label = resolved === 'pro' ? 'Decision Pro' : 'Beginner';
            hint.textContent = 'Experience: ' + label;
            hint.style.display = 'block';
        }

        function onLandingUxModeChange() {
            const mode = document.getElementById('landingUxMode')?.value || 'beginner';
            localStorage.setItem('bd_ux_mode', mode);
            const hint = document.getElementById('landingUxHint');
            if (hint) {
                hint.textContent = 'Experience: ' + (mode === 'pro' ? 'Decision Pro' : 'Beginner') + ' — press Get Decision';
                hint.style.display = 'block';
            }
            loadLandingTrustPulse();
        }

        async function applyAudience() {
            const aud = document.getElementById('landingAudience')?.value || 'retail';
            const lensMap = { retail:'prove', pro:'operate', whale:'desk', fund:'room' };
            const cta = document.getElementById('audienceCta');
            localStorage.setItem('bd_audience', aud);
            localStorage.setItem('bd_lens', lensMap[aud] || 'prove');
            let d = null;
            try {
                const res = await fetch('/api/audience/entry?audience=' + encodeURIComponent(aud), {
                    headers: { Accept: 'application/json' },
                });
                const raw = await res.text();
                try {
                    d = raw && !raw.trim().startsWith('<') ? JSON.parse(raw) : null;
                } catch (error) { console.debug(error); d = null; }
                if (!res.ok || !d || typeof d !== 'object') {
                    if (cta) cta.textContent = formatAudienceCta(aud, null);
                    return;
                }
                if (cta) cta.textContent = formatAudienceCta(aud, d);
                const mode = document.getElementById('landingUxMode');
                if (mode && d.ux_mode_default) mode.value = d.ux_mode_default;
            } catch (error) {
                console.debug(error);
                if (cta) cta.textContent = formatAudienceCta(aud, null);
            }
        }
        window.applyAudience = applyAudience;
        window.consultOracle = consultOracle;
        window.onLandingUxModeChange = onLandingUxModeChange;
        
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
            } catch (error) { console.debug(error); msg.textContent = 'Something went wrong. Try again.';
                msg.style.color = 'var(--danger)';
                msg.style.display = 'block'; }
        }
        
        async function loadLandingAnalytics() {
            try {
                if (typeof window.bdOptionalAnalyticsAllowed === 'function' && !window.bdOptionalAnalyticsAllowed()) {
                    return;
                }
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
                // Stats intentionally below first-viewport budget — only fill if strip exists
                const set = (id, val) => {
                    const el = document.getElementById(id);
                    if (el) el.textContent = val;
                };
                set('landingViews', (analytics.landing_views || 0).toLocaleString());
                set('landingUsers', (users.registered_users || 0).toLocaleString());
                set('landingSubs', (users.paid_subscribers || analytics.subscriber_count || 0).toLocaleString());
                set('landingTelegram', (telegram.active_subscribers || users.telegram_free_subscribers || 0).toLocaleString());
                set('landingWaitlist', (analytics.waitlist_count || 0).toLocaleString());
            } catch (error) { console.debug(error); }
        }

        async function loadTelegramBotLink() {
            try {
                const res = await fetch('/api/telegram/free/status');
                const data = await res.json();
                const link = document.getElementById('telegramBotLink');
                if (!link) return;
                const username = (data.bot_username || '').replace('@', '');
                if (username) {
                    setAnchorHref(link, `https://t.me/${username}`);
                    link.textContent = `@${username} — Start Free`;
                }
            } catch (error) { console.debug(error); }
        }

        let landingPulse = null;
        let landingPulseEs = null;
        let landingPulseSymbol = 'BTC';

        function _landingPulseFactors(data) {
            const whyBlock = data.oqs_why || {};
            return whyBlock.top_3_factors
                || (data.explanation && data.explanation.top_3_factors)
                || data.top_3_factors
                || [];
        }

        function syncLandingTrustPulseFromOracle(data, symbol) {
            if (!data) return;
            const sym = String(data.symbol || symbol || 'BTC').trim().toUpperCase() || 'BTC';
            landingPulseSymbol = sym;
            const action = decideLandingAction(data);
            const cert = data.decision_certificate || {};
            const fresh = data.data_freshness || {};
            const pulseView = {
                symbol: sym,
                action: action,
                price: data.price,
                change_24h: data.change_24h != null ? data.change_24h : data.change_24h_pct,
                sentence: fallbackDecisionSentence(data, sym, action),
                why: { factors: _landingPulseFactors(data) },
                freshness: fresh,
                proof: {
                    ...(landingPulse && landingPulse.proof ? landingPulse.proof : {}),
                    certificate_hash: cert.certificate_hash,
                    prediction_id: data.prediction_id,
                },
                ledger: landingPulse && landingPulse.ledger ? landingPulse.ledger : {},
            };
            renderLandingPulse(pulseView);
            startLandingPulseStream(sym);
        }

        function _lpPriceBit(p) {
            const price = p.price != null
                ? ('$' + Number(p.price).toLocaleString(undefined, { maximumFractionDigits: 2 }))
                : '';
            const ch = p.change_24h;
            if (ch == null) return price;
            const sign = ch >= 0 ? '+' : '';
            return `${price} · ${sign}${Number(ch).toFixed(2)}%`;
        }

        function _lpRenderWhy(factors) {
            const why = document.getElementById('lpWhy');
            if (!why) return;
            why.innerHTML = (factors || []).slice(0, 3).map((f, i) => {
                const detail = f.detail ? (' — ' + esc(f.detail)) : '';
                return '<div><strong>' + (i + 1) + '. ' + esc(f.factor || f) + '</strong>' + detail + '</div>';
            }).join('') || '';
        }

        function _lpProofLedgerHref(proof) {
            const raw = proof.permalink || proof.verify_url || '';
            if (typeof raw === 'string' && raw.startsWith('http')) {
                try {
                    const u = new URL(raw);
                    return u.pathname + u.search + u.hash;
                } catch (error) {
                    console.debug(error);
                }
            }
            const rel = safeUrl(raw) || '/oracle-accuracy';
            if (proof.certificate_hash && rel.indexOf('cert=') < 0) {
                const sep = rel.indexOf('?') >= 0 ? '&' : '?';
                return rel + sep + 'cert=' + encodeURIComponent(String(proof.certificate_hash).slice(0, 16));
            }
            return rel;
        }

        function _lpCertHash(p) {
            const proof = (p && p.proof) || {};
            const cert = (p && p.decision_certificate) || {};
            return proof.certificate_hash || cert.certificate_hash || '';
        }

        function _lpPulseHasCertificate(p) {
            return Boolean(_lpCertHash(p));
        }

        function openLandingPulseProof() {
            const p = landingPulse || {};
            const proof = p.proof || {};
            const drawer = document.getElementById('lpProofDrawer');
            const toast = document.getElementById('lpProofCopyMsg');
            if (toast) toast.hidden = true;
            if (!drawer) return;
            const hash = _lpCertHash(p);
            if (!hash) {
                drawer.hidden = false;
                drawer.innerHTML =
                    '<p style="margin:0;color:var(--text-muted)">No Decision Certificate for this pulse yet. ' +
                    'Use <strong>Get Decision</strong> below to generate signed proof.</p>';
                return;
            }
            drawer.hidden = false;
            const data = { symbol: p.symbol || 'BTC', prediction_id: proof.prediction_id || cert.prediction_id };
            renderLandingPulseProofDrawer(drawer, cert, data, p);
        }

        function renderLandingPulseProofDrawer(drawerEl, cert, data, pulse) {
            const proof = (pulse && pulse.proof) || {};
            const ledgerHref = esc(_lpProofLedgerHref(proof));
            const hashLabel = cert.certificate_hash ? String(cert.certificate_hash).slice(0, 16) + '…' : 'pending';
            const copyBtn = cert.share_text
                ? '<button type="button" class="btn-secondary" id="lpDrawerCopyCert">Copy certificate text</button>'
                : '';
            drawerEl.innerHTML =
                '<p style="margin:0 0 .5rem"><strong>Decision Certificate</strong> · Trust Pulse</p>' +
                '<p style="margin:0 0 .5rem;color:var(--text-muted)"><code>' + esc(hashLabel) + '</code></p>' +
                '<div style="display:flex;flex-wrap:wrap;gap:.35rem;margin-bottom:.5rem">' +
                copyBtn +
                '<a class="btn-secondary" href="' + ledgerHref + '">Open proof on ledger</a>' +
                '<button type="button" class="btn-secondary" id="lpDrawerClose">Close</button>' +
                '</div>';
            document.getElementById('lpDrawerCopyCert')?.addEventListener('click', () => {
                navigator.clipboard.writeText(cert.share_text || '').then(() => {
                    const msg = document.getElementById('lpProofCopyMsg');
                    if (msg) {
                        msg.textContent = 'Certificate text copied.';
                        msg.hidden = false;
                    }
                }).catch(() => {});
            });
            document.getElementById('lpDrawerClose')?.addEventListener('click', () => {
                drawerEl.hidden = true;
            });
        }

        function copyLandingPulseCertHash() {
            const hash = _lpCertHash(landingPulse);
            const msg = document.getElementById('lpProofCopyMsg');
            if (!hash) {
                if (msg) {
                    msg.textContent = 'No certificate hash yet — use Get Decision below.';
                    msg.hidden = false;
                }
                return;
            }
            const done = () => {
                if (msg) {
                    msg.textContent = 'Certificate hash copied.';
                    msg.hidden = false;
                }
            };
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(String(hash)).then(done).catch(() => {
                    openLandingPulseProof();
                });
            } else {
                openLandingPulseProof();
            }
        }

        let lpProofClickWired = false;
        function wireLandingPulseProofClicks() {
            if (lpProofClickWired) return;
            const box = document.getElementById('lpProof');
            if (!box) return;
            lpProofClickWired = true;
            box.addEventListener('click', (e) => {
                if (!e.target.closest('#lpProof')) return;
                if (e.target.closest('[data-lp-proof-open]')) {
                    e.preventDefault();
                    e.stopPropagation();
                    openLandingPulseProof();
                    return;
                }
                if (e.target.closest('[data-lp-copy-hash]')) {
                    e.preventDefault();
                    e.stopPropagation();
                    copyLandingPulseCertHash();
                }
            });
        }

        /** Sole writer for #lpProof — ledger + Free Proof drawer + cert hash only (no share/X chips). */
        function _lpRenderProof(p) {
            const box = document.getElementById('lpProof');
            if (!box) return;
            wireLandingPulseProofClicks();
            const hash = _lpCertHash(p);
            const hasCert = Boolean(hash);
            const bits = [
                '<a class="bd-chip ok" href="/oracle-accuracy">Verified on Ledger</a>',
            ];
            if (hasCert) {
                bits.push(
                    '<button type="button" class="bd-chip bd-chip-btn ok" data-lp-proof-open="1">Free Proof</button>'
                );
                const short = esc(String(hash).slice(0, 10));
                bits.push(
                    `<button type="button" class="bd-chip bd-chip-btn" data-lp-copy-hash="1" title="Copy certificate hash">cert ${short}…</button>`
                );
            } else {
                bits.push(
                    '<span class="bd-chip bd-chip-muted">Free Proof — certificate pending</span>'
                );
            }
            box.innerHTML = bits.join('');
            box.querySelectorAll('a[href*="twitter.com"], a[href*="x.com"]').forEach((node) => node.remove());
            const drawer = document.getElementById('lpProofDrawer');
            if (drawer && !hasCert) drawer.hidden = true;
        }

        function renderLandingPulse(p) {
            if (!p) return;
            landingPulse = p;
            const act = window.BDPublicDecision?.mapPublicDecisionAction(p.action || p.verdict) || p.action || 'WAIT';
            const actionEl = document.getElementById('lpAction');
            if (actionEl) {
                actionEl.textContent = act;
                const cssToken = act === 'CONDITIONS MET' ? 'WAIT' : String(act).replace(/\s+/g, '_');
                actionEl.className = 'tp-mini-action bd-tp-action ' + cssToken;
            }
            const sym = document.getElementById('lpSym');
            if (sym) sym.textContent = `${p.symbol || 'BTC'} ${_lpPriceBit(p)}`;
            const sent = document.getElementById('lpSentence');
            if (sent) sent.textContent = p.sentence || 'One clear Act / Wait — reviewable.';
            _lpRenderWhy((p.why && p.why.factors) || []);
            const fresh = p.freshness || {};
            const dot = document.getElementById('lpDot');
            if (dot) dot.className = 'tp-mini-dot' + (fresh.stale ? ' stale' : '');
            const fl = document.getElementById('lpFresh');
            if (fl) {
                const state = String(fresh.state || fresh.status || '').toLowerCase();
                const stale = fresh.stale === true || state === 'stale';
                const knownFresh = state === 'fresh' || state === 'ok' || state === 'live';
                fl.textContent = stale
                    ? (fresh.label || 'Stale — not live')
                    : (fresh.label || (knownFresh ? 'Live' : 'Freshness unknown'));
            }
            _lpRenderProof(p);
        }

        async function fetchLandingTrustPulse(symbol, mode, lang) {
            const sym = String(symbol || 'BTC').trim().toUpperCase() || 'BTC';
            landingPulseSymbol = sym;
            try {
                const q = new URLSearchParams({
                    symbol: sym,
                    ux_mode: mode || 'beginner',
                    lang: lang || 'en',
                });
                const res = await fetch('/api/trust-pulse?' + q.toString());
                if (!res.ok) return;
                renderLandingPulse(await res.json());
                startLandingPulseStream(sym);
            } catch (error) { console.debug(error); }
        }

        async function loadLandingTrustPulse() {
            const symbol = (document.getElementById('symbolInput')?.value || 'BTC').toUpperCase();
            const mode = document.getElementById('landingUxMode')?.value || 'beginner';
            const lang = currentLang();
            await fetchLandingTrustPulse(symbol, mode, lang);
        }

        function startLandingPulseStream(symbol) {
            const sym = String(symbol || landingPulseSymbol || 'BTC').trim().toUpperCase() || 'BTC';
            landingPulseSymbol = sym;
            try {
                if (landingPulseEs) landingPulseEs.close();
                landingPulseEs = new EventSource('/api/trust-pulse/stream?symbol=' + encodeURIComponent(sym));
                landingPulseEs.onmessage = (ev) => {
                    try {
                        const d = JSON.parse(ev.data);
                        if (d.pulse && String(d.pulse.symbol || '').toUpperCase() === landingPulseSymbol) {
                            renderLandingPulse(d.pulse);
                        }
                    } catch (error) { console.debug(error); }
                };
            } catch (error) { console.debug(error); }
        }

        function shareLandingPulseProof() {
            const btn = document.getElementById('lpShareBtn');
            if (!btn) return;
            btn.classList.remove('bd-motion-share');
            btn.dataset.reflow = String(btn.offsetWidth);
            btn.classList.add('bd-motion-share');
            const proof = (landingPulse && landingPulse.proof) || {};
            const text = proof.share_text || 'BLACKDARK Trust Pulse — verify /oracle-accuracy';
            if (navigator.clipboard) navigator.clipboard.writeText(text).catch(() => {});
            if (proof.share_urls && proof.share_urls.x) {
                openWindow(proof.share_urls.x);
            }
        }
        document.getElementById('lpShareBtn')?.addEventListener('click', shareLandingPulseProof);


        async function loadBillingReadyLine() {
            const el = document.getElementById('billingReadyLine');
            if (!el) return;
            try {
                const res = await fetch('/api/billing/payments');
                const d = await res.json();
                const ops = d.ops_readiness || {};
                const provider = d.active_provider || 'none';
                if (ops.launch_ready || d.billing_configured) {
                    el.textContent = 'USD payments ready · ' + provider + ' hosted checkout · Decision Pro $29 · Decision Desk $49 · Institutional from $3,000 → open';
                } else {
                    el.textContent = 'USD payment rails live in product · finish Lemon/Stripe KYC + checkout URLs for live charges. Proof Pass ($0) and Sign up work now. Profile → Plan & billing.';
                    el.style.color = 'var(--text-muted)';
                }
            } catch (error) { console.debug(error); el.textContent = 'Payment status: see /api/billing/payments · Profile & Billing for checkout.';
                el.style.color = 'var(--text-muted)'; }
        }

        async function wireInstitutionalInquiry() {
            const form = document.getElementById('institutionalInquiryForm');
            if (!form) return;
            form.addEventListener('submit', async (ev) => {
                ev.preventDefault();
                const fd = new FormData(form);
                const payload = Object.fromEntries(fd.entries());
                const msg = document.getElementById('institutionalInquiryMsg');
                try {
                    const res = await fetch('/api/billing/institutional-inquiry', {
                        method: 'POST', headers: {'Content-Type':'application/json'},
                        body: JSON.stringify(payload)
                    });
                    const d = await res.json();
                    msg.textContent = res.ok ? (d.message || 'Received') : (d.detail || 'Failed');
                    msg.style.color = res.ok ? 'var(--success)' : 'var(--danger)';
                    if (res.ok) form.reset();
                } catch (error) { console.debug(error); msg.textContent = 'Inquiry unavailable right now';
                    msg.style.color = 'var(--danger)'; }
            });
        }
        window.addEventListener('load', async () => {
            updateShareLinks(null);
            scheduleNonCriticalLandingWork(() => {
                loadLandingAnalytics();
                loadTelegramBotLink();
                loadBillingReadyLine();
            });
            wireInstitutionalInquiry();
            await applyAudience();
            await loadLandingTrustPulse();
            setTimeout(consultOracle, 500);
            if ('serviceWorker' in navigator) {
                navigator.serviceWorker.register('/sw.js').catch((error) => { console.debug(error); });
            }
        });
    