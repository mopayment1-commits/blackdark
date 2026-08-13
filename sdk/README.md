# BLACKDARK Python SDK

Official client for Trust OS public evidence routes and **Decision API v1**.

```python
from blackdark import BlackdarkClient

# Commercial Financial Intelligence contract (sales-issued key)
client = BlackdarkClient("https://api.example", api_key="bd_live_…")
print(client.me())
print(client.oracle("BTC")["verdict"])
print(client.accuracy()["oracle"])
print(client.feed()["record_count"])
```

Auth: `X-API-Key` / `Authorization: Bearer`. Session `token=` is only for Trust OS product routes, not the commercial contract.

Versioning: Decision API lives under `/api/v1`. Deprecations are announced in `/api/v1/changelog` with ≥12 months `Sunset` notice. Legacy `/api/b2b/feed` (shared house key) is deprecated.
