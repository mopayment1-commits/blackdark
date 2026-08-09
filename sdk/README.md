# BLACKDARK Python SDK

Official decision-signal client (`sdk/blackdark`).

```python
from blackdark import BlackdarkClient

client = BlackdarkClient("https://your-host")
print(client.model_card())
print(client.dd_closure()["all_done"])
```

Versioning: semver. Deprecations announced in `/changelog`.
