# API Reference (V2)

> **Interactive Documentation:** For complete, up-to-date API documentation, use Swagger UI at `http://localhost:8000/docs` when the backend is running.
> 
> This document provides a quick reference for V2 Clean Architecture endpoints.

---

## Base Configuration

- **Base URL**: `http://localhost:8000`
- **API Prefix**: `/api/v2/`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

**Router Locations** (V2 Clean Architecture):
- Coins: `src/infrastructure/web/routers/v2.py`
- Vocabulary: `src/infrastructure/web/routers/vocab.py`
- Series: `src/infrastructure/web/routers/series.py`
- Scraper: `src/infrastructure/web/routers/scrape_v2.py`
- Audit: `src/infrastructure/web/routers/audit_v2.py`
- LLM: `src/infrastructure/web/routers/llm.py`
- Provenance: `src/infrastructure/web/routers/provenance.py`
- Die Study: `src/infrastructure/web/routers/die_study.py`

---

## Coins API (`/api/v2/coins`)

**Router**: `src/infrastructure/web/routers/v2.py`

### List Coins

```http
GET /api/v2/coins
```

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (1-based). Frontend uses infinite scroll; no page-number UI. `page`/`per_page` are "chunk"/"offset" semantics. |
| `per_page` | int | 20 | Items per page (1–1000). |
| `category` | string | - | Filter by category (imperial, republic, etc.) |
| `metal` | string | - | Filter by metal (gold, silver, bronze, etc.) |
| `issuer` | string | - | Search by issuer name (partial match). UI "search" uses this parameter. |
| `mint` | string | - | Filter by mint name |
| `year_start` | int | - | Minimum year |
| `year_end` | int | - | Maximum year |
| `sort_by` | string | - | Sort field |
| `sort_dir` | string | `asc` | Sort direction (`asc`, `desc`) |

**Search in the UI:** The header and Command Palette "search" are implemented via the `issuer` parameter (partial match). There is no separate full-text `search` or `q` parameter on this endpoint.

**Response**: `List[CoinResponse]`

```json
[
  {
    "id": 1,
    "category": "imperial",
    "metal": "silver",
    "dimensions": {
      "weight_g": 3.82,
      "diameter_mm": 18.0,
      "die_axis": 6,
      "specific_gravity": 10.5
    },
    "issue_status": "official",
    "attribution": {
      "issuer": "Augustus",
      "mint": "Lugdunum",
      "year_start": -2,
      "year_end": 4
    },
    "grading": {
      "grading_state": "graded",
      "grade": "VF",
      "service": "ngc",
      "certification_number": "1234567-001"
    },
    "images": [
      {
        "url": "/images/coins/1/obverse.jpg",
        "image_type": "obverse",
        "is_primary": true
      }
    ]
  }
]
```

**Example**:

```bash
curl "http://localhost:8000/api/v2/coins?category=imperial&metal=silver&page=1&per_page=20"
```

---

### Get Coin by ID

```http
GET /api/v2/coins/{id}
```

**Response**: `CoinResponse` (includes all relationships: images, references, provenance)

```json
{
  "id": 1,
  "category": "imperial",
  "metal": "silver",
  "dimensions": { ... },
  "attribution": { ... },
  "grading": { ... },
  "acquisition": {
    "price": 450.00,
    "currency": "USD",
    "source": "Heritage Auctions",
    "date": "2023-06-15",
    "url": "https://..."
  },
  "design": {
    "obverse_legend": "CAESAR AVGVSTVS DIVI F PATER PATRIAE",
    "obverse_description": "Laureate head right",
    "reverse_legend": "AVGVSTI F COS DESIG PRINC IVVENT",
    "reverse_description": "Gaius and Lucius standing"
  },
  "issue_status": "official",
  "die_info": {
    "obverse_die_id": "O-Aug-1",
    "reverse_die_id": "R-Aug-1"
  },
  "monograms": [ ... ],
  "find_data": {
    "find_spot": "Tetbury Hoard",
    "find_date": "2024-01-01"
  },
  "images": [ ... ],
  "references": [ ... ],
  "provenance": [ ... ]
}
```

---

### Create Coin

