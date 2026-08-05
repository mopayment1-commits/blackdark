# AGENTS.md

## Cursor Cloud specific instructions

BLACKDARK is an async Python 3.12 FastAPI crypto-arbitrage intelligence platform. The primary
developer-facing service is the web dashboard/API (monolith) on port `8080`. Auxiliary worker
modes (`aggregator`, `arbitrage`, `ingestion`) and the full Postgres/Redis/Kafka/Vault stack in
`docker-compose.yml` are for production scale-out and are NOT required for local development.

### Environment
- Python dependencies are installed into a virtualenv at `.venv/` (gitignored) from
  `requirements.txt`. Activate it with `source .venv/bin/activate` before running anything.
- The startup/update script only refreshes dependencies; it does NOT start services.
- Local dev uses SQLite by default (`data/blackdark.db`) because `DATABASE_URL` is empty. No
  external database/Redis/Kafka/Vault is needed to run or test the monolith.

### Running the app (dev)
- Start the web service: `source .venv/bin/activate && MANIFEST_AUTO_APPROVE=true python run_service.py web`
  - Serves the dashboard/API on `http://localhost:8080` and a health sidecar on `http://localhost:8180/health/live`.
  - Always export `MANIFEST_AUTO_APPROVE=true`; otherwise ingestion/aggregator paths pause waiting
    for a human to press ENTER to approve `data/operational_manifest.json`. (In `web` mode
    `run_service.py` disables the aggregator/ingestion loops, but the env var keeps other code paths
    non-interactive.)
  - A couple of non-fatal background `ImportError` warnings (e.g. `load_persistent_freeze`,
    `get_quote_age_ms`) may print at startup; the server still starts and serves requests normally.
- No API keys are required for local dev — data source fetchers fall back to mock/free tiers.

### Testing
- Run the suite with `source .venv/bin/activate && MANIFEST_AUTO_APPROVE=true python -m pytest -q`
  (config in `pytest.ini`, `asyncio_mode=auto`).
- Known pre-existing failures unrelated to environment setup (present on the base branch): several
  `tests/test_slippage_guard.py` cases and `tests/test_platform_features.py::test_footprint_async`
  fail due to code-level issues (a missing `get_quote_age_ms` symbol and test DB-table setup), and
  `tests/test_fee_matrix.py::test_refresh_fee_matrix_ccxt_mock` is order-dependent. Do not treat
  these as caused by your changes.
- CI (`.github/workflows/ci.yml`) only gates a subset: the profit/fee tests with a 90% coverage
  bar, plus due-diligence smoke scripts and a Docker build. There is no configured
  linter/formatter (no ruff/flake8/black/pyproject); pytest is the effective quality gate.
