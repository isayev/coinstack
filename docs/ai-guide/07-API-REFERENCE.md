# API Reference

Base URL: `http://localhost:8000/api`

API Documentation: `http://localhost:8000/docs` (Swagger UI)

---

## Coins API

### List Coins

```
GET /api/coins
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 20 | Items per page (20, 50, 100, -1 for all) |
| `sort_by` | string | created_at | Sort field |
| `sort_dir` | string | desc | Sort direction (asc, desc) |
| `category` | string | - | Filter by category enum |
| `metal` | string | - | Filter by metal enum |
| `rarity` | string | - | Filter by rarity enum |
| `ruler` | string | - | Search issuing_authority |
| `mint` | string | - | Filter by mint name |
| `grade_min` | string | - | Minimum grade |
| `grade_max` | string | - | Maximum grade |
| `price_min` | number | - | Minimum acquisition price |
| `price_max` | number | - | Maximum acquisition price |
| `year_start` | int | - | Minimum reign year |
| `year_end` | int | - | Maximum reign year |
| `search` | string | - | Full-text search |

**Response:** `PaginatedCoins`

```json
{
  "items": [
    {
      "id": 1,
      "category": "imperial",
      "metal": "silver",
      "denomination": "Denarius",
      "issuing_authority": "Augustus",
      "grade": "VF",
      "acquisition_price": 450.00,
      "primary_image_url": "/images/coins/1/obverse.jpg"
    }
  ],
  "total": 110,
  "page": 1,
  "per_page": 20,
  "pages": 6
}
```

**Example:**

```bash
curl "http://localhost:8000/api/coins?category=imperial&metal=silver&page=1&per_page=20"
```

---

### Get Coin Detail

```
GET /api/coins/{id}
```

**Response:** `CoinDetail`

```json
{
  "id": 1,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "category": "imperial",
  "denomination": "Denarius",
  "metal": "silver",
  "issuing_authority": "Augustus",
  "portrait_subject": "Augustus",
  "reign_start": -27,
  "reign_end": 14,
  "weight_g": 3.82,
  "diameter_mm": 18.0,
  "die_axis": 6,
  "obverse_legend": "CAESAR AVGVSTVS DIVI F PATER PATRIAE",
  "obverse_description": "Laureate head right",
  "reverse_legend": "AVGVSTI F COS DESIG PRINC IVVENT",
  "reverse_description": "Gaius and Lucius standing",
  "grade_service": "ngc",
  "grade": "VF",
  "certification_number": "1234567-001",
  "acquisition_date": "2023-06-15",
  "acquisition_price": 450.00,
  "acquisition_source": "Heritage Auctions",
  "rarity": "common",
  "mint": {
    "id": 1,
    "name": "Lugdunum",
    "ancient_name": "Lugdunum",
    "modern_name": "Lyon"
  },
  "references": [
    {
      "id": 1,
      "system": "RIC",
      "volume": "I",
      "number": "207"
    }
  ],
  "images": [
    {
      "id": 1,
      "image_type": "obverse",
      "file_path": "/images/coins/1/obverse.jpg",
      "is_primary": true
    }
  ],
  "provenance_events": [],
  "tags": [],
  "countermarks": [],
  "auction_data": []
}
```

---

### Create Coin

```
POST /api/coins
```

**Request Body:** `CoinCreate`

```json
{
  "category": "imperial",
  "denomination": "Denarius",
  "metal": "silver",
  "issuing_authority": "Augustus",
  "weight_g": 3.82,
  "grade": "VF"
}
```

**Response:** `CoinDetail`

---

### Update Coin

```
PUT /api/coins/{id}
```

**Request Body:** `CoinUpdate` (all fields optional)

```json
{
  "grade": "EF",
  "current_value": 600.00
}
```

**Response:** `CoinDetail`

---

### Delete Coin

```
DELETE /api/coins/{id}
```

**Response:** `204 No Content`

---

### Get Coin Navigation

```
GET /api/coins/{id}/nav
```

Get previous and next coin IDs for navigation.

**Response:**

```json
{
  "prev_id": 45,
  "next_id": 47
}
```

---

## Import API

### Import from URL

```
POST /api/import/url
```

**Request Body:**

```json
{
  "url": "https://coins.ha.com/itm/lot-12345"
}
```

**Response:** `ImportPreview`

```json
{
  "parsed_data": {
    "category": "imperial",
    "denomination": "Denarius",
    "metal": "silver",
    "issuing_authority": "Augustus",
    "weight_g": 3.82,
    "obverse_legend": "CAESAR AVGVSTVS...",
    "reference_text": "RIC I 207"
  },
  "confidence": {
    "denomination": "high",
    "weight_g": "high",
    "issuing_authority": "medium"
  },
  "potential_duplicates": [
    {
      "id": 23,
      "issuing_authority": "Augustus",
      "denomination": "Denarius",
      "similarity_score": 0.85
    }
  ],
  "source_url": "https://coins.ha.com/itm/lot-12345"
}
```

---

### NGC Lookup

```
POST /api/import/ngc
```

**Request Body:**

```json
{
  "certification_number": "1234567-001"
}
```

**Response:** Similar to URL import preview

---

### Excel/CSV Import

```
POST /api/import/excel
```

**Request:** `multipart/form-data` with file

**Response:**

```json
{
  "rows_parsed": 50,
  "preview": [
    { "category": "imperial", "denomination": "Denarius", ... },
    ...
  ],
  "errors": [
    { "row": 15, "error": "Invalid metal value: 'gold-plated'" }
  ]
}
```

---

### Batch Import

```
POST /api/import/batch
```

**Request Body:**

```json
{
  "coins": [
    { "category": "imperial", "denomination": "Denarius", ... },
    { "category": "republic", "denomination": "Quinarius", ... }
  ]
}
```

**Response:**

```json
{
  "created": 48,
  "failed": 2,
  "errors": [
    { "index": 12, "error": "Duplicate detected" }
  ]
}
```

---

### Check Duplicates

```
POST /api/import/duplicates
```

**Request Body:**

```json
{
  "issuing_authority": "Augustus",
  "denomination": "Denarius",
  "weight_g": 3.82
}
```

**Response:**

```json
{
  "duplicates": [
    {
      "id": 23,
      "similarity_score": 0.92,
      "matching_fields": ["issuing_authority", "denomination", "weight_g"]
    }
  ]
}
```

---

## Audit API

### Start Audit

```
POST /api/audit/start
```

**Request Body:**

```json
{
  "coin_ids": [1, 2, 3]  // Optional, null = all coins
}
```

**Response:** `AuditRun`

```json
{
  "id": 5,
  "started_at": "2024-01-20T14:30:00Z",
  "completed_at": "2024-01-20T14:31:15Z",
  "coins_audited": 3,
  "discrepancies_found": 5,
  "enrichments_suggested": 8,
  "status": "completed"
}
```

---

### Get Audit Summary

```
GET /api/audit/summary
```

**Response:**

```json
{
  "pending_discrepancies": 12,
  "pending_enrichments": 25,
  "auto_merge_candidates": 8,
  "last_audit": {
    "id": 5,
    "started_at": "2024-01-20T14:30:00Z",
    "coins_audited": 110,
    "status": "completed"
  }
}
```

---

### List Discrepancies

```
GET /api/audit/discrepancies
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `coin_id` | int | Filter by coin |
| `status` | string | pending, accepted, rejected, ignored |
| `severity` | string | low, medium, high |
| `field_name` | string | Filter by field |

