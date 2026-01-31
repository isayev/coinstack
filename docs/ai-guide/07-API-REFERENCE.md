# API Reference (V2)

> **Interactive Documentation:** For complete, up-to-date API documentation, use Swagger UI at `http://localhost:8000/docs`.
> 
> This document provides a quick reference for V2 Clean Architecture endpoints.

---

## Base Configuration

- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api/v2/`
- **Swagger UI**: `http://localhost:8000/docs`

**Router Locations**:
- Coins: `src/infrastructure/web/routers/v2.py`
- LLM: `src/infrastructure/web/routers/llm.py`
- Catalog: `src/infrastructure/web/routers/catalog.py` (V1) & `catalog_v2.py` (V2)
- Scraper: `src/infrastructure/web/routers/scrape_v2.py`
- Vocab: `src/infrastructure/web/routers/vocab.py`
- Series: `src/infrastructure/web/routers/series.py`
- Provenance: `src/infrastructure/web/routers/provenance.py`
- Die Study: `src/infrastructure/web/routers/die_study.py`
- Stats: `src/infrastructure/web/routers/stats.py`
- Audit: `src/infrastructure/web/routers/audit_v2.py`
- Review: `src/infrastructure/web/routers/review.py`
- Import: `src/infrastructure/web/routers/import_v2.py`

---

## Coins API (`/api/v2/coins`)

### List Coins
```http
GET /api/v2/coins
```
**Query Parameters**: `page`, `per_page`, `category`, `metal`, `issuer`, `mint`, `year_start`, `year_end`, `sort_by`, `sort_dir`

### Get Coin
```http
GET /api/v2/coins/{id}
```

### Create Coin
```http
POST /api/v2/coins
```

### Update Coin
```http
PUT /api/v2/coins/{id}
```

### Delete Coin
```http
DELETE /api/v2/coins/{id}
```

---

## LLM API (`/api/v2/llm`)

### Identify Coin (Vision)
```http
POST /api/v2/llm/identify/coin/{coin_id}
```

### Transcribe Legends
```http
POST /api/v2/llm/legend/transcribe/coin/{coin_id}
```

### Generate Context (RAG)
```http
POST /api/v2/llm/context/generate
```

---

## Catalog API

### Parse Reference (V2)
```http
POST /api/v2/catalog/parse
```
Parses a raw string (e.g. "RIC I 207") into structured data.

### Reference Integrity (V1)
```http
GET /api/catalog/integrity
```

### Bulk Enrich (V1)
```http
POST /api/catalog/bulk-enrich
```

---

## Scraper API (`/api/v2/scrape`)

### Scrape URL
```http
POST /api/v2/scrape?url={url}
```
Supports Heritage, CNG, Biddr, eBay, etc.

---

## Import API (`/api/v2/import`)

### Import from URL
```http
POST /api/v2/import/url
```
Scrapes and imports a coin in one step.

### Lookup NGC Cert
```http
POST /api/v2/import/ngc/{cert_number}/{grade}
```

---

## Vocabulary API (`/api/v2/vocab`)

### Search Terms
```http
GET /api/v2/vocab/search
```

### Sync Vocabulary
```http
POST /api/v2/vocab/sync
```

---

## Series API (`/api/v2/series`)

### List Series
```http
GET /api/v2/series
```

### Create Series
```http
POST /api/v2/series
```

---

## Provenance API

### Get Coin Provenance
```http
GET /api/v2/coins/{coin_id}/provenance
```

### Add Provenance Event
```http
POST /api/v2/coins/{coin_id}/provenance
```

### Update/Delete Event
```http
PUT /api/v2/provenance/{id}
DELETE /api/v2/provenance/{id}
```

---

## Die Study API (`/api/v2/die-study`)

### Die Links
```http
GET /api/v2/die-study/links/{coin_id}
POST /api/v2/die-study/links
```

### Die Groups
```http
GET /api/v2/die-study/groups
```

---

## Stats API (`/api/v2/stats`)

### Dashboard Stats
```http
GET /api/v2/stats/dashboard
```
Returns total coins, value, health, and distribution metrics.

---

## Audit API (`/api/v2/audit`)

### Run Audit
```http
GET /api/v2/audit/run
```

### Get Report
```http
GET /api/v2/audit/report
```

---

## Review API (`/api/v2/review`)

### Review Counts
```http
GET /api/v2/review/counts
```
Returns counts for pending vocabulary reviews, LLM suggestions, etc.

---

**Next:** [08-CODING-PATTERNS.md](08-CODING-PATTERNS.md)