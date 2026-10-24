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

        function applyLandingPulseSSR() {
            const el = document.getElementById('landing-pulse-ssr');
            if (!el) return false;
            try {
                const p = JSON.parse(el.textContent || '{}');
                if (p && (p.symbol || p.action)) {
                    renderLandingPulse(p);
                    landingPulseSymbol = String(p.symbol || 'BTC').trim().toUpperCase() || 'BTC';
                    return true;
                }
            } catch (error) { console.debug(error); }
            return false;
        }

        const BDDom = window.BDDomSafe || {};
        const escapeHtml = BDDom.escapeHtml || function (v) { return String(v ?? ''); };
        const esc = BDDom.esc || escapeHtml;
        const safeUrl = BDDom.safeUrl || function () { return ''; };
        const assignLocationHref = typeof BDDom.assignLocationHref === 'function'
            ? BDDom.assignLocationHref
            : function (value) {
                const raw = String(value ?? '').trim();
                if (raw && /^https?:\/\//i.test(raw)) window.location.href = raw;
            };
        const openWindow = typeof BDDom.openWindow === 'function'
            ? BDDom.openWindow
            : function (value) {
                const raw = String(value ?? '').trim();
                if (raw && /^https?:\/\//i.test(raw)) window.open(raw, '_blank', 'noopener');
            };
        function setAnchorHref(el, value) {
            if (!el) return;
            if (typeof BDDom.setAnchorHref === 'function') {
                BDDom.setAnchorHref(el, value);
                return;
            }
            if (typeof window.setAnchorHref === 'function') {
                window.setAnchorHref(el, value);
                return;
            }
            const raw = String(value ?? '').trim();
            if (raw && (/^https?:\/\//i.test(raw) || (raw.startsWith('/') && !raw.startsWith('//')))) {
                el.href = raw;
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
                    text: i18nT('pulse.share_default') || 'BLACKDARK Trust Pulse — one Act/Wait decision you can verify',
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

        function setLandingOraclePresentationLayout(mode) {
            const header = document.querySelector('#oracleResult .result-header');
            const verdictWrap = document.getElementById('resultVerdict')?.parentElement;
            const share = document.getElementById('oracleShare');
            const metrics = document.getElementById('landingOracleMetrics');
            const full = mode === 'full';
            const summary = full || mode === 'summary' || mode === 'partial';
            if (header) header.style.display = summary ? '' : 'none';
            if (verdictWrap) verdictWrap.style.display = summary ? '' : 'none';
            if (share) share.style.display = full ? '' : 'none';
            if (metrics && mode === 'down') {
                metrics.hidden = true;
                metrics.innerHTML = '';
            }
        }

        function updateShareLinks(result) {
            window.lastOracleResult = result;
            const oracleFull = !!(result && landingOracleIsFull(result));
            if (result && landingOracleIsAgeOnly(result)) {
                setLandingOraclePresentationLayout('partial');
            } else {
                setLandingOraclePresentationLayout(oracleFull ? 'full' : 'down');
            }
            if (!oracleFull) return;
            const { url, text } = buildSharePayload(result);
            const full = `${text}\n${url}`;

            const xBtn = document.getElementById('shareXBtn');
            const fbBtn = document.getElementById('shareFacebookBtn');
            const waBtn = document.getElementById('shareWhatsappBtn');
            const tgBtn = document.getElementById('shareTelegramBtn');
            const rdBtn = document.getElementById('shareRedditBtn');

            try {
                if (xBtn) setAnchorHref(xBtn, `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`);
                if (fbBtn) setAnchorHref(fbBtn, `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}&quote=${encodeURIComponent(text)}`);
                if (waBtn) setAnchorHref(waBtn, `https://wa.me/?text=${encodeURIComponent(full)}`);
                if (tgBtn) setAnchorHref(tgBtn, `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text)}`);
                if (rdBtn) setAnchorHref(rdBtn, `https://www.reddit.com/submit?url=${encodeURIComponent(url)}&title=${encodeURIComponent(text)}`);
            } catch (shareError) { console.debug(shareError); }

            const igBtn = document.getElementById('shareInstagramBtn');
            if (igBtn) {
                igBtn.onclick = function(e) {
                    e.preventDefault();
                    navigator.clipboard.writeText(full).then(() => {
                        igBtn.textContent = i18nT('oracle.share.copied');
                        setTimeout(() => { igBtn.textContent = i18nT('oracle.share.instagram'); }, 2000);
                    });
                };
            }

            const copyBtn = document.getElementById('shareCopyBtn');
            if (copyBtn) {
                copyBtn.onclick = function(e) {
                    e.preventDefault();
                    navigator.clipboard.writeText(full).then(() => {
                        copyBtn.textContent = i18nT('oracle.share.copied');
                        copyBtn.classList.add('copied');
                        setTimeout(() => {
                            copyBtn.textContent = i18nT('oracle.share.copy');
                            copyBtn.classList.remove('copied');
                        }, 2000);
                    });
                };
            }
        }


        function landingOracleHasDecision(data) {
            if (!data || typeof data !== 'object') return false;
            return Boolean(
                data.decision_sentence
                || data.oracle
                || data.decision_action
                || data.verdict
            );
        }

        function setLandingOracleFailReason(reason) {
            const el = document.getElementById('landingOracleFailReason');
            if (!el) return;
            if (!reason) {
                el.textContent = '';
                el.style.display = 'none';
                return;
            }
            el.textContent = reason;
            el.style.display = 'block';
        }

        async function fetchOraclePayload(symbol, mode, lang) {
            // Landing always uses /quick first — full /oracle/{sym} requires terms ack and returns no decision fields.
            const preferQuick = true;
            const primary = preferQuick
                ? `/oracle/${encodeURIComponent(symbol)}/quick?ux_mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`
                : `/oracle/${encodeURIComponent(symbol)}?ux_mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`;
            const fallback = preferQuick
                ? `/oracle/${encodeURIComponent(symbol)}?ux_mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`
                : `/oracle/${encodeURIComponent(symbol)}/quick?ux_mode=${encodeURIComponent(mode)}&lang=${encodeURIComponent(lang)}`;

            let networkFailure = false;

            async function loadOracle(url) {
                try {
                    const fetchOracle = (window.BDOracleFetchGate && window.BDOracleFetchGate.fetch)
                        ? window.BDOracleFetchGate.fetch.bind(window.BDOracleFetchGate)
                        : fetch;
                    const response = await fetchOracle(url, { headers: { Accept: 'application/json' } });
                    const rawText = await response.text();
                    let data = null;
                    try {
                        if (rawText && !rawText.trim().startsWith('<') && !rawText.includes('Internal Server Error')) {
                            data = JSON.parse(rawText);
                        }
                    } catch (error) { console.debug(error); }
                    return { response, data, networkFailure: false };
                } catch (error) {
                    console.debug(error);
                    networkFailure = true;
                    return { response: null, data: null, networkFailure: true };
                }
            }

            const first = await loadOracle(primary);
            if (first.response && first.response.status === 429) {
                return { ...first, networkFailure: false };
            }
            if (landingOracleHasDecision(first.data)) {
                return { ...first, networkFailure: false };
            }
            const second = await loadOracle(fallback);
            if (second.response && second.response.status === 429) {
                return { ...second, networkFailure: false };
            }
            if (landingOracleHasDecision(second.data)) {
                return { ...second, networkFailure: false };
            }
            const picked = first.response && first.response.ok ? first : second;
            return {
                ...picked,
                networkFailure: networkFailure && !landingOracleHasDecision(picked.data),
            };
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
        function fallbackDecisionSentence(data, symbol, action) {
            let sentence = data.decision_sentence || data.conditions_met_review || data.narrative || data.oracle || data.action_line || '';
            if (sentence && !/meditat|consulting the oracle/i.test(sentence)) return sentence;
            if (typeof data.action === 'string' && data.action.length > 12 && !/\bBuy\b/i.test(data.action)) return data.action;
            const review = i18nT('pulse.conditions_met_review');
            const sym = data.symbol || symbol;
            if (action === 'CONDITIONS MET') {
                return i18nT('pulse.model_state_conditions', { symbol: sym, review: review });
            }
            return i18nT('pulse.model_state', { action: action, symbol: sym });
        }
        function landingOracleFactors(data) {
            if (!data) return [];
            const whyBlock = data.oqs_why || {};
            return whyBlock.top_3_factors
                || (data.explanation && data.explanation.top_3_factors)
                || data.top_3_factors
                || [];
        }

        function landingChange24h(data) {
            if (!data) return null;
            if (data.change_24h != null) return data.change_24h;
            if (data.change_24h_pct != null) return data.change_24h_pct;
            return null;
        }

        function landingPriceBit(data) {
            const price = data && data.price != null
                ? ('$' + Number(data.price).toLocaleString(undefined, { maximumFractionDigits: 2 }))
                : '—';
            const ch = landingChange24h(data);
            if (ch == null) return price;
            const sign = Number(ch) >= 0 ? '+' : '';
            return `${price} · ${sign}${Number(ch).toFixed(2)}%`;
        }

        function landingMetricValue(raw) {
            if (raw === null || raw === undefined || raw === '') return '—';
            return String(raw);
        }

        function paintLandingOracleMetrics(data) {
            const row = document.getElementById('landingOracleMetrics');
            if (!row) return;
            if (!data || !landingOracleHasDecision(data)) {
                row.hidden = true;
                row.innerHTML = '';
                return;
            }
            const truth = (data.net_edge_truth && data.net_edge_truth.truth_score != null)
                ? data.net_edge_truth.truth_score
                : null;
            const half = data.opportunity_half_life || {};
            const halfSec = half.remaining_seconds != null ? half.remaining_seconds : null;
            const regime = data.market_regime != null && String(data.market_regime).trim()
                ? data.market_regime
                : null;
            const sig = data.signal_id != null && String(data.signal_id).trim()
                ? String(data.signal_id).slice(0, 10)
                : null;
            const conf = data.confidence != null ? `${landingMetricValue(data.confidence)}%` : '—';
            const cells = [
                [landingMetricValue(data.opportunity_score), i18nT('ui.score')],
                [conf, i18nT('ui.confidence')],
                [landingMetricValue(truth), i18nT('ui.truth')],
                [halfSec != null ? `${halfSec}s` : '—', i18nT('ui.half_life')],
                [landingMetricValue(regime), i18nT('ui.regime')],
                [landingMetricValue(sig), i18nT('ui.signal')],
            ];
            row.innerHTML = cells.map(([val, label]) =>
                `<div class="landing-oracle-metric"><strong>${esc(val)}</strong><span>${esc(label)}</span></div>`
            ).join('');
            row.hidden = false;
        }

        function paintLandingOracleHeader(symbolEl, scoreEl, verdictEl, data, symbol, action) {
            const sym = String((data && data.symbol) || symbol || 'BTC').trim().toUpperCase() || 'BTC';
            if (symbolEl) symbolEl.textContent = `${sym} · ${landingPriceBit(data || {})}`;
            if (scoreEl) {
                scoreEl.textContent = data && data.opportunity_score != null
                    ? String(data.opportunity_score)
                    : '—';
            }
            if (verdictEl && data) paintLandingVerdict(verdictEl, data, action);
        }
        function landingOracleFreshnessKnown(data) {
            if (!data) return false;
            const fresh = data.data_freshness || {};
            const state = String(fresh.state || fresh.status || '').toLowerCase();
            if (state === 'unknown') return false;
            return fresh.freshness_ms != null || fresh.age_sec != null || fresh.age_seconds != null
                || state === 'fresh' || state === 'ok' || state === 'live' || state === 'stale';
        }
        function landingOracleIsFull(data) {
            if (!landingOracleHasDecision(data)) return false;
            if (!landingOracleFreshnessKnown(data)) return false;
            return landingOracleFactors(data).length > 0;
        }
        function landingOracleIsAgeOnly(data) {
            if (!landingOracleHasDecision(data)) return false;
            if (!landingOracleFreshnessKnown(data)) return false;
            return landingOracleFactors(data).length === 0;
        }
        function landingOracleIsLive(data) {
            return landingOracleIsFull(data);
        }
        function renderLandingCertificate(certEl, cert, data) {
            if (!landingOracleIsLive(data) || !(cert.certificate_hash || data.prediction_id)) {
                certEl.style.display = 'none';
                certEl.innerHTML = '';
                return;
            }
            certEl.style.display = 'block';
            const hashLabel = cert.certificate_hash ? String(cert.certificate_hash).slice(0,16)+'…' : i18nT('ui.pending');
            const copyBtn = cert.share_text ? `<button type="button" class="btn-secondary" id="copyCertBtn">${esc(i18nT('ui.copy_certificate'))}</button>` : '';
            const txtBtn = cert.export_text ? `<button type="button" class="btn-secondary" id="dlCertTxtBtn">${esc(i18nT('ui.download_txt'))}</button>` : '';
            const xHref = safeUrl(cert.share_urls && cert.share_urls.x);
            const tgHref = safeUrl(cert.share_urls && cert.share_urls.telegram);
            const xBtn = xHref ? `<a class="btn-secondary" id="certShareX" href="${xHref}" target="_blank" rel="noopener">${esc(i18nT('ui.share_x'))}</a>` : '';
            const tgBtn = tgHref ? `<a class="btn-secondary" id="certShareTg" href="${tgHref}" target="_blank" rel="noopener">${esc(i18nT('ui.share_tg'))}</a>` : '';
            certEl.innerHTML =
                `${esc(i18nT('ui.decision_certificate'))} · <code>${esc(hashLabel)}</code>` +
                `<div style="margin-top:.35rem;display:flex;flex-wrap:wrap;gap:.35rem">` +
                copyBtn +
                `<button type="button" class="btn-secondary" id="dlCertBtn">${esc(i18nT('ui.download_json'))}</button>` +
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
        function renderLandingWhy(oracleEl, data, cert) {
            let whyEl = document.getElementById('landingWhy');
            if (!whyEl) {
                whyEl = document.createElement('div');
                whyEl.id = 'landingWhy';
                whyEl.style.cssText = 'margin-top:.75rem;font-size:.85rem;color:var(--text-muted);text-align:left';
                oracleEl.parentNode.insertBefore(whyEl, oracleEl.nextSibling);
            }
            if (!landingOracleIsFull(data)) {
                whyEl.innerHTML = '';
                whyEl.style.display = 'none';
                return;
            }
            whyEl.style.display = '';
            const whyBlock = data.oqs_why || {};
            const factors = whyBlock.top_3_factors
                || (data.explanation && data.explanation.top_3_factors)
                || data.top_3_factors
                || [];
            const scen = (data.scenarios && data.scenarios.scenarios) || {};
            let scenHtml = '';
            if (scen.bull || scen.base || scen.bear) {
                const bits = ['bull','base','bear'].map(k => {
                    const s = scen[k] || {};
                    const pct = s.probability_pct != null ? s.probability_pct+'%' : '—';
                    return `${esc(s.label||k)} ${esc(pct)}`;
                }).join(' · ');
                const disc = (data.scenarios && data.scenarios.disclaimer) || '';
                scenHtml = `<div style="margin-top:.65rem"><strong style="color:var(--text)">${esc(i18nT('ui.scenarios_title'))}</strong> · ${bits}<div style="font-size:.75rem;margin-top:.25rem;opacity:.8">${esc(disc)}</div></div>`;
            }
            let whyList = '';
            if (factors.length) {
                whyList = '<ol style="margin:.35rem 0 0 1.1rem;color:var(--text)">' + factors.slice(0,3).map(f => {
                    const label = f.factor || f.label || f.name || f;
                    const detail = f.detail ? ` — ${esc(f.detail)}` : '';
                    const src = f.source ? ` <span style="opacity:.7">· ${esc(f.source)}</span>` : '';
                    return `<li>${esc(label)}${detail}${src}</li>`;
                }).join('') + '</ol>';
            }
            let certLine = '';
            if (cert && cert.certificate_hash) {
                const hashShort = String(cert.certificate_hash).slice(0, 16) + '…';
                certLine = `<div style="margin-top:.5rem;font-size:.8rem">${esc(i18nT('ui.certificate_label'))} <code>${esc(hashShort)}</code> · ${esc(i18nT('ui.prediction_id'))} <code>${esc(data.prediction_id || '—')}</code></div>`;
            }
            const whyTitle = factors.length
                ? `<div style="font-size:.78rem;color:var(--accent);margin-bottom:.35rem">${esc(whyBlock.grasp_line || i18nT('ui.why_top3'))}</div>`
                : '';
            whyEl.innerHTML =
                whyTitle +
                whyList +
                '<details style="margin-top:.65rem;border:1px solid var(--border,#2a2a35);border-radius:10px;padding:.65rem .85rem;background:rgba(0,0,0,.2)">' +
                '<summary style="cursor:pointer;color:var(--accent);font-weight:600">' + esc(i18nT('ui.evidence_drawer')) + '</summary>' +
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
            const wrap = document.getElementById('oracleFreshnessChip');
            const state = String(fresh.state || fresh.status || '').toLowerCase();
            if (state === 'unknown') {
                freshChip.textContent = '';
                if (wrap) wrap.style.display = 'none';
                return;
            }
            const stale = fresh.stale === true || state === 'stale';
            const knownFresh = state === 'fresh' || state === 'ok' || state === 'live';
            freshChip.textContent = stale
                ? (fresh.label || 'Stale — not live')
                : (fresh.label || (knownFresh ? 'Live' : ''));
            if (!freshChip.textContent) {
                if (wrap) wrap.style.display = 'none';
                return;
            }
            if (!wrap) return;
            wrap.style.display = '';
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
                    ? ` · <a href="/oracle-accuracy" class="landing-inline-link">accuracy</a>`
                    : '');
                return;
            }
            if (data.prediction_id) {
                proMeta.style.display = 'block';
                proMeta.innerHTML = `Proof · prediction_id <code>${esc(data.prediction_id)}</code> · <a href="/oracle-accuracy" class="landing-inline-link">Public accuracy</a>`;
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
            if (!disc) return;
            if (!landingOracleIsLive(data)) {
                disc.style.display = 'none';
                disc.innerHTML = '';
                return;
            }
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

        function clearLandingOracleChrome() {
            setLandingOraclePresentationLayout('down');
            const scoreEl = document.getElementById('resultScore');
            const verdictEl = document.getElementById('resultVerdict');
            const symbolEl = document.getElementById('resultSymbol');
            if (scoreEl) scoreEl.textContent = '';
            if (verdictEl) {
                verdictEl.textContent = '';
                verdictEl.className = 'result-verdict';
            }
            if (symbolEl) symbolEl.textContent = '';
            const freshChip = document.getElementById('oracleFreshnessLabel');
            const freshWrap = document.getElementById('oracleFreshnessChip');
            if (freshChip) freshChip.textContent = '';
            if (freshWrap) freshWrap.style.display = 'none';
            const certEl = document.getElementById('landingCert');
            if (certEl) {
                certEl.style.display = 'none';
                certEl.innerHTML = '';
            }
            const metricsRow = document.getElementById('landingOracleMetrics');
            if (metricsRow) {
                metricsRow.hidden = true;
                metricsRow.innerHTML = '';
            }
            const disc = document.getElementById('landingDiscipline');
            if (disc) {
                disc.style.display = 'none';
                disc.innerHTML = '';
            }
            const whyEl = document.getElementById('landingWhy');
            if (whyEl) {
                whyEl.innerHTML = '';
                whyEl.style.display = 'none';
            }
        }

        function landingSymbolValue() {
            return (document.getElementById('symbol')?.value || 'BTC').trim().toUpperCase() || 'BTC';
        }

        function setSymbol(symbol) {
            const value = String(symbol || '').trim().toUpperCase();
            if (!value) return;
            const sel = document.getElementById('symbol');
            if (sel) sel.value = value;
        }

        let consultOracleInflight = null;
        let landingOracleBootComplete = false;

        async function consultOracle(opts) {
            const silent = !!(opts && opts.silent);
            if (!landingOracleBootComplete && silent) return;
            if (consultOracleInflight) return consultOracleInflight;
            const symbol = landingSymbolValue();
            const mode = document.getElementById('landingUxMode').value || 'beginner';
            const lang = (window.BD_I18N && window.BD_I18N.lang) || document.documentElement.lang || 'en';
            const resultDiv = document.getElementById('oracleResult');
            if (!resultDiv) return;
            resultDiv.classList.add('active');
            await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
            const symbolEl = document.getElementById('resultSymbol');
            const scoreEl = document.getElementById('resultScore');
            const verdictEl = document.getElementById('resultVerdict');
            const oracleEl = document.getElementById('resultOracle');
            const proMeta = document.getElementById('landingProMeta');
            const upgradeEl = document.getElementById('landingUpgrade');
            
            localStorage.setItem('bd_ux_mode', mode);
            localStorage.setItem('bd_lang', lang);
            if (!silent) oracleEl.textContent = i18nT('oracle.loading');
            setLandingOracleFailReason('');
            setLandingOraclePresentationLayout('down');
            proMeta.style.display = 'none';
            upgradeEl.style.display = 'none';
            let oracleDecisionShown = false;

            consultOracleInflight = (async () => {
            try {
                const { response, data, networkFailure } = await fetchOraclePayload(symbol, mode, lang);
                if (!landingOracleHasDecision(data)) {
                    clearLandingOracleChrome();
                    const failReason = networkFailure
                        ? 'Network failure.'
                        : 'Response had no decision.';
                    setLandingOracleFailReason(failReason);
                    if (data && response && !response.ok) {
                        const detail = data.detail || {};
                        const msg = detail.message || i18nT('oracle.error');
                        oracleEl.textContent = msg;
                        if (detail.upgrade_url || detail.error === 'quota_exceeded') {
                            upgradeEl.style.display = 'block';
                            upgradeEl.innerHTML = `<a class="btn-primary" href="${esc(safeUrl(detail.upgrade_url) || '/create-checkout-session?tier=pro')}">Upgrade to Pro</a>`;
                        }
                    } else {
                        const offline = window.BDOracleWorkspace && window.BDOracleWorkspace.getOfflinePayload(symbol);
                        if (offline) {
                            const action = decideLandingAction(offline);
                            oracleEl.textContent = fallbackDecisionSentence(offline, symbol, action) + ' (Offline · last known)';
                            oracleDecisionShown = true;
                            return;
                        }
                        oracleEl.textContent = i18nT('oracle.error');
                    }
                    return;
                }

                setLandingOracleFailReason('');
                const full = landingOracleIsFull(data);
                const ageOnly = landingOracleIsAgeOnly(data);
                const action = decideLandingAction(data);
                oracleEl.textContent = fallbackDecisionSentence(data, symbol, action);
                oracleDecisionShown = true;
                if (window.BDOracleWorkspace) window.BDOracleWorkspace.onOracleSuccess(symbol, data);
                const certEl = document.getElementById('landingCert');
                const cert = full ? (data.decision_certificate || {}) : {};
                const disc = document.getElementById('landingDiscipline');
                const comp = document.getElementById('landingCompliance');
                paintLandingOracleHeader(symbolEl, scoreEl, verdictEl, data, symbol, action);
                paintLandingOracleMetrics(data);
                if (full) {
                    setLandingOraclePresentationLayout('full');
                    paintLandingFreshness(data);
                    paintLandingProMeta(proMeta, data, mode);
                    paintLandingUpgrade(upgradeEl, data);
                    renderLandingCertificate(certEl, cert, data);
                    renderLandingWhy(oracleEl, data, cert);
                    const followAction = data.decision_action || data.verdict || action || 'WAIT';
                    wireDisciplineMirror(disc, data, symbol, followAction);
                    paintLandingCompliance(data);
                    try { updateShareLinks(data); } catch (shareError) { console.debug(shareError); }
                } else if (ageOnly) {
                    setLandingOraclePresentationLayout('summary');
                    paintLandingFreshness(data);
                    proMeta.style.display = 'none';
                    upgradeEl.style.display = 'none';
                    renderLandingCertificate(certEl, {}, data);
                    renderLandingWhy(oracleEl, data, {});
                    if (disc) { disc.style.display = 'none'; disc.innerHTML = ''; }
                    if (comp) comp.style.display = 'none';
                    try { updateShareLinks(data); } catch (shareError) { console.debug(shareError); }
                } else {
                    setLandingOraclePresentationLayout('summary');
                    const freshChip = document.getElementById('oracleFreshnessLabel');
                    const freshWrap = document.getElementById('oracleFreshnessChip');
                    if (freshChip) freshChip.textContent = '';
                    if (freshWrap) freshWrap.style.display = 'none';
                    proMeta.style.display = 'none';
                    upgradeEl.style.display = 'none';
                    renderLandingCertificate(certEl, {}, data);
                    renderLandingWhy(oracleEl, data, {});
                    if (disc) { disc.style.display = 'none'; disc.innerHTML = ''; }
                    if (comp) comp.style.display = 'none';
                    try { updateShareLinks(data); } catch (shareError) { console.debug(shareError); }
                }
                try {
                    paintSealCertificateStamp(data);
                    syncLandingTrustPulseFromOracle(data, symbol);
                } catch (pulseError) { console.debug(pulseError); }
            } catch (error) {
                console.debug(error);
                if (!oracleDecisionShown) {
                    clearLandingOracleChrome();
                    oracleEl.textContent = i18nT('oracle.error');
                    const detail = error && error.message ? String(error.message) : String(error || 'unknown');
                    setLandingOracleFailReason('Exception: ' + detail);
                }
            }
            })();
            try {
                return await consultOracleInflight;
            } finally {
                consultOracleInflight = null;
                landingOracleBootComplete = true;
            }
        }

        function syncSymbolFromCatalog(symbol) {
            setSymbol(symbol);
        }

        async function applyAudience() {
            const aud = document.getElementById('landingAudience')?.value || 'retail';
            const lensMap = { retail:'prove', pro:'operate', whale:'desk', fund:'room' };
            localStorage.setItem('bd_audience', aud);
            localStorage.setItem('bd_lens', lensMap[aud] || 'prove');
            try {
                const res = await fetch('/api/audience/entry?audience=' + encodeURIComponent(aud));
                const d = await res.json();
                const cta = document.getElementById('audienceCta');
                if (cta) {
                    const promise = d.lens_promise || d.cta || '';
                    cta.textContent = (d.lens_label ? (d.lens_label + ' — ') : '') + promise;
                }
                const mode = document.getElementById('landingUxMode');
                if (mode && d.ux_mode_default) mode.value = d.ux_mode_default;
                if ((aud === 'fund' || aud === 'whale' || aud === 'pro') && d.entry_path) {
                    assignLocationHref(d.entry_path);
                }
            } catch (error) { console.debug(error); }
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
                    msg.textContent = data.detail || data.message || i18nT('waitlist.msg.generic');
                    msg.style.color = response.status === 409 ? 'var(--warning)' : 'var(--danger)';
                } else {
                    msg.textContent = data.message || i18nT('waitlist.msg.welcome', { position: data.position });
                    msg.style.color = 'var(--success)';
                    document.getElementById('waitlistEmail').value = '';
                }
                msg.style.display = 'block';
            } catch (error) { console.debug(error); msg.textContent = i18nT('waitlist.msg.generic');
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
        /** Oracle / seal certificate kept when trust-pulse stream omits hash. */
        let landingDecisionCert = null;

        function rememberLandingDecisionCert(data, symbol) {
            const cert = (data && data.decision_certificate) || {};
            const hash = cert.certificate_hash;
            if (!hash) return;
            const sym = String(cert.asset || data.symbol || symbol || landingPulseSymbol || 'BTC')
                .trim().toUpperCase() || 'BTC';
            landingDecisionCert = {
                ...cert,
                certificate_hash: hash,
                asset: sym,
                symbol: sym,
                prediction_id: data.prediction_id ?? cert.prediction_id ?? null,
            };
        }

        function _lpEnrichPulseWithLandingCert(p) {
            if (!p) return p;
            const sym = String(p.symbol || landingPulseSymbol || '').trim().toUpperCase();
            const proof = p.proof || {};
            const dc = p.decision_certificate || {};
            let hash = proof.certificate_hash || dc.certificate_hash || '';
            let mergedCert = dc;
            let mergedProof = { ...proof };
            if (!hash && landingDecisionCert && landingDecisionCert.certificate_hash) {
                const csym = String(landingDecisionCert.symbol || landingDecisionCert.asset || '').toUpperCase();
                if (sym && csym && sym === csym) {
                    hash = landingDecisionCert.certificate_hash;
                    mergedCert = { ...landingDecisionCert, ...dc, certificate_hash: hash };
                    mergedProof = {
                        ...mergedProof,
                        certificate_hash: hash,
                        prediction_id: mergedProof.prediction_id ?? landingDecisionCert.prediction_id,
                        share_text: mergedProof.share_text || landingDecisionCert.share_text,
                    };
                }
            }
            if (!hash) return p;
            return {
                ...p,
                decision_certificate: mergedCert,
                proof: mergedProof,
            };
        }

        function _landingPulseFactors(data) {
            const whyBlock = data.oqs_why || {};
            return whyBlock.top_3_factors
                || (data.explanation && data.explanation.top_3_factors)
                || data.top_3_factors
                || [];
        }

        function paintSealCertificateStamp(data) {
            const wrap = document.getElementById('sealCertificateStamp');
            const hashEl = document.getElementById('sealCertificateHash');
            if (!wrap || !hashEl) return;
            const cert = (data && data.decision_certificate) || {};
            const hash = cert.certificate_hash;
            if (!hash) {
                wrap.style.display = 'none';
                hashEl.textContent = '';
                return;
            }
            rememberLandingDecisionCert(data, data.symbol);
            hashEl.textContent = String(hash);
            wrap.style.display = 'block';
        }

        function syncLandingTrustPulseFromOracle(data, symbol) {
            if (!data) return;
            paintSealCertificateStamp(data);
            rememberLandingDecisionCert(data, symbol);
            const sym = String(data.symbol || symbol || 'BTC').trim().toUpperCase() || 'BTC';
            landingPulseSymbol = sym;
            const action = decideLandingAction(data);
            const cert = data.decision_certificate || {};
            const priorProof = (landingPulse && landingPulse.proof) || {};
            const fresh = data.data_freshness || {};
            const pulseView = {
                symbol: sym,
                action: action,
                verdict: action,
                price: data.price,
                change_24h: data.change_24h != null ? data.change_24h : data.change_24h_pct,
                sentence: fallbackDecisionSentence(data, sym, action),
                why: { factors: _landingPulseFactors(data) },
                freshness: fresh,
                decision_certificate: cert.certificate_hash ? cert : (landingPulse && landingPulse.decision_certificate),
                proof: {
                    ...priorProof,
                    certificate_hash: cert.certificate_hash || priorProof.certificate_hash,
                    prediction_id: data.prediction_id ?? priorProof.prediction_id,
                    share_text: cert.share_text || priorProof.share_text,
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
                const rawSrc = (f && typeof f === 'object' && f.source) ? String(f.source).trim() : '';
                const srcBit = rawSrc
                    ? (' <span style="opacity:.75;font-size:.78rem">· ' + esc(rawSrc) + '</span>')
                    : '';
                return '<div><strong>' + (i + 1) + '. ' + esc(f.factor || f) + '</strong>' + detail + srcBit + '</div>';
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
            const enriched = _lpEnrichPulseWithLandingCert(p || {});
            const proof = (enriched && enriched.proof) || {};
            const cert = (enriched && enriched.decision_certificate) || {};
            return proof.certificate_hash || cert.certificate_hash || '';
        }

        function _lpPulseHasCertificate(p) {
            return Boolean(_lpCertHash(p));
        }

        function _lpCertFromPulse(p) {
            const proof = (p && p.proof) || {};
            const dc = (p && p.decision_certificate) || {};
            const hash = _lpCertHash(p);
            if (!hash) return null;
            const mapFn = window.BDPublicDecision?.mapPublicDecisionAction;
            const rawVerdict = dc.decision_action || p.action || p.verdict || '';
            const verdict = typeof mapFn === 'function' ? mapFn(rawVerdict) : rawVerdict;
            return {
                ...dc,
                certificate_hash: hash,
                asset: String(dc.asset || p.symbol || 'BTC').trim().toUpperCase() || 'BTC',
                prediction_id: proof.prediction_id ?? dc.prediction_id ?? null,
                decision_action: verdict || rawVerdict || 'WAIT',
                share_text: dc.share_text || proof.share_text || '',
            };
        }

        function _lpNoCertificateLine() {
            return i18nT('pulse.no_cert');
        }

        function _lpCertIdPrefix(p) {
            const cert = _lpCertFromPulse(p);
            if (!cert) return '';
            let pid = cert.prediction_id != null && cert.prediction_id !== ''
                ? String(cert.prediction_id)
                : '';
            if (!pid && cert.certificate_hash) {
                pid = String(cert.certificate_hash).slice(0, 10);
            }
            return pid;
        }

        function openLandingPulseProof() {
            const p = landingPulse || {};
            const drawer = document.getElementById('lpProofDrawer');
            const toast = document.getElementById('lpProofCopyMsg');
            if (toast) toast.hidden = true;
            if (!drawer) return;
            const cert = _lpCertFromPulse(p);
            if (!cert) {
                drawer.hidden = true;
                drawer.innerHTML = '';
                if (toast) {
                    toast.textContent = _lpNoCertificateLine();
                    toast.hidden = false;
                }
                return;
            }
            drawer.hidden = false;
            renderLandingPulseProofDrawer(drawer, cert, p);
        }

        function renderLandingPulseProofDrawer(drawerEl, cert, pulse) {
            const proof = (pulse && pulse.proof) || {};
            const ledgerHref = esc(_lpProofLedgerHref(proof));
            const hashLabel = cert.certificate_hash ? String(cert.certificate_hash).slice(0, 16) + '…' : i18nT('ui.pending');
            const asset = cert.asset || pulse.symbol || 'BTC';
            const verdict = cert.decision_action || pulse.action || pulse.verdict || 'WAIT';
            let pid = cert.prediction_id != null && cert.prediction_id !== ''
                ? String(cert.prediction_id)
                : '';
            if (!pid && cert.certificate_hash) {
                pid = String(cert.certificate_hash).slice(0, 10);
            }
            if (!pid) pid = '—';
            const copyBtn = cert.share_text
                ? '<button type="button" class="btn-secondary" id="lpDrawerCopyCert">' + esc(i18nT('ui.copy_certificate_text')) + '</button>'
                : '';
            drawerEl.innerHTML =
                '<p style="margin:0 0 .5rem"><strong>' + esc(i18nT('pulse.drawer.title')) + '</strong></p>' +
                '<p style="margin:0 0 .35rem"><strong>' + esc(i18nT('ui.asset')) + ':</strong> ' + esc(asset) + '</p>' +
                '<p style="margin:0 0 .35rem"><strong>' + esc(i18nT('ui.verdict')) + ':</strong> ' + esc(verdict) + '</p>' +
                '<p style="margin:0 0 .5rem"><strong>' + esc(i18nT('ui.id')) + ':</strong> ' + esc(pid) + '</p>' +
                '<p style="margin:0 0 .5rem;color:var(--text-muted)"><code>' + esc(hashLabel) + '</code></p>' +
                '<div style="display:flex;flex-wrap:wrap;gap:.35rem;margin-bottom:.5rem">' +
                copyBtn +
                '<a class="btn-secondary" href="' + ledgerHref + '">' + esc(i18nT('pulse.drawer.open_ledger')) + '</a>' +
                '<button type="button" class="btn-secondary" id="lpDrawerClose">' + esc(i18nT('pulse.drawer.close')) + '</button>' +
                '</div>';
            document.getElementById('lpDrawerCopyCert')?.addEventListener('click', () => {
                navigator.clipboard.writeText(cert.share_text || '').then(() => {
                    const msg = document.getElementById('lpProofCopyMsg');
                    if (msg) {
                        msg.textContent = i18nT('pulse.msg.cert_text_copied');
                        msg.hidden = false;
                    }
                }).catch(() => {});
            });
            document.getElementById('lpDrawerClose')?.addEventListener('click', () => {
                drawerEl.hidden = true;
            });
        }

        function copyLandingPulseCertId() {
            const idPrefix = _lpCertIdPrefix(landingPulse);
            const msg = document.getElementById('lpProofCopyMsg');
            if (!idPrefix) {
                if (msg) {
                    msg.textContent = _lpNoCertificateLine();
                    msg.hidden = false;
                }
                return;
            }
            const done = () => {
                if (msg) {
                    msg.textContent = i18nT('pulse.msg.cert_id_copied');
                    msg.hidden = false;
                }
            };
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(String(idPrefix)).then(done).catch(() => {
                    if (msg) {
                        msg.textContent = i18nT('pulse.msg.copy_cert_id_failed');
                        msg.hidden = false;
                    }
                });
            } else if (msg) {
                msg.textContent = i18nT('pulse.msg.copy_unsupported');
                msg.hidden = false;
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
                if (e.target.closest('[data-lp-copy-cert-id]')) {
                    e.preventDefault();
                    e.stopPropagation();
                    copyLandingPulseCertId();
                    return;
                }
                if (e.target.closest('[data-lp-proof-open]')) {
                    e.preventDefault();
                    e.stopPropagation();
                    requestAnimationFrame(() => openLandingPulseProof());
                    return;
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
            const proof = (p && p.proof) || {};
            const ledgerHref = esc(_lpProofLedgerHref(proof));
            const bits = [
                '<a class="bd-chip ok" href="' + ledgerHref + '">' + esc(i18nT('pulse.verify_ledger')) + '</a>',
            ];
            if (hasCert) {
                bits.push(
                    '<button type="button" class="bd-chip bd-chip-btn ok" data-lp-proof-open="1">' + esc(i18nT('pulse.free_proof')) + '</button>'
                );
                const idPrefix = _lpCertIdPrefix(p);
                if (idPrefix) {
                    bits.push(
                        `<button type="button" class="bd-chip bd-chip-btn" data-lp-copy-cert-id="1" title="${esc(i18nT('ui.copy_cert_id_title'))}">${esc(i18nT('pulse.cert_prefix'))} ${esc(idPrefix)}</button>`
                    );
                }
            } else {
                bits.push(
                    `<span class="bd-chip bd-chip-muted">${esc(_lpNoCertificateLine())}</span>`
                );
            }
            box.innerHTML = bits.join('');
            box.querySelectorAll('a[href*="twitter.com"], a[href*="x.com"]').forEach((node) => node.remove());
            const drawer = document.getElementById('lpProofDrawer');
            if (drawer && !hasCert) drawer.hidden = true;
        }

        function renderLandingPulse(p) {
            if (!p) return;
            p = _lpEnrichPulseWithLandingCert(p);
            if (_lpCertHash(p)) {
                const dc = p.decision_certificate || {};
                const sym = String(p.symbol || landingPulseSymbol || '').toUpperCase();
                landingDecisionCert = {
                    ...landingDecisionCert,
                    ...dc,
                    certificate_hash: _lpCertHash(p),
                    symbol: sym,
                    asset: dc.asset || sym,
                    prediction_id: (p.proof || {}).prediction_id ?? dc.prediction_id,
                };
            }
            landingPulse = p;
            const act = window.BDPublicDecision?.mapPublicDecisionAction(p.action || p.verdict) || p.action || 'WAIT';
            const actionEl = document.getElementById('lpAction');
            if (actionEl) {
                const label = window.BDPublicDecision?.mapAndLocalizePublicDecisionAction
                    ? window.BDPublicDecision.mapAndLocalizePublicDecisionAction(p.action || p.verdict || act)
                    : act;
                actionEl.textContent = label;
                const cssToken = act === 'CONDITIONS MET' ? 'WAIT' : String(act).replace(/\s+/g, '_');
                actionEl.className = 'tp-mini-action bd-tp-action ' + cssToken;
            }
            const sym = document.getElementById('lpSym');
            if (sym) sym.textContent = `${p.symbol || 'BTC'} ${_lpPriceBit(p)}`;
            const sent = document.getElementById('lpSentence');
            if (sent) sent.textContent = p.sentence || i18nT('pulse.fallback_sentence');
            _lpRenderWhy((p.why && p.why.factors) || []);
            const fresh = p.freshness || p.data_freshness || {};
            const dot = document.getElementById('lpDot');
            if (dot) dot.className = 'tp-mini-dot' + (fresh.stale ? ' stale' : '');
            const fl = document.getElementById('lpFresh');
            if (fl) {
                const state = String(fresh.state || fresh.status || '').toLowerCase();
                if (state === 'unknown') {
                    fl.textContent = '';
                } else {
                    const stale = fresh.stale === true || state === 'stale';
                    const knownFresh = state === 'fresh' || state === 'ok' || state === 'live';
                    fl.textContent = stale
                        ? (fresh.label || i18nT('pulse.stale'))
                        : (fresh.label || (knownFresh ? i18nT('pulse.live') : ''));
                    if (!fl.textContent) fl.textContent = '';
                }
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
                scheduleLandingPulseStream(sym);
            } catch (error) { console.debug(error); }
        }

        async function loadLandingTrustPulse() {
            const symbol = landingSymbolValue();
            const mode = document.getElementById('landingUxMode')?.value || 'beginner';
            const lang = currentLang();
            await fetchLandingTrustPulse(symbol, mode, lang);
        }

        let lpRefreshInFlight = false;
        function setLpRefreshUi(state) {
            const btn = document.getElementById('lpRefreshBtn');
            if (!btn) return;
            const def = btn.getAttribute('data-default-label') || i18nT('dash.refresh') || 'Refresh';
            if (state === 'loading') {
                btn.disabled = true;
                btn.setAttribute('aria-busy', 'true');
                btn.classList.add('bd-lp-refreshing');
                btn.textContent = i18nT('pulse.refreshing') || 'Refreshing…';
            } else if (state === 'updated') {
                btn.disabled = true;
                btn.removeAttribute('aria-busy');
                btn.classList.remove('bd-lp-refreshing');
                btn.textContent = i18nT('pulse.updated') || 'Updated';
            } else {
                btn.disabled = false;
                btn.removeAttribute('aria-busy');
                btn.classList.remove('bd-lp-refreshing');
                btn.textContent = def;
            }
        }
        async function refreshLandingTrustPulseInteractive() {
            if (lpRefreshInFlight) return;
            lpRefreshInFlight = true;
            setLpRefreshUi('loading');
            try {
                await loadLandingTrustPulse();
            } catch (error) {
                console.debug(error);
            } finally {
                lpRefreshInFlight = false;
                setLpRefreshUi('updated');
                window.setTimeout(() => setLpRefreshUi('idle'), 1000);
            }
        }
        window.__landing_refreshTrustPulse = refreshLandingTrustPulseInteractive;

        function scheduleLandingPulseStream(symbol) {
            const start = () => startLandingPulseStream(symbol);
            if (typeof requestIdleCallback === 'function') {
                requestIdleCallback(start, { timeout: 2500 });
            } else {
                setTimeout(start, 0);
            }
        }

        let landingPulsePollTimer = null;
        let landingOraclePollTimer = null;

        function startLandingPulseStream(symbol) {
            const sym = String(symbol || landingPulseSymbol || 'BTC').trim().toUpperCase() || 'BTC';
            landingPulseSymbol = sym;
            const policy = window.BDLiveRefresh && window.BDLiveRefresh.getPolicy();
            if (policy && !policy.live_stream_enabled) {
                if (landingPulseEs) {
                    try { landingPulseEs.close(); } catch (error) { console.debug(error); }
                    landingPulseEs = null;
                }
                return;
            }
            if (window.BDLiveRefresh) {
                if (landingPulseEs) {
                    try { landingPulseEs.close(); } catch (error) { console.debug(error); }
                    landingPulseEs = null;
                }
                landingPulseEs = window.BDLiveRefresh.startTrustPulseStream(sym, (d) => {
                    const pulse = d && (d.pulse || d);
                    if (pulse && String(pulse.symbol || '').toUpperCase() === landingPulseSymbol) {
                        renderLandingPulse(pulse);
                    }
                }, { key: 'landing-trust-pulse' });
                return;
            }
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

        function startLandingLiveRefresh(policy) {
            const ms = (policy && policy.poll_interval_ms) || 45000;
            if (landingPulsePollTimer) clearInterval(landingPulsePollTimer);
            landingPulsePollTimer = setInterval(() => {
                if (document.hidden) return;
                const symbol = landingPulseSymbol || landingSymbolValue();
                const mode = document.getElementById('landingUxMode')?.value || 'beginner';
                const lang = currentLang();
                void fetchLandingTrustPulse(symbol, mode, lang);
            }, ms);
            if (landingOraclePollTimer) clearInterval(landingOraclePollTimer);
            landingOraclePollTimer = setInterval(() => {
                if (document.hidden || !landingOracleBootComplete) return;
                void consultOracle({ silent: true });
            }, ms);
            startLandingPulseStream(landingPulseSymbol || landingSymbolValue());
        }

        function shareLandingPulseProof() {
            const btn = document.getElementById('lpShareBtn');
            if (!btn) return;
            const proof = (landingPulse && landingPulse.proof) || {};
            const text = proof.share_text || 'BLACKDARK Trust Pulse — verify /oracle-accuracy';
            if (navigator.clipboard) navigator.clipboard.writeText(text).catch(() => {});
            if (proof.share_urls && proof.share_urls.x) {
                openWindow(proof.share_urls.x);
            }
        }
        function landingPaidTier(tier) {
            const t = String(tier || 'free').toLowerCase();
            return ['pro', 'elite', 'quant', 'institutional', 'whale'].includes(t);
        }

        async function syncLandingArbButton() {
            const btn = document.getElementById('lpArbBtn');
            if (!btn) return;
            if (window.BDSessionHint && !window.BDSessionHint.likelyAuthenticated()) {
                btn.style.display = 'none';
                return;
            }
            try {
                const res = await fetch('/api/auth/me', { credentials: 'same-origin' });
                const d = await res.json();
                const tier = (d.user && d.user.tier) || (d.tier && (d.tier.tier || d.tier.id)) || 'free';
                btn.style.display = (d.authenticated && landingPaidTier(tier)) ? '' : 'none';
            } catch (error) {
                btn.style.display = 'none';
            }
        }

        async function toggleLandingArbPanel() {
            const panel = document.getElementById('lpArbPanel');
            const list = document.getElementById('lpArbList');
            const sym = landingPulseSymbol || landingSymbolValue() || 'BTC';
            if (!panel || !list) return;
            panel.hidden = !panel.hidden;
            if (panel.hidden) return;
            list.innerHTML = '<li>' + (window.BD_I18N && BD_I18N.t('arb.loading') || '…') + '</li>';
            try {
                const res = await fetch('/api/oracle/arb-opportunities/' + encodeURIComponent(sym), { credentials: 'same-origin' });
                const d = await res.json();
                if (!res.ok) {
                    const msg = (d.detail && d.detail.message) || d.detail || 'Upgrade required';
                    list.innerHTML = '<li>' + String(msg) + '</li>';
                    return;
                }
                const rows = d.opportunities || [];
                list.innerHTML = rows.length
                    ? rows.map((o) => (
                        '<li style="margin:.35rem 0"><strong>' + o.exchange_1 + '</strong> vs <strong>' + o.exchange_2 + '</strong> · ' +
                        o.price_diff_percent + '% · ' +
                        '<a href="' + o.link_exchange_1 + '" target="_blank" rel="noopener">' + o.exchange_1 + '</a> · ' +
                        '<a href="' + o.link_exchange_2 + '" target="_blank" rel="noopener">' + o.exchange_2 + '</a></li>'
                    )).join('')
                    : '<li>' + (window.BD_I18N && BD_I18N.t('arb.none_symbol', { symbol: sym }) || sym) + '</li>';
            } catch (error) {
                list.innerHTML = '<li>Could not load arb opportunities.</li>';
            }
        }

        document.getElementById('lpArbBtn')?.addEventListener('click', () => { toggleLandingArbPanel(); });

        document.getElementById('lpShareBtn')?.addEventListener('click', (ev) => {
            const btn = ev.currentTarget;
            if (!(btn instanceof HTMLElement)) return;
            btn.classList.remove('bd-motion-share');
            void btn.offsetWidth;
            btn.classList.add('bd-motion-share');
            window.setTimeout(() => shareLandingPulseProof(), 0);
        });


        window.openCompare = function () {
            window.BDOracleWorkspace?.openCompareModal();
        };

        function afterLandingOracleBoot() {
            if (window.BDLiveRefresh) {
                return window.BDLiveRefresh.ensurePolicy().then((p) => startLandingLiveRefresh(p));
            }
            startLandingLiveRefresh(null);
            return Promise.resolve();
        }

        function scheduleDeferredOracleBoot(hadPulseSSR) {
            let started = false;
            const bootOracle = () => {
                if (started) return;
                started = true;
                requestAnimationFrame(() => {
                    void consultOracle().finally(() => { void afterLandingOracleBoot(); });
                });
            };
            const oracleEl = document.getElementById('oracle');
            if (oracleEl && typeof IntersectionObserver === 'function') {
                const io = new IntersectionObserver((entries) => {
                    if (entries.some((e) => e.isIntersecting)) {
                        io.disconnect();
                        bootOracle();
                    }
                }, { rootMargin: '160px', threshold: 0.01 });
                io.observe(oracleEl);
            }
            scheduleNonCriticalLandingWork(bootOracle);
            if (!hadPulseSSR) {
                scheduleNonCriticalLandingWork(() => {
                    void loadLandingTrustPulse();
                });
            } else {
                scheduleNonCriticalLandingWork(() => {
                    scheduleLandingPulseStream(landingPulseSymbol || landingSymbolValue());
                });
            }
        }

        function landingBootMainOnLoad() {
            const hadPulseSSR = applyLandingPulseSSR();
            scheduleNonCriticalLandingWork(() => {
                updateShareLinks(null);
                if (window.BDOracleWorkspace) {
                    window.BDOracleWorkspace.init({
                        fetchQuick: async (sym) => {
                            const mode = document.getElementById('landingUxMode')?.value || 'beginner';
                            const lang = currentLang();
                            const { data } = await fetchOraclePayload(sym, mode, lang);
                            if (!landingOracleHasDecision(data)) {
                                const offline = window.BDOracleWorkspace.getOfflinePayload(sym);
                                if (offline) return offline;
                                throw new Error('no decision');
                            }
                            return data;
                        },
                        getLang: currentLang,
                    });
                }
                loadLandingAnalytics();
                loadTelegramBotLink();
                void syncLandingArbButton();
                if ('serviceWorker' in navigator) {
                    navigator.serviceWorker.register('/sw.js').catch((error) => { console.debug(error); });
                }
            });
            if (!window.__landingPulseHydrated && !hadPulseSSR) {
                void loadLandingTrustPulse();
            }
            if (!window.__landingPulseHydrated) {
                scheduleDeferredOracleBoot(hadPulseSSR);
            } else {
                scheduleDeferredOracleBoot(true);
            }
        }

        if (document.readyState === 'complete') {
            landingBootMainOnLoad();
        } else {
            window.addEventListener('load', landingBootMainOnLoad, { once: true });
        }

        window.__landing_consultOracle = consultOracle;
        window.__landing_tryOracleFree = tryOracleFree;
        window.__landing_applyAudience = applyAudience;
        window.__landing_joinWaitlist = joinWaitlist;
        window.__landing_openCompare = function () {
            window.BDOracleWorkspace?.openCompareModal();
        };
        window.consultOracle = consultOracle;
        window.tryOracleFree = tryOracleFree;
        window.applyAudience = applyAudience;
        window.joinWaitlist = joinWaitlist;
        window.openCompare = window.__landing_openCompare;