```http
POST /api/v2/coins
```

**Request Body**: `CreateCoinRequest`

```json
{
  "category": "imperial",
  "metal": "silver",
  "weight_g": 3.82,
  "diameter_mm": 18.0,
  "specific_gravity": 10.5,
  "issuer": "Augustus",
  "grading_state": "graded",
  "grade": "VF",
  "mint": "Lugdunum",
  "year_start": -2,
  "year_end": 4,
  "die_axis": 6,
  "grade_service": "ngc",
  "certification": "1234567-001",
  "acquisition_price": 450.00,
  "acquisition_source": "Heritage Auctions",
  "acquisition_date": "2023-06-15",
  "storage_location": "SlabBox1",
  "personal_notes": "Fine patina",
  "issue_status": "official",
  "obverse_die_id": "O-Aug-1",
  "reverse_die_id": "R-Aug-1",
  "find_spot": "Tetbury Hoard",
  "find_date": "2024-01-01",
  "images": [
    {
      "url": "/images/coins/1/obverse.jpg",
      "image_type": "obverse",
      "is_primary": true
    }
  ]
}
```

**Response**: `CoinResponse` (201 Created)

---

### Update Coin

```http
PUT /api/v2/coins/{id}
```

**Request Body**: `UpdateCoinRequest` (all fields optional, partial update supported)

```json
{
  "grade": "EF",
  "acquisition_price": 600.00,
  "personal_notes": "Upgraded from VF to EF after re-examination",
  "obverse_die_id": "O-Aug-2"
}
```

**Response**: `CoinResponse` (200 OK)

---

### Delete Coin

```http
DELETE /api/v2/coins/{id}
```

**Response**: `204 No Content`

---

## Vocabulary API (`/api/v2/vocab`)

**Router**: `src/infrastructure/web/routers/vocab.py`

Unified controlled vocabulary system (V3) for issuers, mints, denominations, and dynasties.

### Search Vocabulary

```http
GET /api/v2/vocab/search/{vocab_type}?q={query}
```

**Path Parameters**:
- `vocab_type`: One of `issuer`, `mint`, `denomination`, `dynasty`, `canonical_series`

**Query Parameters**:
- `q` (required): Search query
- `limit`: Max results (default: 10, max: 50)

**Response**: `List[VocabTermResponse]`

```json
[
  {
    "id": 1,
    "vocab_type": "issuer",
    "canonical_name": "Augustus",
    "nomisma_uri": "http://nomisma.org/id/augustus",
    "metadata": {
      "reign_start": -27,
      "reign_end": 14,
      "titles": ["Imperator", "Caesar", "Augustus"]
    }
  }
]
```

---

### Normalize Text to Vocabulary

```http
POST /api/v2/vocab/normalize
```

Converts raw text (e.g., "Aug", "AVGVSTVS") to canonical vocabulary term.

**Request Body**: `NormalizeRequest`

```json
{
  "raw": "AVGVSTVS",
  "vocab_type": "issuer",
  "context": {
    "category": "imperial",
    "year": -2
  }
}
```

**Response**: `NormalizeResponse`

```json
{
  "success": true,
  "term": {
    "id": 1,
    "vocab_type": "issuer",
    "canonical_name": "Augustus",
    "nomisma_uri": "http://nomisma.org/id/augustus"
  },
  "method": "exact",
  "confidence": 1.0,
  "needs_review": false,
  "alternatives": []
}
```

**Normalization Methods**:
- `exact`: Exact match (confidence: 1.0)
- `fts`: Full-text search match (confidence: 0.7-0.95)
- `nomisma`: Nomisma API lookup (confidence: 0.8-1.0)
- `llm`: LLM-assisted (confidence: varies)
- `manual`: User-assigned (confidence: 1.0)

---

### Sync Vocabulary from External Source

```http
POST /api/v2/vocab/sync/{vocab_type}
```

Syncs vocabulary terms from Nomisma.org or other external sources.

**Path Parameters**:
- `vocab_type`: `issuer`, `mint`, `denomination`, `dynasty`

**Response**: `SyncResponse`

```json
{
  "status": "success",
  "vocab_type": "issuer",
  "added": 150,
  "unchanged": 50,
  "errors": 0
}
```

