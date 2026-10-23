/**
 * TradingView Lightweight Charts — shared price candle mount (Binance / public API).
 */
(function (global) {
    const _charts = new WeakMap();

    function normalizeSymbol(sym) {
        return String(sym || "BTC").trim().toUpperCase().replace(/[^A-Z0-9]/g, "") || "BTC";
    }

    async function fetchChartBars(symbol, interval, limit) {
        const qs = new URLSearchParams({
            symbol: normalizeSymbol(symbol),
            interval: interval || "1h",
            limit: String(limit || 120),
        });
        const res = await fetch("/api/public/market/chart-bars?" + qs.toString(), {
            credentials: "same-origin",
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok || !body.ok) {
            const err = new Error(body.detail || "chart_bars_unavailable");
            err.status = res.status;
            throw err;
        }
        return body;
    }

    function barsToSeries(bars) {
        return (bars || [])
            .map((b) => {
                const t = Math.floor((b.open_time_ms || b.time_ms || 0) / 1000);
                if (!t) return null;
                return {
                    time: t,
                    open: +b.open,
                    high: +b.high,
                    low: +b.low,
                    close: +b.close,
                };
            })
            .filter(Boolean);
    }

    function ensureChart(el) {
        if (typeof global.LightweightCharts === "undefined") return null;
        let row = _charts.get(el);
        if (row) return row;
        const chart = global.LightweightCharts.createChart(el, {
            layout: { background: { color: "#111118" }, textColor: "#a1a1aa" },
            grid: { vertLines: { color: "#2a2a35" }, horzLines: { color: "#2a2a35" } },
            timeScale: { borderColor: "#2a2a35" },
            rightPriceScale: { borderColor: "#2a2a35" },
            width: el.clientWidth || 320,
            height: el.clientHeight || 220,
        });
        const series = chart.addCandlestickSeries({
            upColor: "#22c55e",
            downColor: "#ef4444",
            borderVisible: false,
            wickUpColor: "#22c55e",
            wickDownColor: "#ef4444",
        });
        const ro = new ResizeObserver(() => {
            chart.applyOptions({ width: el.clientWidth });
        });
        ro.observe(el);
        row = { chart, series, ro };
        _charts.set(el, row);
        return row;
    }

    async function mountPriceChart(el, options) {
        if (!el) return null;
        const opts = options || {};
        const symbol = normalizeSymbol(opts.symbol);
        const interval = opts.interval || "1h";
        const limit = opts.limit || 120;
        const noteEl = opts.noteEl || null;
        if (noteEl) noteEl.textContent = opts.loadingText || "Loading chart…";
        try {
            for (let i = 0; i < 30 && typeof global.LightweightCharts === "undefined"; i++) {
                await new Promise((r) => setTimeout(r, 50));
            }
            const row = ensureChart(el);
            if (!row) {
                if (noteEl) noteEl.textContent = "Chart library loading — refresh shortly.";
                return null;
            }
            const payload = await fetchChartBars(symbol, interval, limit);
            const data = barsToSeries(payload.bars);
            row.series.setData(data);
            row.chart.timeScale().fitContent();
            if (noteEl) {
                noteEl.textContent =
                    "TradingView Lightweight Charts · " +
                    (payload.source || "binance") +
                    " · " +
                    data.length +
                    " bars · " +
                    (payload.interval || interval);
            }
            return payload;
        } catch (e) {
            if (noteEl) noteEl.textContent = opts.errorText || "Chart unavailable.";
            console.debug(e);
            return null;
        }
    }

    global.bdMountPriceChart = mountPriceChart;
})(window);
