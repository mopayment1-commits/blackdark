"""Trust Pulse uses CoinPaprika when Binance is unavailable."""

import pytest


@pytest.mark.asyncio
async def test_trust_pulse_coinpaprika_market(monkeypatch):
    from trust_pulse import _compute_oracle_payload

    async def paprika(pair):
        return {
            "price": 44000.0,
            "change_24h": 1.2,
            "volume": 50.0,
            "quote_volume": 2_200_000.0,
            "source": "coinpaprika",
            "price_history_daily": [{"close": 44000.0}],
            "price_history_source": "coinpaprika_ohlcv_latest",
        }

    monkeypatch.setattr("market_context.fetch_binance_ticker", paprika)

    async def passthrough_enrich(m, a, session=None):
        return m

    monkeypatch.setattr("coinmarketcap_api.enrich_market_with_cmc_metadata", passthrough_enrich)
    async def noop_persist(*a, **k):
        return None

    monkeypatch.setattr("trust_pulse._persist_trust_pulse_payload", noop_persist)
    monkeypatch.setattr("trust_pulse._attach_trust_pulse_certificate", lambda p, **k: None)

    async def no_whale(*a, **k):
        return None

    async def no_unified(*a, **k):
        return {}

    monkeypatch.setattr("market_context.fetch_cvvd_whale_alert", no_whale)
    monkeypatch.setattr("trust_pulse._fetch_trust_pulse_unified", no_unified)

    def identity_enrich(p, **kwargs):
        return p

    monkeypatch.setattr("decision_enrichment.enrich_oracle_decision", identity_enrich)

    payload = await _compute_oracle_payload(
        "BTC",
        tier="free",
        ux_mode="beginner",
        lang="en",
        persist=False,
    )
    assert payload.get("price") == 44000.0
    assert payload.get("price_history_daily")
    assert payload.get("price_source") == "coinpaprika"