---

### Bulk Normalize Coins

```http
POST /api/v2/vocab/bulk-normalize
```

Normalizes vocabulary fields for multiple coins.

**Request Body**: `BulkNormalizeRequest`

```json
{
  "coin_ids": [1, 2, 3, 4, 5],
  "vocab_types": ["issuer", "mint", "denomination"]
}
```

**Response**: Background task status

---

### Get Review Queue

```http
GET /api/v2/vocab/review
```

Returns vocabulary assignments that need manual review (low confidence or ambiguous). Data comes from `coin_vocab_assignments` (populated by bulk normalization).

**Query Parameters**:
- `status`: Filter by status (alias `status`) — `pending_review`, `assigned`, `approved`, `rejected` (default: `pending_review`)
- `limit`: Max items (default: 50, range 1–200)

**Response**: `List[ReviewQueueItem]`

```json
[
  {
    "id": 1,
    "coin_id": 23,
    "field_name": "issuer",
    "raw_value": "Aug.",
    "vocab_term_id": 1,
    "confidence": 0.65,
    "method": "fts",
    "suggested_name": "Augustus"
  }
]
```

---

### Approve/Reject Review Item

```http
POST /api/v2/vocab/review/{assignment_id}/approve
POST /api/v2/vocab/review/{assignment_id}/reject
```

**Response**: `{"status": "approved"|"rejected", "id": <assignment_id>}`

---

## Series API (`/api/v2/series`)

**Router**: `src/infrastructure/web/routers/series.py`

Series/collection management system.

### List Series

```http
GET /api/v2/series
```

**Response**: `SeriesListResponse`

```json
{
  "items": [
    {
      "id": 1,
      "name": "Augustus Denarii",
      "slug": "augustus-denarii",
      "series_type": "ruler",
      "target_count": 25,
      "is_complete": false,
      "slots": [
        {
          "id": 1,
          "series_id": 1,
          "slot_number": 1,
          "name": "RIC I 207",
          "status": "filled"
        }
      ]
    }
  ],
  "total": 1
}
```

---

### Get Series by ID

```http
GET /api/v2/series/{series_id}
```

**Response**: `SeriesResponse` (includes slots and memberships)

---

### Create Series

```http
POST /api/v2/series
```

**Request Body**: `SeriesCreate`

```json
{
  "name": "Twelve Caesars",
  "series_type": "ruler",
  "target_count": 12,
  "description": "Roman emperors from Julius Caesar to Domitian"
}
```

**Response**: `SeriesResponse` (201 Created)

**Series Types**:
- `ruler`: Organized by issuing authority
- `type`: Organized by coin type/reference
- `catalog`: Based on catalog series (RIC, Crawford)
- `custom`: User-defined grouping

---

### Add Coin to Series

```http
POST /api/v2/series/{series_id}/memberships
```

**Request Body**:

```json
{
  "coin_id": 23,
  "slot_id": 1
}
```

**Response**: `MembershipResponse`

---

### Update Slot Status

```http
PATCH /api/v2/series/{series_id}/slots/{slot_id}
```

**Request Body**:

```json
{
  "status": "filled"
}
```

**Slot Statuses**:
- `empty`: No coin assigned
- `filled`: Coin assigned
- `duplicate`: Multiple coins for this slot

---

### Delete Series

```http
DELETE /api/v2/series/{series_id}
```

**Response**: `204 No Content`

---

## Scraper API (`/api/v2/scrape`)

**Router**: `src/infrastructure/web/routers/scrape_v2.py`

Auction house scraper endpoints (Playwright-based).

### Scrape Auction Lot

```http
POST /api/v2/scrape?url={auction_url}
```

**Query Parameters**:
- `url` (required): Auction lot URL

**Supported Auction Houses**:
- Heritage Auctions (`coins.ha.com`)
- CNG (`cngcoins.com`)
- Biddr (`biddr.com`, `sixbid.com`, `coinarchives.com`)
- eBay (`ebay.com`)
- Agora Auctions (`agoraauctions.com`)

**Response**: `AuctionLotResponse`

