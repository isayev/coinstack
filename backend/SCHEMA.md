# CoinStack Database Schema Specification

> Developer reference for the CoinStack database schema.  
> Last updated: January 2026 | SQLite + SQLAlchemy 2.0

## Overview

CoinStack uses SQLite with SQLAlchemy ORM. The schema is designed around a central `Coin` entity with supporting tables for references, provenance, images, and audit tracking.

### Entity Relationship Diagram (Simplified)

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│    Mint     │────<│      Coin        │>────│   CoinImage     │
└─────────────┘     └──────────────────┘     └─────────────────┘
                           │ │ │                      │
                           │ │ │              ┌───────┴───────┐
                           │ │ └─────────────>│ImageAuctionSrc│
                           │ │                └───────────────┘
                    ┌──────┘ └──────┐
                    ▼                ▼
           ┌───────────────┐  ┌──────────────┐
           │ CoinReference │  │ProvenanceEvt │
           └───────┬───────┘  └──────────────┘
                   │
                   ▼
           ┌───────────────┐     ┌──────────────────┐
           │ ReferenceType │────<│ReferenceMatchAtmp│
           └───────────────┘     └──────────────────┘
                   │
                   ▼
           ┌───────────────┐
           │ PriceHistory  │
           └───────────────┘
```

---

## Core Tables

### `coins` (72 columns)

The central entity representing a coin specimen in the collection.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `created_at` | DATETIME | YES | Record creation timestamp |
| `updated_at` | DATETIME | YES | Last modification timestamp |
| **Classification** |
| `category` | ENUM(Category) | NO | Coin category (imperial, republic, etc.) |
| `sub_category` | VARCHAR(50) | YES | Sub-category (Julio-Claudian, Flavian) |
| `denomination` | VARCHAR(50) | NO | Coin type (Denarius, Antoninianus) |
| `metal` | ENUM(Metal) | NO | Metal composition |
| `series` | VARCHAR(100) | YES | Series name |
| **People** |
| `issuing_authority` | VARCHAR(100) | NO | Emperor/authority who issued |
| `portrait_subject` | VARCHAR(100) | YES | Person depicted on coin |
| `status` | VARCHAR(50) | YES | Political status at time |
| **Chronology** |
| `reign_start` | INTEGER | YES | Start of reign (year, negative=BC) |
| `reign_end` | INTEGER | YES | End of reign |
| `mint_year_start` | INTEGER | YES | Earliest possible mint year |
| `mint_year_end` | INTEGER | YES | Latest possible mint year |
| `is_circa` | BOOLEAN | NO | Date is approximate |
| `dating_certainty` | ENUM(DatingCertainty) | YES | Certainty level |
| `dating_notes` | VARCHAR(255) | YES | Dating explanation |
| **Physical Attributes** |
| `weight_g` | NUMERIC(6,3) | YES | Weight in grams (0.001g precision) |
| `diameter_mm` | NUMERIC(5,2) | YES | Diameter in mm |
| `diameter_min_mm` | NUMERIC(5,2) | YES | Minimum diameter (irregular flans) |
| `thickness_mm` | NUMERIC(4,2) | YES | Thickness in mm |
| `die_axis` | INTEGER | YES | Die axis (0-12h), validated by constraint |
| `orientation` | ENUM(Orientation) | YES | Photo orientation |
| `is_test_cut` | BOOLEAN | NO | Has diagnostic test cut |
| **Design: Obverse** |
| `obverse_legend` | VARCHAR(255) | YES | Obverse inscription |
| `obverse_legend_expanded` | TEXT | YES | Full expansion of abbreviations |
| `obverse_description` | TEXT | YES | Obverse design description |
| `obverse_symbols` | VARCHAR(255) | YES | Control marks, symbols |
| **Design: Reverse** |
| `reverse_legend` | VARCHAR(255) | YES | Reverse inscription |
| `reverse_legend_expanded` | TEXT | YES | Full expansion |
| `reverse_description` | TEXT | YES | Reverse design description |
| `reverse_symbols` | VARCHAR(255) | YES | Control marks, symbols |
| `exergue` | VARCHAR(100) | YES | Text below main design |
| **Mint** |
| `mint_id` | INTEGER FK | YES | Reference to mints table |
| `officina` | VARCHAR(20) | YES | Workshop identifier |
| `script` | VARCHAR(20) | YES | Script type (Latin, Greek) |
| **Grading** |
| `grade_service` | ENUM(GradeService) | YES | Grading service used |
| `grade` | VARCHAR(50) | YES | Grade (VF, EF, etc.) |
| `strike_quality` | INTEGER | YES | Strike score (1-5) |
| `surface_quality` | INTEGER | YES | Surface score (1-5) |
| `certification_number` | VARCHAR(50) | YES | NGC/PCGS cert number |
| `surface_issues` | JSON | YES | Array of surface issues |
| `eye_appeal` | VARCHAR(50) | YES | Eye appeal rating |
| `toning_description` | VARCHAR(255) | YES | Toning characteristics |
| `style_notes` | VARCHAR(255) | YES | Artistic style notes |
| **Acquisition** |
| `acquisition_date` | DATE | YES | Purchase date |
| `acquisition_price` | NUMERIC(10,2) | YES | Purchase price |
| `acquisition_currency` | VARCHAR(3) | YES | Currency code (USD) |
| `acquisition_source` | VARCHAR(100) | YES | Dealer/auction house |
| `acquisition_url` | VARCHAR(500) | YES | Original listing URL |
| **Valuation** |
| `estimate_low` | NUMERIC(10,2) | YES | Low estimate |
| `estimate_high` | NUMERIC(10,2) | YES | High estimate |
| `estimate_date` | DATE | YES | When estimated |
| `estimated_value_usd` | NUMERIC(10,2) | YES | Estimated value from comps |
| `insured_value` | NUMERIC(10,2) | YES | Insurance value |
| **Storage** |
| `holder_type` | ENUM(HolderType) | YES | Storage holder type |
| `storage_location` | VARCHAR(50) | YES | Physical location code |
| `for_sale` | BOOLEAN | NO | Listed for sale |
| `asking_price` | NUMERIC(10,2) | YES | Sale price if for_sale |
| **Research** |
| `rarity` | ENUM(Rarity) | YES | Rarity rating |
| `rarity_notes` | VARCHAR(255) | YES | Rarity explanation |
| `historical_significance` | TEXT | YES | Historical context |
| `die_match_notes` | TEXT | YES | Die study observations |
| `personal_notes` | TEXT | YES | Personal notes |
| `provenance_notes` | TEXT | YES | Provenance narrative |
| **Die Study** |
| `die_study_obverse_id` | INTEGER FK | YES | Self-ref to obverse die match |
| `die_study_reverse_id` | INTEGER FK | YES | Self-ref to reverse die match |
| `die_study_group` | VARCHAR(50) | YES | Die study group identifier |
| **LLM Enrichment** |
| `llm_enriched` | JSON | YES | LLM-generated metadata |
| `llm_enriched_at` | DATETIME | YES | When LLM enrichment occurred |
| **Auto-Merge Tracking** |
| `field_sources` | JSON | YES | Tracks field value sources |

**Constraints:**
- `ck_die_axis_range`: die_axis IS NULL OR (die_axis >= 0 AND die_axis <= 12)

**Indexes:**
- `ix_coins_id` (PK)
- `ix_coins_category`
- `ix_coins_sub_category`
- `ix_coins_denomination`
- `ix_coins_metal`
- `ix_coins_issuing_authority`
- `ix_coins_portrait_subject`

---

### `mints` (6 columns)

Mint locations for coin production.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `name` | VARCHAR(100) | NO | Mint name (unique) |
| `province` | VARCHAR(100) | YES | Roman province |
| `modern_location` | VARCHAR(100) | YES | Modern city/country |
| `latitude` | NUMERIC(9,6) | YES | Geographic latitude |
| `longitude` | NUMERIC(9,6) | YES | Geographic longitude |

**Relationships:**
- `coins.mint_id` → `mints.id`

---

### `coin_references` (11 columns)

Links coin specimens to catalog reference types.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `coin_id` | INTEGER FK | NO | Reference to coins |
| `reference_type_id` | INTEGER FK | NO | Reference to reference_types |
| `is_primary` | BOOLEAN | YES | Primary reference flag |
| `plate_coin` | BOOLEAN | YES | Is a plate coin |
| `position` | ENUM(ReferencePosition) | YES | Which side described |
| `variant_notes` | VARCHAR(255) | YES | Variant description |
| `page` | VARCHAR(20) | YES | Page reference |
| `plate` | VARCHAR(30) | YES | Plate number |
| `note_number` | VARCHAR(20) | YES | Footnote reference |
| `notes` | VARCHAR(255) | YES | Additional notes |

**Indexes:**
- `ix_coin_references_coin_id`
- `ix_coin_references_reference_type_id`

---

### `reference_types` (19 columns)

Catalog type records - single source of truth for reference data.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `created_at` | DATETIME | YES | Creation timestamp |
| `updated_at` | DATETIME | YES | Update timestamp |
| **Core Identification** |
| `system` | VARCHAR(20) | NO | Catalog system (ric, crawford, rpc) |
| `local_ref` | VARCHAR(100) | NO | Display reference (RIC I 207) |
| `local_ref_normalized` | VARCHAR(100) | NO | Normalized key (ric.1.207) |
| **Parsed Components** |
| `volume` | VARCHAR(20) | YES | Volume (I, II, 1) |
| `number` | VARCHAR(50) | YES | Number (207, 335/1c) |
| `edition` | VARCHAR(10) | YES | Edition (2 for RIC I(2)) |
| **External Catalog Link** |
| `external_id` | VARCHAR(100) | YES | OCRE/CRRO ID |
| `external_url` | VARCHAR(500) | YES | Full catalog URL |
| **Lookup Metadata** |
| `lookup_status` | VARCHAR(20) | YES | Status (pending, success, not_found) |
| `lookup_confidence` | NUMERIC(3,2) | YES | Match confidence (0.00-1.00) |
| `last_lookup` | DATETIME | YES | Last lookup timestamp |
| `source_version` | VARCHAR(50) | YES | OCRE snapshot version |
| `error_message` | TEXT | YES | Last error if any |
| **Cached Catalog Data** |
| `payload` | JSON | YES | Parsed JSON-LD summary |
| `citation` | TEXT | YES | Generated citation |
| `bibliography_refs` | JSON | YES | Related bibliography |

**Constraints:**
- `uq_ref_type`: UNIQUE(system, local_ref_normalized)

**Indexes:**
- `ix_reference_types_system`
- `ix_reference_types_local_ref_normalized`

---

### `reference_match_attempts` (10 columns)

Audit log for catalog matching attempts.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `reference_type_id` | INTEGER FK | YES | Reference to reference_types |
| `timestamp` | DATETIME | YES | Attempt timestamp |
| `query_sent` | TEXT | YES | Query sent to API |
| `context_used` | JSON | YES | Coin context (ruler, mint) |
| `result_status` | VARCHAR(20) | YES | Result (success, not_found, error) |
| `confidence` | NUMERIC(3,2) | YES | Match confidence |
| `candidates_returned` | INTEGER | YES | Number of candidates |
| `selected_candidate` | JSON | YES | Chosen candidate |
| `error_message` | TEXT | YES | Error details |

---

### `provenance_events` (20 columns)

Tracks ownership history and auction appearances.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `coin_id` | INTEGER FK | NO | Reference to coins |
| `event_type` | ENUM(ProvenanceType) | NO | Event type |
| `event_date` | DATE | YES | Event date |
| **Auction Details** |
| `auction_house` | VARCHAR(100) | YES | Auction house name |
| `sale_series` | VARCHAR(50) | YES | Sale series (Triton) |
| `sale_number` | VARCHAR(20) | YES | Sale number (XXIV) |
| `lot_number` | VARCHAR(20) | YES | Lot number |
| `catalog_reference` | VARCHAR(200) | YES | Full citation |
| **Pricing** |
| `hammer_price` | NUMERIC(10,2) | YES | Hammer price |
| `buyers_premium_pct` | NUMERIC(4,2) | YES | Buyer's premium % |
| `total_price` | NUMERIC(10,2) | YES | Total with premium |
| `currency` | VARCHAR(3) | YES | Currency code |
| **Dealer/Collection** |
| `dealer_name` | VARCHAR(100) | YES | Dealer name |
| `collection_name` | VARCHAR(100) | YES | Named collection |
| **Documentation** |
| `url` | VARCHAR(500) | YES | URL to listing |
| `receipt_available` | BOOLEAN | YES | Has receipt |
| `notes` | TEXT | YES | Additional notes |
| `sort_order` | INTEGER | YES | Display order |
| `auction_data_id` | INTEGER FK | YES | Link to auction_data |

---

### `coin_images` (16 columns)

Coin photographs with deduplication support.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `coin_id` | INTEGER FK | NO | Reference to coins |
| **Image Metadata** |
| `image_type` | ENUM(ImageType) | NO | Image type |
| `file_path` | VARCHAR(255) | NO | Storage path |
| `file_name` | VARCHAR(100) | YES | Original filename |
| `mime_type` | VARCHAR(50) | YES | MIME type |
| `size_bytes` | INTEGER | YES | File size |
| `width` | INTEGER | YES | Image width px |
| `height` | INTEGER | YES | Image height px |
| `is_primary` | BOOLEAN | YES | Primary image flag |
| `uploaded_at` | DATETIME | YES | Upload timestamp |
| **Deduplication** |
| `perceptual_hash` | VARCHAR(64) | YES | Perceptual hash |
| **Source Tracking** |
| `source_url` | VARCHAR(500) | YES | Original URL |
| `source_auction_id` | INTEGER FK | YES | Source auction_data |
| `source_house` | VARCHAR(50) | YES | Source house |
| `downloaded_at` | DATETIME | YES | Download timestamp |

**Indexes:**
- `ix_coin_images_coin_id`
- `ix_coin_images_perceptual_hash`
- `ix_coin_image_hash` (coin_id, perceptual_hash)

---

### `coin_tags` (3 columns)

Custom tags for coins.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `coin_id` | INTEGER FK | NO | Reference to coins |
| `tag` | VARCHAR(50) | NO | Tag name |

**Constraints:**
- `uq_coin_tag`: UNIQUE(coin_id, tag)

---

### `countermarks` (13 columns)

Countermarks on provincial coins.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `coin_id` | INTEGER FK | NO | Reference to coins |
| `countermark_type` | ENUM(CountermarkType) | NO | Type of countermark |
| `description` | VARCHAR(100) | NO | Countermark text |
| `expanded` | VARCHAR(255) | YES | Full expansion |
| `placement` | ENUM(CountermarkPlacement) | NO | Obverse/Reverse |
| `position` | VARCHAR(50) | YES | Position on coin |
| `condition` | ENUM(CountermarkCondition) | YES | Legibility |
| `authority` | VARCHAR(100) | YES | Applied by whom |
| `date_applied` | VARCHAR(50) | YES | Date applied |
| `image_url` | VARCHAR(500) | YES | Image URL |
| `image_side` | ENUM(CountermarkPlacement) | YES | Side shown |
| `notes` | VARCHAR(255) | YES | Notes |

---

### `auction_data` (74 columns)

Comprehensive auction record data for enrichment and price comparison.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `created_at` | DATETIME | YES | Creation timestamp |
| `updated_at` | DATETIME | YES | Update timestamp |
| `coin_id` | INTEGER FK | YES | Link to your coin |
| **Auction Identification** |
| `auction_house` | VARCHAR(100) | NO | House name |
| `sale_name` | VARCHAR(200) | YES | Sale name |
| `lot_number` | VARCHAR(50) | YES | Lot number |
| `source_lot_id` | VARCHAR(50) | YES | External lot ID |
| `auction_date` | DATE | YES | Auction date |
| `url` | VARCHAR(500) | NO | Listing URL (unique) |
| **Pricing** |
| `estimate_low` | NUMERIC(10,2) | YES | Low estimate |
| `estimate_high` | NUMERIC(10,2) | YES | High estimate |
| `estimate_usd` | INTEGER | YES | Single estimate |
| `hammer_price` | NUMERIC(10,2) | YES | Hammer price |
| `total_price` | NUMERIC(10,2) | YES | Total price |
| `buyers_premium_pct` | NUMERIC(4,2) | YES | Premium % |
| `currency` | VARCHAR(3) | YES | Currency code |
| `sold` | BOOLEAN | YES | Sold flag |
| `bids` | INTEGER | YES | Bid count |
| **Classification** |
| `ruler` | VARCHAR(200) | YES | Ruler name |
| `ruler_title` | VARCHAR(100) | YES | Title |
| `reign_dates` | VARCHAR(50) | YES | Reign dates |
| `denomination` | VARCHAR(100) | YES | Denomination |
| `metal` | VARCHAR(20) | YES | Metal |
| `mint` | VARCHAR(100) | YES | Mint |
| `struck_dates` | VARCHAR(100) | YES | Strike dates |
| `struck_under` | VARCHAR(200) | YES | Struck under |
| `categories` | JSON | YES | Categories array |
| **Physical** |
| `weight_g` | NUMERIC(6,3) | YES | Weight |
| `diameter_mm` | NUMERIC(5,2) | YES | Diameter |
| `thickness_mm` | NUMERIC(4,2) | YES | Thickness |
| `die_axis` | INTEGER | YES | Die axis (hours) |
| `die_axis_degrees` | INTEGER | YES | Die axis (degrees) |
| **Descriptions** |
| `title` | VARCHAR(1000) | YES | Full title |
| `description` | TEXT | YES | Full description |
| `obverse_description` | TEXT | YES | Obverse description |
| `reverse_description` | TEXT | YES | Reverse description |
| **Grading** |
| `grade` | VARCHAR(50) | YES | Grade |
| `grade_service` | VARCHAR(20) | YES | Service |
| `certification_number` | VARCHAR(50) | YES | Cert number |
| `condition_notes` | TEXT | YES | Condition notes |
| `strike_score` | VARCHAR(10) | YES | Strike score |
| `surface_score` | VARCHAR(10) | YES | Surface score |
| `numeric_grade` | INTEGER | YES | Sheldon grade |
| `grade_designation` | VARCHAR(50) | YES | Designation |
| **References** |
| `catalog_references` | JSON | YES | Parsed refs |
| `catalog_references_raw` | JSON | YES | Raw refs |
| `primary_reference` | VARCHAR(100) | YES | Primary ref |
| `reference_type_id` | INTEGER FK | YES | Reference type |
| **Provenance** |
| `provenance_text` | TEXT | YES | Provenance text |
| `pedigree_year` | INTEGER | YES | Earliest year |
| `has_provenance` | BOOLEAN | YES | Has provenance |
| `provenance_entries` | JSON | YES | Structured entries |
| **Photos** |
| `photos` | JSON | YES | Photo URLs |
| `primary_photo_url` | VARCHAR(500) | YES | Main photo |
| `photos_downloaded` | BOOLEAN | YES | Downloaded flag |
| **Source-Specific** |
| `sub_house` | VARCHAR(50) | YES | Biddr sub-house |
| `seller_username` | VARCHAR(100) | YES | eBay seller |
| `seller_feedback_score` | INTEGER | YES | Feedback score |
| `seller_feedback_pct` | NUMERIC(5,2) | YES | Feedback % |
| `seller_is_top_rated` | BOOLEAN | YES | Top rated flag |
| `seller_location` | VARCHAR(100) | YES | Seller location |
| `listing_type` | VARCHAR(50) | YES | Listing type |
| `shipping_cost` | NUMERIC(10,2) | YES | Shipping cost |
| `watchers` | INTEGER | YES | Watcher count |
| **Legends** |
| `obverse_legend` | VARCHAR(500) | YES | Obverse legend |
| `reverse_legend` | VARCHAR(500) | YES | Reverse legend |
| `exergue` | VARCHAR(200) | YES | Exergue text |
| `historical_notes` | TEXT | YES | Historical notes |
| **Metadata** |
| `scraped_at` | DATETIME | YES | Scrape timestamp |
| `raw_data` | JSON | YES | Raw response |
| **Campaign Tracking** |
| `campaign_scraped_at` | DATETIME | YES | Campaign scrape time |
| `campaign_successful` | BOOLEAN | YES | Campaign success |
| `campaign_error` | VARCHAR(500) | YES | Campaign error |

**Constraints:**
- `url` is UNIQUE

**Indexes:**
- `ix_auction_data_auction_house`
- `ix_auction_data_source_lot_id`
- `ix_auction_data_auction_date`
- `ix_auction_data_url`
- `ix_auction_data_reference_type_id`

---

### `price_history` (13 columns)

Price trends aggregated by reference type.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `created_at` | DATETIME | YES | Creation timestamp |
| `reference_type_id` | INTEGER FK | NO | Reference type |
| `period_date` | DATE | NO | Period start date |
| `period_type` | VARCHAR(20) | YES | Period type |
| **Statistics** |
| `min_price` | NUMERIC(10,2) | YES | Minimum price |
| `max_price` | NUMERIC(10,2) | YES | Maximum price |
| `median_price` | NUMERIC(10,2) | YES | Median price |
| `mean_price` | NUMERIC(10,2) | YES | Mean price |
| **Volume** |
| `comp_count` | INTEGER | YES | Total sales |
| `sold_count` | INTEGER | YES | Sold count |
| `passed_count` | INTEGER | YES | Unsold count |
| `median_price_vf_adj` | NUMERIC(10,2) | YES | VF-adjusted median |

**Constraints:**
- `uq_price_history_period`: UNIQUE(reference_type_id, period_date, period_type)

---

## Audit Tables

### `audit_runs` (16 columns)

Tracks audit execution sessions.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `started_at` | DATETIME | NO | Start time |
| `completed_at` | DATETIME | YES | Completion time |
| `scope` | VARCHAR(20) | NO | Scope (single, all, selected) |
| `coin_ids` | JSON | YES | Target coin IDs |
| **Progress** |
| `total_coins` | INTEGER | YES | Total to audit |
| `coins_audited` | INTEGER | YES | Audited count |
| `coins_with_issues` | INTEGER | YES | Issues found |
| **Results** |
| `discrepancies_found` | INTEGER | YES | Discrepancy count |
| `enrichments_found` | INTEGER | YES | Enrichment count |
| `images_downloaded` | INTEGER | YES | Images downloaded |
| `auto_accepted` | INTEGER | YES | Auto-accepted |
| `auto_applied` | INTEGER | YES | Auto-applied |
| **Status** |
| `status` | VARCHAR(20) | NO | Status |
| `error_message` | TEXT | YES | Error message |
| `config_snapshot` | JSON | YES | Config at runtime |

---

### `discrepancy_records` (20 columns)

Records data conflicts between coins and auction data.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `created_at` | DATETIME | NO | Creation time |
| `coin_id` | INTEGER FK | NO | Coin reference |
| `auction_data_id` | INTEGER FK | YES | Auction data ref |
| `audit_run_id` | INTEGER FK | YES | Audit run ref |
| `field_name` | VARCHAR(50) | NO | Field being compared |
| `current_value` | TEXT | YES | Current value |
| `auction_value` | TEXT | YES | Auction value |
| `similarity` | FLOAT | YES | Similarity score |
| `difference_type` | VARCHAR(30) | YES | Difference type |
| `comparison_notes` | TEXT | YES | Comparison notes |
| `normalized_current` | TEXT | YES | Normalized current |
| `normalized_auction` | TEXT | YES | Normalized auction |
| `source_house` | VARCHAR(50) | NO | Source house |
| `trust_level` | VARCHAR(20) | NO | Trust level |
| `auto_acceptable` | BOOLEAN | YES | Auto-accept flag |
| `status` | VARCHAR(20) | NO | Resolution status |
| `resolved_at` | DATETIME | YES | Resolution time |
| `resolution` | VARCHAR(20) | YES | Resolution action |
| `resolution_notes` | TEXT | YES | Resolution notes |

**Indexes:**
- `ix_discrepancy_status_trust` (status, trust_level)
- `ix_discrepancy_coin_status` (coin_id, status)

---

### `enrichment_records` (15 columns)

Tracks suggested field updates from auction data.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `created_at` | DATETIME | NO | Creation time |
| `coin_id` | INTEGER FK | NO | Coin reference |
| `auction_data_id` | INTEGER FK | YES | Auction data ref |
| `audit_run_id` | INTEGER FK | YES | Audit run ref |
| `field_name` | VARCHAR(50) | NO | Field to enrich |
| `suggested_value` | TEXT | NO | Suggested value |
| `source_house` | VARCHAR(50) | NO | Source house |
| `trust_level` | VARCHAR(20) | NO | Trust level |
| `confidence` | FLOAT | YES | Confidence score |
| `auto_applicable` | BOOLEAN | YES | Auto-apply flag |
| `status` | VARCHAR(20) | NO | Status |
| `applied_at` | DATETIME | YES | Application time |
| `applied` | BOOLEAN | YES | Applied flag |
| `rejection_reason` | TEXT | YES | Rejection reason |

**Indexes:**
- `ix_enrichment_status_trust` (status, trust_level)
- `ix_enrichment_coin_status` (coin_id, status)

---

### `field_history` (17 columns)

Audit trail for field changes with rollback support.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `coin_id` | INTEGER FK | NO | Coin reference |
| `field_name` | VARCHAR(50) | NO | Changed field |
| `old_value` | JSON | YES | Previous value |
| `new_value` | JSON | YES | New value |
| `old_source` | VARCHAR(50) | YES | Previous source |
| `new_source` | VARCHAR(50) | YES | New source |
| `old_source_id` | VARCHAR(100) | YES | Previous source ID |
| `new_source_id` | VARCHAR(100) | YES | New source ID |
| `change_type` | VARCHAR(20) | NO | Type (auto_fill, manual) |
| `changed_at` | DATETIME | NO | Change timestamp |
| `changed_by` | VARCHAR(100) | YES | Who made change |
| `batch_id` | VARCHAR(36) | YES | Batch UUID |
| `conflict_type` | VARCHAR(50) | YES | Conflict type |
| `trust_old` | INTEGER | YES | Old trust level |
| `trust_new` | INTEGER | YES | New trust level |
| `reason` | VARCHAR(500) | YES | Change reason |

**Indexes:**
- `ix_field_history_batch_coin` (batch_id, coin_id)
- `ix_field_history_coin_field` (coin_id, field_name)

---

### `image_auction_sources` (7 columns)

Tracks which auctions an image appeared in.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `created_at` | DATETIME | NO | Creation time |
| `image_id` | INTEGER FK | NO | Image reference |
| `auction_data_id` | INTEGER FK | NO | Auction reference |
| `source_url` | VARCHAR(500) | NO | Original URL |
| `source_house` | VARCHAR(50) | YES | Source house |
| `fetched_at` | DATETIME | YES | Fetch timestamp |

---

### `import_records` (13 columns)

Tracks provenance of imported coins.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Primary key |
| `coin_id` | INTEGER FK | NO | Coin reference |
| `source_type` | VARCHAR(50) | NO | Source type |
| `source_id` | VARCHAR(100) | YES | Source identifier |
| `source_url` | VARCHAR(500) | YES | Source URL |
| `imported_at` | DATETIME | NO | Import timestamp |
| `raw_data` | JSON | YES | Original data |
| `import_method` | VARCHAR(50) | YES | Import method |
| `imported_by` | VARCHAR(100) | YES | Importer |
| `file_name` | VARCHAR(255) | YES | Source file |
| `file_row` | INTEGER | YES | Source row |
| `enriched_at` | DATETIME | YES | Enrichment time |
| `enrichment_source` | VARCHAR(50) | YES | Enrichment source |

**Constraints:**
- `uq_import_source`: UNIQUE(source_type, source_id)

**Indexes:**
- `ix_import_source_lookup` (source_type, source_id)

---

## Enums

### Category
```python
GREEK = "greek"
CELTIC = "celtic"
REPUBLIC = "republic"
IMPERIAL = "imperial"
PROVINCIAL = "provincial"
JUDAEAN = "judaean"
BYZANTINE = "byzantine"
MIGRATION = "migration"
PSEUDO_ROMAN = "pseudo_roman"
OTHER = "other"
```

### Metal
```python
GOLD = "gold"
ELECTRUM = "electrum"
SILVER = "silver"
BILLON = "billon"
POTIN = "potin"
ORICHALCUM = "orichalcum"
BRONZE = "bronze"
COPPER = "copper"
LEAD = "lead"
AE = "ae"
UNCERTAIN = "uncertain"
```

### DatingCertainty
```python
EXACT = "exact"
NARROW = "narrow"
BROAD = "broad"
UNKNOWN = "unknown"
```

### GradeService
```python
NGC = "ngc"
PCGS = "pcgs"
SELF = "self"
DEALER = "dealer"
```

### HolderType
```python
NGC_SLAB = "ngc_slab"
PCGS_SLAB = "pcgs_slab"
FLIP = "flip"
CAPSULE = "capsule"
TRAY = "tray"
RAW = "raw"
```

### Rarity
```python
COMMON = "common"
SCARCE = "scarce"
RARE = "rare"
VERY_RARE = "very_rare"
EXTREMELY_RARE = "extremely_rare"
UNIQUE = "unique"
```

### Orientation
```python
OBVERSE_UP = "obverse_up"
REVERSE_UP = "reverse_up"
ROTATED = "rotated"
```

### ReferenceSystem
```python
RIC = "ric"
CRAWFORD = "crawford"
RPC = "rpc"
RSC = "rsc"
BMCRE = "bmcre"
SEAR = "sear"
SYDENHAM = "sydenham"
SNG = "sng"
BMC = "bmc"
HN = "hn"
OTHER = "other"
```

### ReferencePosition
```python
OBVERSE = "obverse"
REVERSE = "reverse"
BOTH = "both"
```

### ProvenanceType
```python
AUCTION = "auction"
PRIVATE_SALE = "private_sale"
DEALER = "dealer"
FIND = "find"
INHERITANCE = "inheritance"
GIFT = "gift"
COLLECTION = "collection"
EXCHANGE = "exchange"
```

### ImageType
```python
OBVERSE = "obverse"
REVERSE = "reverse"
EDGE = "edge"
SLAB = "slab"
DETAIL = "detail"
COMBINED = "combined"
OTHER = "other"
```

### CountermarkType
```python
HOST_VALIDATION = "host_validation"
VALUE_REDUCTION = "value_reduction"
MILITARY = "military"
CIVIC = "civic"
IMPERIAL = "imperial"
OTHER = "other"
```

### CountermarkCondition
```python
CLEAR = "clear"
PARTIAL = "partial"
WORN = "worn"
UNCERTAIN = "uncertain"
```

### CountermarkPlacement
```python
OBVERSE = "obverse"
REVERSE = "reverse"
```

### ImportSourceType
```python
HERITAGE = "heritage"
CNG = "cng"
EBAY = "ebay"
BIDDR = "biddr"
ROMA = "roma"
AGORA = "agora"
NGC = "ngc"
PCGS = "pcgs"
VCOINS = "vcoins"
MA_SHOPS = "ma_shops"
FILE = "file"
MANUAL = "manual"
```

---

## SQLAlchemy Notes

### Database Settings

```python
# Database URL format
DATABASE_URL = "sqlite:///./data/coinstack.db"

# Engine configuration
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite-specific
    echo=False,  # Set True for SQL logging
)
```

### Enum Handling (SQLAlchemy 2.0)

SQLAlchemy 2.0 stores enum **member names** (uppercase), not values:
- Database stores: `IMPERIAL`, `SILVER`, `OBVERSE_UP`
- Not the values: `imperial`, `silver`, `obverse_up`

### Session Management

```python
from app.database import get_db

# In FastAPI endpoints
def my_endpoint(db: Session = Depends(get_db)):
    coins = db.query(Coin).all()
```

---

## Migration Notes

### Adding Columns

SQLite doesn't support all ALTER TABLE operations. For adding columns:

```python
conn.execute(text("ALTER TABLE coins ADD COLUMN new_field VARCHAR(100)"))
```

### Removing Columns

SQLite doesn't support DROP COLUMN. Use table recreation:

1. Create new table with desired schema
2. Copy data from old table
3. Drop old table
4. Rename new table

### Adding Indexes

```python
conn.execute(text("CREATE INDEX IF NOT EXISTS ix_name ON table (column)"))
```

### Adding Unique Constraints

```python
conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_name ON table (col1, col2)"))
```
