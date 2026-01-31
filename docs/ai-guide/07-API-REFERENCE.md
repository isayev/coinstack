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
- LLM Enrichments: `src/infrastructure/web/routers/llm_enrichment.py` (Phase 4)
- Catalog: `src/infrastructure/web/routers/catalog.py` (V1) & `catalog_v2.py` (V2)
- Scraper: `src/infrastructure/web/routers/scrape_v2.py`
- Vocab: `src/infrastructure/web/routers/vocab.py`
- Series: `src/infrastructure/web/routers/series.py`
- Provenance: `src/infrastructure/web/routers/provenance.py`
- Grading History: `src/infrastructure/web/routers/grading_history.py`
- Rarity Assessment: `src/infrastructure/web/routers/rarity_assessment.py`
- Concordance: `src/infrastructure/web/routers/concordance.py`
- External Links: `src/infrastructure/web/routers/external_links.py`
- Census Snapshot: `src/infrastructure/web/routers/census_snapshot.py`
- Market Prices: `src/infrastructure/web/routers/market.py` (Phase 5)
- Valuations: `src/infrastructure/web/routers/valuation.py` (Phase 5)
- Wishlist: `src/infrastructure/web/routers/wishlist.py` (Phase 5)
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

## Reference Concordance API (`/api/v2/concordance`)

Manages cross-reference linking between equivalent catalog references.
Example: RIC 207 = RSC 112 = BMC 298 = Cohen 169

### Get Concordance Group
```http
GET /api/v2/concordance/group/{group_id}
```
Returns all entries in a concordance group.

### Get Concordances for Reference
```http
GET /api/v2/concordance/reference/{reference_type_id}
```
Returns all concordance entries for a specific reference type.

### Find Equivalent References
```http
GET /api/v2/concordance/reference/{reference_type_id}/equivalents
```
Returns all reference_type_ids equivalent to the given reference.

### Create Concordance Group
```http
POST /api/v2/concordance/group
```
**Request Body**:
```json
{
  "reference_type_ids": [1, 2, 3],
  "source": "user",
  "confidence": 1.0,
  "notes": "Confirmed equivalence"
}
```

### Add to Concordance Group
```http
POST /api/v2/concordance/group/{group_id}/add
```
**Request Body**:
```json
{
  "reference_type_id": 4,
  "confidence": 0.9,
  "notes": "Probable match"
}
```

### Delete Concordance Entry
```http
DELETE /api/v2/concordance/entry/{entry_id}
```

### Delete Concordance Group
```http
DELETE /api/v2/concordance/group/{group_id}
```

---

## External Catalog Links API (`/api/v2/external-links`)

Manages links to external online catalog databases (OCRE, Nomisma, CRRO, RPC Online).

**Supported catalog sources**: `ocre`, `nomisma`, `crro`, `rpc_online`, `acsearch`, `coinproject`, `wildwinds`

### Get External Links for Reference
```http
GET /api/v2/external-links/reference/{reference_type_id}
```
Returns all external links for a reference type.

### Get External Link by Source
```http
GET /api/v2/external-links/reference/{reference_type_id}/{catalog_source}
```
Returns a specific external link.

### Get Pending Sync Links
```http
GET /api/v2/external-links/pending?limit=100
```
Returns links pending synchronization with external databases.

### Create External Link
```http
POST /api/v2/external-links
```
**Request Body**:
```json
{
  "reference_type_id": 1,
  "catalog_source": "ocre",
  "external_id": "ric.3.ant.42",
  "external_url": "http://numismatics.org/ocre/id/ric.3.ant.42"
}
```

### Update External Link
```http
PUT /api/v2/external-links/{link_id}
```

### Mark Link as Synced
```http
POST /api/v2/external-links/{link_id}/sync
```
**Request Body**:
```json
{
  "external_data": "{\"title\": \"RIC III 42\", ...}"
}
```

### Delete External Link
```http
DELETE /api/v2/external-links/{link_id}
```

---

## LLM Enrichments API (`/api/v2/llm-enrichments`)

Centralized LLM enrichment management with versioning, review workflow, prompt templates, feedback, and usage analytics.

### Enrichment Endpoints

#### Get Coin Enrichments
```http
GET /api/v2/llm-enrichments/coin/{coin_id}
```
**Query Parameters**: `capability`, `review_status`

#### Get Current Enrichment
```http
GET /api/v2/llm-enrichments/coin/{coin_id}/current/{capability}
```
Returns the current active enrichment for a coin/capability.

#### Check Cache
```http
GET /api/v2/llm-enrichments/cache?capability={capability}&input_hash={hash}
```
Check if an enrichment exists in cache by input hash.

#### Get Pending Review
```http
GET /api/v2/llm-enrichments/pending-review?capability={capability}&limit=100
```
Returns enrichments pending review.

