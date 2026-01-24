# CoinStack Backend

## Setup

1. Install dependencies:
```bash
pip install uv
uv sync
```

2. Create data directories:
```bash
bash create_dirs.sh
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

4. Run the server:
```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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