**Response:**

```json
{
  "items": [
    {
      "id": 1,
      "coin_id": 23,
      "field_name": "weight_g",
      "coin_value": "3.82",
      "auction_value": "3.85",
      "difference_type": "measurement",
      "severity": "low",
      "status": "pending"
    }
  ],
  "total": 12
}
```

---

### Resolve Discrepancy

```
POST /api/audit/discrepancies/{id}/resolve
```

**Request Body:**

```json
{
  "status": "accepted",  // or "rejected", "ignored"
  "note": "Auction house measurement more accurate"
}
```

**Response:** Updated `Discrepancy`

---

### List Enrichments

```
GET /api/audit/enrichments
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `coin_id` | int | Filter by coin |
| `status` | string | pending, applied, rejected |
| `source_type` | string | catalog, auction, llm |
| `min_confidence` | float | Minimum confidence |

**Response:**

```json
{
  "items": [
    {
      "id": 1,
      "coin_id": 23,
      "field_name": "obverse_description",
      "suggested_value": "Laureate head of Augustus right",
      "confidence": 0.92,
      "source_type": "catalog",
      "status": "pending"
    }
  ],
  "total": 25
}
```

---

### Apply Enrichment

```
POST /api/audit/enrichments/{id}/apply
```

**Response:** Updated `Enrichment`

---

### Reject Enrichment

```
POST /api/audit/enrichments/{id}/reject
```

**Response:** Updated `Enrichment`

---

### Auto-Merge

```
POST /api/audit/auto-merge
```

**Request Body:**

```json
{
  "coin_id": 23  // Optional, null = all coins
}
```

**Response:**

```json
{
  "merged": 15,
  "skipped": 10,
  "changes": [
    {
      "coin_id": 23,
      "field_name": "obverse_description",
      "old_value": null,
      "new_value": "Laureate head right"
    }
  ]
}
```

---

### Rollback Field Change

```
POST /api/audit/rollback/{history_id}
```

**Response:**

```json
{
  "success": true,
  "coin_id": 23,
  "field_name": "weight_g",
  "restored_value": "3.82"
}
```

---

## Catalog API

### Lookup Reference

```
GET /api/catalog/lookup
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `system` | string | RIC, Crawford, RPC |
| `volume` | string | Volume number |
| `number` | string | Reference number |

