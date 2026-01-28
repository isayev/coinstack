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