#### Create Enrichment
```http
POST /api/v2/llm-enrichments
```
**Request Body**:
```json
{
  "coin_id": 1,
  "capability": "context_generate",
  "capability_version": 1,
  "model_id": "claude-3-sonnet",
  "input_hash": "abc123...",
  "output_content": "{...}",
  "confidence": 0.95,
  "needs_review": false,
  "cost_usd": 0.003
}
```

#### Update Review Status
```http
PUT /api/v2/llm-enrichments/{enrichment_id}/review
```
**Request Body**:
```json
{
  "review_status": "approved",
  "reviewed_by": "user",
  "review_notes": "Verified accuracy"
}
```

#### Supersede Enrichment
```http
POST /api/v2/llm-enrichments/{old_id}/supersede/{new_id}
```

#### Delete Enrichment
```http
DELETE /api/v2/llm-enrichments/{enrichment_id}
```

### Prompt Template Endpoints

#### List Templates
```http
GET /api/v2/llm-enrichments/templates/{capability}?include_deprecated=false
```

#### Get Active Template
```http
GET /api/v2/llm-enrichments/templates/{capability}/active?variant_name=default
```

#### Create Template
```http
POST /api/v2/llm-enrichments/templates
```
**Request Body**:
```json
{
  "capability": "context_generate",
  "version": 1,
  "system_prompt": "You are a numismatic expert...",
  "user_template": "Generate historical context for: {coin_description}",
  "variant_name": "default",
  "traffic_weight": 1.0
}
```

#### Deprecate Template
```http
POST /api/v2/llm-enrichments/templates/{template_id}/deprecate
```

### Feedback Endpoints

#### Get Enrichment Feedback
```http
GET /api/v2/llm-enrichments/feedback/enrichment/{enrichment_id}
```

#### Create Feedback
```http
POST /api/v2/llm-enrichments/feedback
```
**Request Body**:
```json
{
  "enrichment_id": 1,
  "feedback_type": "modified",
  "field_path": "issuer",
  "original_value": "Augustus",
  "corrected_value": "Octavian",
  "feedback_notes": "Pre-27 BC coinage"
}
```
Valid feedback types: `accepted`, `rejected`, `modified`, `hallucination`

#### List Feedback by Type
```http
GET /api/v2/llm-enrichments/feedback/type/{feedback_type}?skip=0&limit=100
```

### Usage Analytics Endpoints

#### Get Daily Usage
```http
GET /api/v2/llm-enrichments/usage/daily?start_date=2026-01-01&end_date=2026-01-31&capability={optional}&model_id={optional}
```

#### Get Usage Summary
```http
GET /api/v2/llm-enrichments/usage/summary?start_date=2026-01-01&end_date=2026-01-31
```
Returns aggregated usage by capability with total cost and requests.

#### Record Usage
```http
POST /api/v2/llm-enrichments/usage/record?date=2026-01-31&capability=context_generate&model_id=claude-3-sonnet&request_count=1&cost_usd=0.003
```

---

## Market Prices API (`/api/v2/market`)

Type-level market pricing aggregates based on auction data and dealer prices.

### List Market Prices
```http
GET /api/v2/market/prices
```
**Query Parameters**: `issuer`, `denomination`, `metal`, `skip`, `limit`

### Get Market Price by Attribution
```http
GET /api/v2/market/prices/by-attribution?attribution_key={key}
```

### Get Market Price
```http
GET /api/v2/market/prices/{id}
```

### Create Market Price
```http
POST /api/v2/market/prices
```
**Request Body**:
```json
{
  "attribution_key": "hadrian-denarius-rome",
  "issuer": "Hadrian",
  "denomination": "Denarius",
  "mint": "Rome",
  "metal": "silver",
  "catalog_ref": "RIC II 207",
  "avg_price_vf": 250.00,
  "avg_price_ef": 450.00,
  "median_price": 350.00
}
```

### Update/Delete Market Price
```http
PUT /api/v2/market/prices/{id}
DELETE /api/v2/market/prices/{id}
```

### Data Points

#### List Data Points
```http
GET /api/v2/market/prices/{price_id}/data-points
```
**Query Parameters**: `source_type`, `skip`, `limit`

#### Create Data Point
```http
POST /api/v2/market/prices/{price_id}/data-points
```
**Request Body**:
```json
{
  "price": 425.00,
  "currency": "USD",
  "source_type": "auction_realized",
  "date": "2026-01-15",
  "grade": "EF",
  "auction_house": "Heritage",
  "sale_name": "NYINC 2026",
  "lot_number": "3245",
  "confidence": "high"
}
```
Valid source types: `auction_realized`, `auction_unsold`, `dealer_asking`, `private_sale`, `estimate`

#### Get/Update/Delete Data Point
```http
GET /api/v2/market/data-points/{id}
PUT /api/v2/market/data-points/{id}
DELETE /api/v2/market/data-points/{id}
```

---

## Coin Valuations API (`/api/v2/coins/{coin_id}/valuations`)