**Response:**

```json
{
  "found": true,
  "source": "OCRE",
  "data": {
    "title": "Denarius of Augustus",
    "denomination": "Denarius",
    "metal": "Silver",
    "authority": "Augustus",
    "mint": "Lugdunum",
    "date_range": "2 BC - AD 4",
    "obverse_legend": "CAESAR AVGVSTVS DIVI F PATER PATRIAE",
    "obverse_description": "Laureate head, right",
    "reverse_legend": "AVGVSTI F COS DESIG PRINC IVVENT",
    "reverse_description": "Gaius and Lucius Caesar standing front",
    "url": "http://numismatics.org/ocre/id/ric.1(2).aug.207"
  }
}
```

---

### Enrich Coin from Catalog

```
POST /api/catalog/enrich/{coin_id}
```

**Response:**

```json
{
  "enrichments_created": 5,
  "fields": ["obverse_description", "reverse_description", "mint_year_start", "mint_year_end", "exergue"]
}
```

---

### Bulk Enrich

```
POST /api/catalog/bulk-enrich
```

**Request Body:**

```json
{
  "coin_ids": [1, 2, 3, 4, 5]  // Optional, null = all with references
}
```

**Response:**

```json
{
  "job_id": "abc123",
  "status": "started",
  "total_coins": 5
}
```

---

### Get Job Status

```
GET /api/catalog/jobs/{job_id}
```

**Response:**

```json
{
  "job_id": "abc123",
  "status": "running",
  "progress": 3,
  "total": 5,
  "errors": []
}
```

---

## Scrape API

### Scrape Single URL

```
POST /api/scrape/url
```

**Request Body:**

```json
{
  "url": "https://coins.ha.com/itm/lot-12345"
}
```

**Response:** `AuctionData`

```json
{
  "id": 1,
  "auction_house": "Heritage",
  "sale_name": "Long Beach Expo",
  "lot_number": "12345",
  "auction_date": "2024-01-15",
  "title": "Augustus AR Denarius",
  "description": "...",
  "hammer_price": 425.00,
  "total_price": 510.00,
  "currency": "USD",
  "url": "https://coins.ha.com/itm/lot-12345",
  "image_urls": ["https://..."],
  "scraped_at": "2024-01-20T10:30:00Z"
}
```

---

### Batch Scrape

```
POST /api/scrape/batch
```

**Request Body:**

```json
{
  "urls": [
    "https://coins.ha.com/itm/lot-12345",
    "https://cngcoins.com/lot/456789"
  ]
}
```