```json
{
  "id": 1,
  "url": "https://coins.ha.com/itm/lot-12345",
  "source": "Heritage",
  "sale_name": "Long Beach Expo Auction",
  "lot_number": "12345",
  "hammer_price": 425.00,
  "estimate_low": 350.00,
  "estimate_high": 500.00,
  "currency": "USD",
  "issuer": "Augustus",
  "mint": "Lugdunum",
  "year_start": -2,
  "year_end": 4,
  "weight_g": 3.82,
  "diameter_mm": 18.0,
  "title": "Augustus AR Denarius, Lugdunum Mint",
  "description": "...",
  "grade": "VF",
  "primary_image_url": "https://...",
  "scraped_at": "2024-01-20T10:30:00Z"
}
```

---

### Link Scraped Data to Coin

```http
POST /api/v2/scrape/link
```

**Request Body**:

```json
{
  "auction_data_id": 1,
  "coin_id": 23
}
```

Links existing scraped auction data to a coin in the collection.

---

## Audit API (`/api/v2/audit`)

**Router**: `src/infrastructure/web/routers/audit_v2.py`

Audit system for comparing coins against auction data and reference catalogs.

### Run Audit on Coin

```http
POST /api/v2/coins/{coin_id}/audit
```

Runs audit strategies (attribution, physics, dating, grade) on a single coin.

**Response**: `AuditResultResponse`

```json
{
  "coin_id": 23,
  "status": "completed",
  "discrepancies": [
    {
      "field": "weight_g",
      "coin_value": "3.82",
      "reference_value": "3.85",
      "severity": "low",
      "status": "pending"
    }
  ],
  "enrichments": [
    {
      "field": "obverse_description",
      "suggested_value": "Laureate head of Augustus right",
      "confidence": 0.92,
      "source": "OCRE"
    }
  ]
}
```

---

### Get Audit Summary

```http
GET /api/v2/audit/summary
```

**Response**:

```json
{
  "pending_discrepancies": 12,
  "pending_enrichments": 25,
  "last_audit_run": "2024-01-20T14:30:00Z",
  "coins_audited": 110
}
```

---

### Audit Enrichments (Enrichment Opportunities)

Enrichment opportunities are computed on the fly from coins that have linked auction_data: where a coin field is empty and auction_data has a value, one opportunity is returned.

#### List Enrichments

```http
GET /api/v2/audit/enrichments
```

**Query Parameters**: `status`, `trust_level`, `coin_id`, `auto_applicable`, `page`, `per_page`

**Response**: `{ items: Enrichment[], total, page, per_page, pages }`

#### Bulk Apply Enrichments

```http
POST /api/v2/audit/enrichments/bulk-apply
```

**Request Body**: `{ applications: [{ coin_id, field_name, value }] }`

**Response**: `{ applied: number }`

#### Apply One Enrichment

```http
POST /api/v2/audit/enrichments/apply
```

**Request Body**: `{ coin_id, field_name, value }`

**Response**: `{ status, field, new_value }`

#### Auto-Apply Empty Fields

```http
POST /api/v2/audit/enrichments/auto-apply-empty
```

Applies all pending enrichments where the coin field is empty (server-side).

**Response**: `{ applied: number, applied_by_field?: Record }`

---

## Catalog API (`/api/catalog`)

**Router**: `src/infrastructure/web/routers/catalog.py`

Catalog lookup (OCRE/CRRO/RPC) and bulk enrichment.

### Bulk Enrich

```http
POST /api/catalog/bulk-enrich
```

**Request Body**: `{ coin_ids?: number[], missing_fields?: string[], reference_system?: string, category?: string, dry_run?: bool, max_coins?: int }`

**Response**: `{ job_id, total_coins, status, message? }`

### Job Status

```http
GET /api/catalog/job/{job_id}
```

**Response**: `{ job_id, status, progress, total, updated, conflicts, not_found, errors, results?, error_message?, started_at?, completed_at? }`

---

## Import API (`/api/v2/import`)

**Router**: `src/infrastructure/web/routers/import_v2.py`

### Enrich Preview (Catalog Lookup for Import)

```http
POST /api/v2/import/enrich-preview
```

**Request Body**: `{ references: string[], context?: Record }`