Per-coin portfolio valuation snapshots with gain/loss tracking.

### List Valuations
```http
GET /api/v2/coins/{coin_id}/valuations
```

### Get Latest Valuation
```http
GET /api/v2/coins/{coin_id}/valuations/latest
```

### Create Valuation
```http
POST /api/v2/coins/{coin_id}/valuations
```
**Request Body**:
```json
{
  "valuation_date": "2026-01-31",
  "purchase_price": 350.00,
  "purchase_currency": "USD",
  "purchase_date": "2024-05-15",
  "current_market_value": 425.00,
  "value_currency": "USD",
  "market_confidence": "high",
  "comparable_count": 12,
  "gain_loss_usd": 75.00,
  "gain_loss_pct": 21.4,
  "valuation_method": "comparable_sales"
}
```
Valid confidence: `low`, `medium`, `high`, `strong`
Valid methods: `comparable_sales`, `dealer_estimate`, `insurance`, `user_estimate`, `llm_estimate`

### Get/Update/Delete Valuation
```http
GET /api/v2/coins/{coin_id}/valuations/{valuation_id}
PUT /api/v2/coins/{coin_id}/valuations/{valuation_id}
DELETE /api/v2/coins/{coin_id}/valuations/{valuation_id}
```

### Portfolio Summary
```http
GET /api/v2/valuations/portfolio-summary
```
Returns aggregate portfolio totals:
```json
{
  "total_coins": 150,
  "total_purchase_value": 45000.00,
  "total_current_value": 52500.00,
  "total_gain_loss_usd": 7500.00,
  "total_gain_loss_pct": 16.7
}
```

---

## Wishlist API (`/api/v2/wishlist`)

Acquisition targets, matched lots, and price alerts.

### Wishlist Items

#### List Wishlist Items
```http
GET /api/v2/wishlist
```
**Query Parameters**: `status`, `priority`, `category`, `skip`, `limit`
Valid statuses: `wanted`, `watching`, `bidding`, `acquired`, `cancelled`

#### Create Wishlist Item
```http
POST /api/v2/wishlist
```
**Request Body**:
```json
{
  "title": "Hadrian Denarius - Travel Series",
  "issuer": "Hadrian",
  "denomination": "Denarius",
  "category": "roman_imperial",
  "catalog_ref": "RIC II 207",
  "min_grade": "VF",
  "max_price": 500.00,
  "target_price": 350.00,
  "currency": "USD",
  "priority": 1,
  "notify_on_match": true
}
```

#### Get/Update/Delete Wishlist Item
```http
GET /api/v2/wishlist/{id}
PUT /api/v2/wishlist/{id}
DELETE /api/v2/wishlist/{id}
```

#### Mark as Acquired
```http
POST /api/v2/wishlist/{id}/mark-acquired
```
**Request Body**:
```json
{
  "coin_id": 123,
  "acquired_price": 325.00
}
```

### Wishlist Matches

#### List Matches
```http
GET /api/v2/wishlist/{item_id}/matches
```
**Query Parameters**: `include_dismissed`

#### Create Match
```http
POST /api/v2/wishlist/{item_id}/matches
```
**Request Body**:
```json
{
  "match_type": "auction_lot",
  "match_source": "heritage",
  "match_id": "lot-12345",
  "match_url": "https://coins.ha.com/...",
  "title": "Hadrian Denarius",
  "price": 325.00,
  "estimate_low": 300.00,
  "estimate_high": 400.00,
  "grade": "VF+",
  "match_score": 0.92,
  "match_confidence": "high"
}
```
Valid match types: `auction_lot`, `dealer_listing`, `ebay_listing`, `vcoins`
Valid confidence: `exact`, `high`, `medium`, `possible`

#### Update Match
```http
PUT /api/v2/wishlist/matches/{match_id}
```

#### Dismiss/Save Match
```http
POST /api/v2/wishlist/matches/{match_id}/dismiss
POST /api/v2/wishlist/matches/{match_id}/save
```

### Price Alerts

#### List Alerts
```http
GET /api/v2/price-alerts
```
**Query Parameters**: `status`, `trigger_type`, `skip`, `limit`

#### Create Alert
```http
POST /api/v2/price-alerts
```
**Request Body**:
```json
{
  "attribution_key": "hadrian-denarius-rome",
  "trigger_type": "price_below",
  "threshold_value": 300.00,
  "threshold_grade": "VF",
  "cooldown_hours": 24
}
```
Valid trigger types: `price_below`, `price_above`, `price_change_pct`, `new_listing`, `auction_soon`

#### Get/Update/Delete Alert
```http
GET /api/v2/price-alerts/{id}
PUT /api/v2/price-alerts/{id}
DELETE /api/v2/price-alerts/{id}
```

#### Trigger Alert Manually
```http
POST /api/v2/price-alerts/{id}/trigger
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