**Response:**

```json
{
  "job_id": "batch-123",
  "status": "started",
  "total": 2
}
```

---

### Browser Scrape

```
POST /api/scrape/browser
```

For JavaScript-heavy sites requiring browser rendering.

**Request Body:**

```json
{
  "url": "https://example.com/auction/lot",
  "wait_selector": ".lot-details"  // Optional CSS selector to wait for
}
```

**Response:** `AuctionData`

---

## Auctions API

### List Auctions

```
GET /api/auctions
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `auction_house` | string | Filter by house |
| `linked` | bool | Filter linked/unlinked |
| `date_from` | date | Minimum auction date |
| `date_to` | date | Maximum auction date |
| `page` | int | Page number |
| `per_page` | int | Items per page |

**Response:** Paginated `AuctionData` list

---

### Get Comparables

```
GET /api/auctions/comparables/{coin_id}
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10 | Max results |

**Response:**

```json
{
  "coin_id": 23,
  "comparables": [
    {
      "id": 45,
      "auction_house": "CNG",
      "auction_date": "2023-12-01",
      "hammer_price": 425.00,
      "grade": "VF",
      "match_score": 0.88
    }
  ]
}
```

---

### Get Price Statistics

```
GET /api/auctions/stats
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `reference` | string | Reference (e.g., "RIC I 207") |
| `ruler` | string | Ruler name |
| `denomination` | string | Denomination |

**Response:**

```json
{
  "total_sales": 45,
  "avg_hammer": 380.50,
  "min_hammer": 180.00,
  "max_hammer": 850.00,
  "median_hammer": 350.00,
  "trend": "stable",
  "price_history": [
    { "date": "2023-06-01", "price": 350.00, "grade": "VF" },
    { "date": "2023-09-15", "price": 425.00, "grade": "EF" }
  ]
}
```

---

## Stats API

### Collection Statistics

```
GET /api/stats
```

**Response:**

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
  "top_rulers": [
    { "name": "Augustus", "count": 15 },
    { "name": "Trajan", "count": 12 }
  ],
  "recent_acquisitions": [
    { "id": 108, "date": "2024-01-15", "price": 450.00 }
  ],
  "price_distribution": {
    "0-100": 25,
    "100-250": 35,
    "250-500": 30,
    "500-1000": 15,
    "1000+": 5
  }
}
```

---

## Legend API

### Expand Legend

```
POST /api/legend/expand
```

**Request Body:**

```json
{
  "legend": "IMP CAES AVGVSTVS DIVI F PATER PATRIAE"
}
```

**Response:**

```json
{
  "original": "IMP CAES AVGVSTVS DIVI F PATER PATRIAE",
  "expanded": "Imperator Caesar Augustus Divi Filius Pater Patriae",
  "translation": "Emperor Caesar Augustus, Son of the Divine, Father of the Country",
  "abbreviations": [
    { "abbr": "IMP", "expansion": "Imperator" },
    { "abbr": "CAES", "expansion": "Caesar" },
    { "abbr": "DIVI F", "expansion": "Divi Filius" },
    { "abbr": "PATER PATRIAE", "expansion": "Pater Patriae" }
  ]
}
```

---

## Settings API

### Get Database Info

```
GET /api/settings/database
```

**Response:**

```json
{
  "path": "./data/coinstack.db",
  "size_mb": 15.4,
  "coin_count": 110,
  "auction_count": 250,
  "last_backup": "2024-01-19T10:00:00Z"
}
```

---

### Create Backup

```
POST /api/settings/backup
```

**Response:**

```json
{
  "success": true,
  "backup_path": "./backups/coinstack_20240120_103000.db",
  "size_mb": 15.4
}
```

---

### Export to CSV

```
GET /api/settings/export/csv
```

**Response:** CSV file download

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_type": "validation_error"
}
```

**Common Status Codes:**

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Schema validation failed |
| 500 | Server Error - Internal error |

---

**Previous:** [06-DATA-FLOWS.md](06-DATA-FLOWS.md) - Data flows  
**Next:** [08-CODING-PATTERNS.md](08-CODING-PATTERNS.md) - Coding conventions