**Response**: `{ success, suggestions: Record<field, { value, source, confidence }>, lookup_results: Array<{ reference, status, system, confidence?, error?, external_url? }> }`

Used by EnrichmentPanel during import to fill fields from OCRE/CRRO/RPC based on detected references.

---

## LLM API (`/api/v2/llm`)

**Router**: `src/infrastructure/web/routers/llm.py`

LLM-powered enrichment endpoints. Coins can store pending suggestions in `llm_suggested_design`, `llm_suggested_attribution`, `llm_suggested_references`, and `llm_suggested_rarity`; `llm_enriched_at` records when suggestions were last produced. These fields are returned by **GET /api/v2/coins/{id}** when present.

### Expand Legend

```http
POST /api/v2/llm/legend/expand
```

**Request Body**:

```json
{
  "abbreviation": "IMP CAES AVGVSTVS DIVI F"
}
```

**Response**: `{ "expanded": "...", "confidence": 0.9, "cost_usd": 0.0, "model_used": "...", "cached": false }`

---

### Generate Description

```http
POST /api/v2/llm/generate-description
```

**Request Body**: `{ "coin_id": 23, "include_context": true }`

Generates catalog-style description using LLM based on coin data.

---

### Transcribe legends for coin

```http
POST /api/v2/llm/legend/transcribe/coin/{coin_id}
```

Runs legend transcription on the coin’s primary image and **saves** results as suggestions on the coin.

- **Path**: `coin_id` (int).
- **Behavior**: Resolves primary image (first `is_primary` or first image; supports `http(s)` URLs and local paths under `data/coin_images`). Calls the LLM transcribe capability and writes to `llm_suggested_design` (obverse_legend, reverse_legend, exergue, obverse_legend_expanded, reverse_legend_expanded), sets `llm_enriched_at`, then commits.
- **Errors**: `404` if the coin does not exist; `400` if the coin has no primary image or the image cannot be loaded.
- **Response**: Same shape as `POST /api/v2/llm/legend/transcribe` — `LegendTranscribeResponse` (obverse_legend, reverse_legend, exergue, expanded variants, uncertain_portions, confidence, cost_usd).

---

### Identify coin from its primary image

```http
POST /api/v2/llm/identify/coin/{coin_id}
```

Runs identify-from-image on the coin’s primary image and **saves** results as suggestions on the coin.

- **Path**: `coin_id` (int).
- **Behavior**: Resolves primary image as for transcribe. Calls the LLM identify capability; writes ruler→issuer, mint, denomination, and parsed date_range→year_start/year_end into `llm_suggested_attribution`; merges obverse/reverse descriptions into `llm_suggested_design`; merges `suggested_references` into `llm_suggested_references`; sets `llm_enriched_at`, then commits.
- **Errors**: `404` if the coin does not exist; `400` if the coin has no primary image or the image cannot be loaded.
- **Response**: Same shape as `POST /api/v2/llm/identify` — `CoinIdentifyResponse` (ruler, denomination, mint, date_range, obverse_description, reverse_description, suggested_references, confidence, cost_usd).

---

### LLM review queue

#### Get LLM suggestions for review

```http
GET /api/v2/llm/review
```

**Query**: `limit` (default 100, max 500).

**Response**: `{ "items": LLMSuggestionItem[], "total": number }`

Includes coins where any of `llm_suggested_references`, `llm_suggested_rarity`, `llm_suggested_design`, or `llm_suggested_attribution` is set. Each item includes:

- **Context**: `coin_id`, `issuer`, `denomination`, `mint`, `year_start`, `year_end`, `category`, `obverse_legend`, `reverse_legend`, `existing_references`, `enriched_at`.
- **Suggestions**: `suggested_references`, `validated_references`, `rarity_info`, **`suggested_design`** (LlmSuggestedDesign: obverse_legend, reverse_legend, exergue, obverse/reverse_description, expanded legends), **`suggested_attribution`** (LlmSuggestedAttribution: issuer, mint, denomination, year_start, year_end).

#### Dismiss LLM suggestions

```http
POST /api/v2/llm/review/{coin_id}/dismiss
```

