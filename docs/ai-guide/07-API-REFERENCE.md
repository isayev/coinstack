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
- Grading History: `src/infrastructure/web/routers/grading_history.py`
- Rarity Assessment: `src/infrastructure/web/routers/rarity_assessment.py`
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

### Coin Request Schema (Create/Update)

The request body for create/update includes all coin fields plus Phase 1 numismatic enhancements:

```typescript
interface CreateCoinRequest {
  // Required fields
  category: string;  // roman_imperial, greek, byzantine, etc.
  metal: string;     // gold, silver, bronze, etc.
  diameter_mm: number;
  issuer: string;
  grading_state: string;  // raw, slabbed, capsule, flip
  grade: string;          // VF, XF, AU, etc.

  // Optional base fields
  weight_g?: number;
  mint?: string;
  year_start?: number;   // Negative for BC
  year_end?: number;
  die_axis?: number;     // 0-12
  grade_service?: string;  // ngc, pcgs, etc.
  certification?: string;
  strike?: string;
  surface?: string;
  acquisition_price?: number;
  acquisition_source?: string;
  acquisition_date?: string;  // ISO date
  acquisition_url?: string;
  images?: Array<{ url: string; image_type: string; is_primary: boolean }>;
  denomination?: string;
  portrait_subject?: string;
  design?: {
    obverse_legend?: string;
    obverse_description?: string;
    reverse_legend?: string;
    reverse_description?: string;
    exergue?: string;
  };
  storage_location?: string;
  personal_notes?: string;
  rarity?: string;
  rarity_notes?: string;
  specific_gravity?: number;
  issue_status?: string;  // official, fourree, imitation, etc.
  obverse_die_id?: string;
  reverse_die_id?: string;
  find_spot?: string;
  find_date?: string;
  references?: Array<CatalogReferenceInput>;
  provenance?: Array<ProvenanceEntryRequest>;

  // Schema V3 Phase 1: Numismatic Enhancements (all optional)
  secondary_authority?: {
    name?: string;
    term_id?: number;
    authority_type?: string;  // magistrate, satrap, dynast, etc.
  };
  co_ruler?: {
    name?: string;
    term_id?: number;
    portrait_relationship?: string;  // self, consort, heir, etc.
  };
  moneyer_gens?: string;  // Republican moneyer family
  physical_enhancements?: {
    weight_standard?: string;  // attic, aeginetan, denarius_reformed, etc.
    expected_weight_g?: number;
    flan_shape?: string;  // round, irregular, oval, scyphate
    flan_type?: string;   // cast, struck, hammered
    flan_notes?: string;
  };
  secondary_treatments_v3?: {
    is_overstrike?: boolean;
    undertype_visible?: string;
    undertype_attribution?: string;
    has_test_cut?: boolean;
    test_cut_count?: number;
    test_cut_positions?: string;
    has_bankers_marks?: boolean;
    has_graffiti?: boolean;
    graffiti_description?: string;
    was_mounted?: boolean;
    mount_evidence?: string;
  };
  tooling_repairs?: {
    tooling_extent?: string;  // none, minor, moderate, significant, extensive
    tooling_details?: string;
    has_ancient_repair?: boolean;
    ancient_repairs?: string;
  };
  centering_info?: {
    centering?: string;  // well-centered, slightly_off, off_center
    centering_notes?: string;
  };
  die_study?: {
    obverse_die_state?: string;  // fresh, early, middle, late, worn, broken
    reverse_die_state?: string;
    die_break_description?: string;
  };
  grading_tpg?: {
    grade_numeric?: number;  // NGC/PCGS numeric grade (e.g., 35, 50, 65)
    grade_designation?: string;  // Fine Style, Choice, Gem
    has_star_designation?: boolean;
    photo_certificate?: boolean;
    verification_url?: string;
  };
  chronology?: {
    date_period_notation?: string;  // "c. 150-100 BC"
    emission_phase?: string;  // First Issue, Second Issue
  };
}
```

**Example: Create coin with Phase 1 fields:**
```json
{
  "category": "roman_imperial",
  "metal": "silver",
  "diameter_mm": 19,
  "issuer": "Hadrian",
  "grading_state": "slabbed",
  "grade": "XF",
  "grade_service": "ngc",
  "grading_tpg": {
    "grade_numeric": 45,
    "grade_designation": "Fine Style",
    "has_star_designation": true
  },
  "physical_enhancements": {
    "weight_standard": "denarius_reformed",
    "flan_shape": "round"
  },
  "centering_info": {
    "centering": "well-centered"
  }
}
```

**Update behavior:** For updates, Phase 1 fields preserve existing values if not provided. To clear a field, explicitly send the nested object with null values.

### Coin Response (Schema V3)

The coin response includes Phase 1 numismatic enhancements:

```typescript
interface CoinResponse {
  id: number;
  category: string;
  metal: string;
  dimensions: { weight_g, diameter_mm, die_axis, specific_gravity };
  attribution: { issuer, mint, year_start, year_end };
  grading: { grading_state, grade, service, certification_number, strike, surface };
  acquisition: { price, currency, source, date, url } | null;
  images: Array<{ url, image_type, is_primary }>;
  // ... (existing fields)

  // Schema V3 Phase 1: Numismatic Enhancements
  secondary_authority: {
    name: string | null;
    term_id: number | null;
    authority_type: string | null;  // magistrate, satrap, dynast, etc.
  } | null;
  co_ruler: {
    name: string | null;
    term_id: number | null;
    portrait_relationship: string | null;  // self, consort, heir, etc.
  } | null;
  moneyer_gens: string | null;
  physical_enhancements: {
    weight_standard: string | null;  // attic, aeginetan, etc.
    expected_weight_g: number | null;
    flan_shape: string | null;  // round, irregular, scyphate, etc.
    flan_type: string | null;  // cast, struck, hammered
    flan_notes: string | null;
  } | null;
  secondary_treatments_v3: {
    is_overstrike: boolean;
    undertype_visible: string | null;
    undertype_attribution: string | null;
    has_test_cut: boolean;
    test_cut_count: number | null;
    test_cut_positions: string | null;
    has_bankers_marks: boolean;
    has_graffiti: boolean;
    graffiti_description: string | null;
    was_mounted: boolean;
    mount_evidence: string | null;
  } | null;
  tooling_repairs: {
    tooling_extent: string | null;  // none, minor, moderate, significant, extensive
    tooling_details: string | null;
    has_ancient_repair: boolean;
    ancient_repairs: string | null;
  } | null;
  centering_info: {
    centering: string | null;  // well-centered, slightly_off, off_center, significantly_off
    centering_notes: string | null;
  } | null;
  die_study: {
    obverse_die_state: string | null;  // fresh, early, middle, late, worn, broken, repaired
    reverse_die_state: string | null;
    die_break_description: string | null;
  } | null;
  grading_tpg: {
    grade_numeric: number | null;  // NGC/PCGS numeric grades
    grade_designation: string | null;  // Fine Style, Choice, Gem, Superb Gem
    has_star_designation: boolean;
    photo_certificate: boolean;
    verification_url: string | null;
  } | null;
  chronology: {
    date_period_notation: string | null;  // "c. 150-100 BC", "late 3rd century AD"
    emission_phase: string | null;  // First Issue, Second Issue, etc.
  } | null;
}
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

## Grading History API (`/api/v2/coins/{coin_id}/grading-history`)

Tracks the complete TPG (Third Party Grading) lifecycle from initial submission through crossovers, regrades, and crack-outs.

### List Grading History
```http
GET /api/v2/coins/{coin_id}/grading-history
```
Returns all grading history entries for a coin, ordered by sequence.

### Get Current Grading
```http
GET /api/v2/coins/{coin_id}/grading-history/current
```
Returns the current (active) grading state.

### Create Grading Entry
```http
POST /api/v2/coins/{coin_id}/grading-history
```
**Body:**
```json
{
  "grading_state": "slabbed",
  "event_type": "initial",  // initial, crossover, regrade, crack_out
  "grade": "Ch XF",
  "grade_service": "ngc",
  "certification_number": "1234567-001",
  "grade_numeric": 45,
  "designation": "Fine Style",
  "has_star": true,
  "graded_date": "2024-01-15",
  "is_current": true
}
```

### Get/Update/Delete Entry
```http
GET /api/v2/coins/{coin_id}/grading-history/{entry_id}
PUT /api/v2/coins/{coin_id}/grading-history/{entry_id}
DELETE /api/v2/coins/{coin_id}/grading-history/{entry_id}
```

### Set Current Grading
```http
POST /api/v2/coins/{coin_id}/grading-history/{entry_id}/set-current
```
Marks an entry as the current grading state (clears is_current on others).

---

## Rarity Assessment API (`/api/v2/coins/{coin_id}/rarity-assessments`)

Tracks multi-source rarity assessments from catalogs, census data, and market analysis.

### List Rarity Assessments
```http
GET /api/v2/coins/{coin_id}/rarity-assessments
```
Returns all rarity assessments for a coin, with primary assessment indicated.

### Get Primary Assessment
```http
GET /api/v2/coins/{coin_id}/rarity-assessments/primary
```
Returns the primary rarity assessment.

### Create Rarity Assessment
```http
POST /api/v2/coins/{coin_id}/rarity-assessments
```
**Body:**
```json
{
  "rarity_code": "R2",  // C, S, R, R1-R5, RR, RRR, UNIQUE
  "rarity_system": "ric",  // ric, catalog, census, market_frequency
  "source_type": "catalog",  // catalog, census_data, auction_analysis, expert_opinion
  "source_name": "RIC II.1",
  "grade_conditional_notes": "R3 in XF+, R5 in MS",
  "census_total": 150,
  "census_this_grade": 12,
  "confidence": "high",  // high, medium, low
  "is_primary": true
}
```

### Get/Update/Delete Assessment
```http
GET /api/v2/coins/{coin_id}/rarity-assessments/{assessment_id}
PUT /api/v2/coins/{coin_id}/rarity-assessments/{assessment_id}
DELETE /api/v2/coins/{coin_id}/rarity-assessments/{assessment_id}
```

### Set Primary Assessment
```http
POST /api/v2/coins/{coin_id}/rarity-assessments/{assessment_id}/set-primary
```
Marks an assessment as primary (clears is_primary on others).

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