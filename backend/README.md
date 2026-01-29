# CoinStack Backend

## Setup

1. Install [uv](https://docs.astral.sh/uv/) and sync dependencies:
```bash
# Install uv: pip install uv  (or curl -LsSf https://astral.sh/uv/install.sh | sh)
cd backend
uv sync --all-extras
```

2. Install Playwright browser (required for scrapers):
```bash
uv run playwright install chromium
```

3. Create data directories:
```bash
bash create_dirs.sh
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

5. Run the server (V2 entrypoint; sets Windows event loop for Playwright):
```bash
uv run run_server.py
```

## Import Collection

To import your Excel collection:

```bash
curl -X POST "http://localhost:8000/api/import/collection?dry_run=false" \
  -F "file=@../collection-v1.xlsx"
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## LLM / Enrichment

API keys are read from env: `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `GOOGLE_API_KEY`. Profile and model routing are in `config/llm_config.yaml`.

If you see **"Your credit balance is too low to access the Anthropic API"** or **"All providers failed"** when using historical context or other LLM features:

1. **Anthropic**: Top up credits at [console.anthropic.com → Settings → Billing](https://console.anthropic.com/settings/billing).
2. **Use another provider**: Set `LLM_PROFILE=development` in `.env` so context_generate uses OpenRouter (e.g. deepseek-v3) as primary; ensure `OPENROUTER_API_KEY` is set and has credits.
3. **Local**: Use `LLM_PROFILE=offline` and run Ollama for free local models.

See [../docs/PLAN-LLM-SETTINGS-PAGE.md](../docs/PLAN-LLM-SETTINGS-PAGE.md) for full LLM settings and billing plan.