**Query parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dismiss_references` | bool | true | Clear `llm_suggested_references` |
| `dismiss_rarity` | bool | true | Clear `llm_suggested_rarity` |
| **`dismiss_design`** | bool | true | Clear **`llm_suggested_design`** |
| **`dismiss_attribution`** | bool | true | Clear **`llm_suggested_attribution`** |

**Response**: `{ "status": "dismissed", "coin_id": number }`. At least one flag must be true.

#### Approve and apply LLM suggestions

```http
POST /api/v2/llm/review/{coin_id}/approve
```

Applies all pending suggestions to the coin and clears the suggestion columns.

- **Design**: from `llm_suggested_design` → obverse_legend, reverse_legend, exergue, obverse/reverse_description, obverse/reverse_legend_expanded (merge into coin design fields); then clear `llm_suggested_design`.
- **Attribution**: from `llm_suggested_attribution` → issuer, mint, denomination, year_start, year_end; then clear `llm_suggested_attribution`.
- **References / Rarity**: applied as before (references → reference_types + coin_references; rarity → rarity, rarity_notes).

**Response**: `{ "status": "approved", "coin_id": number, "applied_rarity": bool, "applied_references": number, "applied_design": bool, "applied_attribution": bool }`

---

## Provenance API (`/api/v2/provenance`)

**Router**: `src/infrastructure/web/routers/provenance.py`

Provenance tracking for ownership history.

### Get Coin Provenance

```http
GET /api/v2/provenance/coin/{coin_id}
```

**Response**: `List[ProvenanceEventResponse]`

```json
[
  {
    "id": 1,
    "coin_id": 23,
    "event_type": "auction",
    "event_date": "2023-06-15",
    "auction_house": "Heritage Auctions",
    "sale_series": "Long Beach Expo",
    "lot_number": "12345",
    "hammer_price": 425.00,
    "total_price": 510.00,
    "currency": "USD",
    "url": "https://..."
  }
]
```

---

### Add Provenance Event

```http
POST /api/v2/provenance/coin/{coin_id}/events
```

**Request Body**:

```json
{
  "event_type": "auction",
  "event_date": "2023-06-15",
  "auction_house": "Heritage Auctions",
  "lot_number": "12345",
  "hammer_price": 425.00,
  "url": "https://..."
}
```

**Event Types**:
- `auction`: Auction appearance
- `private_sale`: Private sale
- `dealer`: Dealer acquisition
- `collection`: From named collection
- `find`: Archaeological find
- `inheritance`: Inherited
- `gift`: Gift/donation
- `exchange`: Trade/exchange

---

## Die Study API (`/api/v2/die-study`)

**Router**: `src/infrastructure/web/routers/die_study.py`

Die study and die-linking functionality.

### List Die Links

```http
GET /api/v2/die-study/links
```

**Response**: Groups of coins sharing obverse or reverse dies.

---

### Create Die Link

```http
POST /api/v2/die-study/links
```

**Request Body**:

```json
{
  "coin_ids": [1, 2, 3],
  "die_side": "obverse",
  "notes": "Same die as RIC I 207"
}
```

---

## Statistics API

### Collection Statistics

```http
GET /api/v2/stats
```

**Response**:

```json
{
  "total_coins": 110,
  "total_value": 45000.00,
  "total_cost": 38000.00,
  "by_category": {
    "imperial": 75,
    "republic": 20,
    "provincial": 10,
    "byzantine": 5
  },
  "by_metal": {
    "silver": 60,
    "bronze": 35,
    "gold": 10,
    "billon": 5
  },
  "top_issuers": [
    { "name": "Augustus", "count": 15 },
    { "name": "Trajan", "count": 12 }
  ],
  "recent_acquisitions": [
    { "id": 108, "date": "2024-01-15", "price": 450.00 }
  ]
}
```

---

## Common Response Patterns

### Success Response

```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response

```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_type": "validation_error"
}
```

**HTTP Status Codes**:

| Code | Meaning |
|------|---------|
| 200 | OK - Successful GET/PUT/PATCH |
| 201 | Created - Successful POST |
| 204 | No Content - Successful DELETE |
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Schema validation failed |
| 500 | Server Error - Internal error |

---

## Query Optimization

### Pagination (Coins list)

The coins list uses `page` and `per_page` (not `skip`/`limit`). The frontend uses **infinite scroll**; there is no page-number UI. `page`/`per_page` are "chunk"/"offset" semantics for loading more items.

```http
GET /api/v2/coins?page=1&per_page=50
```

- `page`: Page number, 1-based (default: 1)
- `per_page`: Items per page (default: 20, max: 1000)

### Filtering

Use query parameters for filtering:

```http
GET /api/v2/coins?category=imperial&metal=silver&year_start=-27&year_end=14
```

### Sorting

```http
GET /api/v2/coins?sort_by=acquisition_date&sort_order=desc
```

---

## Authentication

**Current**: No authentication (single-user desktop app)

**Future**: JWT-based authentication planned for multi-user deployment.

---

## Rate Limiting

**Current**: No rate limiting (single-user desktop app)

**Scraper Endpoints**: Respectful delays built-in (2-5 seconds between requests)

---

## WebSocket Support

**Not Implemented**: Real-time updates via polling or SSE may be added in future.

---

## API Versioning

**Current Version**: V2

- V1 endpoints archived in `backend/v1_archive/`
- V2 endpoints use Clean Architecture (Domain/Application/Infrastructure)
- Breaking changes: New major version (V3)
- Non-breaking changes: Patch updates within V2

---

## Development Tools

### Swagger UI

Interactive API documentation with try-it-out functionality:

```
http://localhost:8000/docs
```

### ReDoc

Alternative API documentation with better readability:

```
http://localhost:8000/redoc
```

### OpenAPI Schema

Raw OpenAPI 3.0 schema:

```
http://localhost:8000/openapi.json
```

---

## Testing API Endpoints

### Using curl

```bash
# List coins
curl "http://localhost:8000/api/v2/coins?page=1&per_page=10"

# Get coin by ID
curl "http://localhost:8000/api/v2/coins/1"

# Create coin
curl -X POST "http://localhost:8000/api/v2/coins" \
  -H "Content-Type: application/json" \
  -d '{"category":"imperial","metal":"silver","weight_g":3.82,...}'

# Search vocabulary
curl "http://localhost:8000/api/v2/vocab/search/issuer?q=Augustus"

# Scrape auction lot
curl -X POST "http://localhost:8000/api/v2/scrape?url=https://coins.ha.com/itm/lot-12345"
```

### Using Python (requests)

```python
import requests

# List coins
response = requests.get("http://localhost:8000/api/v2/coins", params={
    "category": "imperial",
    "metal": "silver",
    "page": 1,
    "per_page": 20
})
coins = response.json()

# Create coin
coin_data = {
    "category": "imperial",
    "metal": "silver",
    "weight_g": 3.82,
    "diameter_mm": 18.0,
    "issuer": "Augustus",
    "grading_state": "graded",
    "grade": "VF"
}
response = requests.post("http://localhost:8000/api/v2/coins", json=coin_data)
created_coin = response.json()
```

### Using Frontend API Client

```typescript
import { apiClient } from '@/api/client' 

# List coins
const coins = await apiClient.get('/api/v2/coins', {
  params: { category: 'imperial', metal: 'silver' }
})

# Get coin by ID
const coin = await apiClient.get('/api/v2/coins/1')

# Create coin
const newCoin = await apiClient.post('/api/v2/coins', coinData)
```

---

## Critical Rules

### Port Configuration (MANDATORY)
- Backend: Port 8000
- Frontend: Port 3000
- Never increment ports

### Database Safety (MANDATORY)
- Backup required before schema changes
- Format: `coinstack_YYYYMMDD_HHMMSS.db`

### API Design Principles
- RESTful conventions
- Clean Architecture (routers → use cases → repositories)
- Repository interfaces (Protocols)
- Automatic transaction management via `get_db()` dependency
- Proper HTTP status codes
- Comprehensive error messages

---

**Previous:** [06-DATA-FLOWS.md](06-DATA-FLOWS.md) - Data flows
**Next:** [08-CODING-PATTERNS.md](08-CODING-PATTERNS.md) - Coding conventions