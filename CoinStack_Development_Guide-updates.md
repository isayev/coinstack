# CoinStack Development Guide

## Architecture Assessment & Future Development Recommendations

*For AI-assisted development with Claude or similar assistants*

---

## Executive Summary

The CoinStack specification is well-architected for a personal collection management app. The tech stack choices (FastAPI/SQLite/React) are appropriate for a single-user desktop application with LLM integration. This guide identifies enhancement opportunities organized by priority and provides specific guidance for AI-assisted implementation.

**Overall Rating**: Solid foundation. The data model captures most numismatic concepts correctly. Main opportunities lie in numismatic-specific refinements, LLM prompt engineering, and search optimization.

---

## 1. Data Model Refinements

### 1.1 Numeric Precision Issues

**Weight field precision is insufficient.**

Current: `Numeric(6, 2)` allows 9999.99g max with 2 decimal precision.

Problem: Ancient coin weights matter to 0.01g for die studies, but some references record to 0.001g. Additionally, the 9999.99g max is overkill—the heaviest ancient coins (large bronze medallions) rarely exceed 100g.

Recommendation: Change to `Numeric(6, 3)` for 999.999g max with 3 decimal precision. This covers all scenarios while allowing sub-centigram precision for detecting weight adjustments, fourees (plated coins), and die study comparisons.

**Die axis should be nullable integer with constraint.**

Current model stores die_axis as Integer without validation.

Problem: Die axis is recorded as clock positions 1-12 (or sometimes 0-12 where 12=0). String variations like "6h", "6 o'clock", "180°" create normalization headaches.

Recommendation: Store as Integer with check constraint 0-12. Handle the 12/0 equivalence at display time. Add a note field for non-standard orientations.

```
die_axis = Column(Integer)  # 1-12 clock position, NULL if unknown
__table_args__ = (CheckConstraint('die_axis >= 0 AND die_axis <= 12'),)
```

### 1.2 Missing Numismatic Fields

**Countermarks table is absent.**

Many provincial bronzes carry countermarks—official stamps applied after minting. These are significant for provenance, dating, and value.

Suggested structure:
- coin_id (FK)
- countermark_type (host validation, value reduction, military, etc.)
- countermark_description (text of stamp, e.g., "TI·C·A" for Tiberius)
- placement (obverse/reverse)
- condition (clear/partial/worn)

**Die linkage is underspecified.**

Current: `die_match_notes` as free text.

For serious die study work, you need actual die linkage records tracking which coins share obverse dies, reverse dies, or both. This enables hoard analysis and emissions sequencing.

Suggested approach:
- die_study_obverse_id (self-referential FK to "master" specimen for this obverse die)
- die_study_reverse_id (same for reverse)
- die_study_group (string identifier for the emission group)
- die_study_notes (text)

This allows queries like "show all coins sharing this obverse die" without parsing free text.

**Provenance needs richer auction fields.**

Current: auction_house and sale_name as separate fields.

Problem: Auction citations follow conventions. "CNG Triton XXIV, lot 567" should decompose into:
- auction_house: "CNG"
- sale_series: "Triton"  
- sale_number: "XXIV" or 24
- lot_number: "567"
- hammer_price vs total_price (buyer's premium is typically 20-22%)

The distinction between hammer and total matters for market analysis and insurance valuations.

**Reference table needs page/plate columns.**

Current: system, volume, number.

For scholarly citations, RIC entries often need plate references: "RIC VII Rome 123, pl. 5, no. 14". Add:
- page (string, allows "123-124")
- plate (string, allows "pl. 5" or "Taf. XII")
- note_number (string, for footnote references)

### 1.3 Enum Expansions

**Metal enum is missing key alloys.**

Current: gold, silver, billon, bronze, orichalcum, copper.

Missing:
- electrum (gold-silver alloy, common for early Greek)
- lead (used for tesserae, some tokens)
- potin (tin-rich bronze, Celtic and Alexandrian)
- brass (sometimes distinguished from orichalcum)
- ae (generic bronze/copper when composition unknown)

**Category enum could be more granular.**

Current: republic, imperial, provincial, byzantine, greek, other.

Consider adding:
- celtic (significant collecting category)
- judaean (distinct from provincial)
- sasanian (if you expand beyond Roman)
- migration_period (Ostrogothic, Vandal, etc.)

Alternatively, make category a two-level hierarchy: major_category + sub_category.

### 1.4 Date Handling Recommendations

**BC/AD representation needs careful thought.**

Current: reign_start/reign_end as integers, negative for BC.

This works but creates display complexity. Consider these edge cases:
- "27 BC - AD 14" (Augustus): reign_start=-27, reign_end=14
- "44 BC" (death of Caesar): single year, not range
- "circa 46-45 BC": needs uncertainty indication

Recommendations:
1. Keep integer storage but add display helper methods
2. Add is_circa boolean for approximate dates
3. Consider separate fields for certain/uncertain date ranges
4. Document the convention clearly: year 1 = AD 1, year -1 = 1 BC, no year 0

---

## 2. LLM Integration Refinements

### 2.1 Auction Listing Parser

The parse-listing feature is the highest-value LLM integration. Here's how to make it robust:

**Prompt engineering for extraction:**

Auction houses follow predictable patterns but with variations. Build the system prompt to handle:

1. **Standard catalog format** (CNG, Heritage):
   ```
   AUGUSTUS. 27 BC-AD 14. AR Denarius (18mm, 3.82g, 6h). Lugdunum mint. 
   Struck 2 BC-AD 4. CAESAR AVGVSTVS DIVI F PATER PATRIAE, laureate head right / 
   AVGVSTI F COS DESIG PRINC IVVENT, C L CAESARES below, Gaius and Lucius standing...
   RIC I 207. EF, attractive toning. Ex Gemini VII (10 January 2011), lot 547.
   ```

2. **European house format** (Künker, Gorny):
   Different field ordering, German abbreviations (Rs. = Rückseite = reverse)

3. **Brief lot format** (VCoins, MA-Shops):
   Less structured, missing fields common

**Extraction schema should be exhaustive:**

Return all possible fields even if null. Let the user confirm/reject rather than having the LLM guess which fields to populate.

**Few-shot examples in system prompt:**

Include 3-4 real auction listings with their correct extractions. This dramatically improves accuracy for edge cases.

**Confidence scoring:**

Have the LLM return confidence for each extracted field:
- high: explicit in text
- medium: inferred from context
- low: guessed from conventions

Display these to users so they know what to verify.

### 2.2 Legend Expansion

**Build an abbreviation dictionary first.**

Roman coin legends use standard abbreviations. Build a JSON reference:

```
{
  "IMP": "Imperator",
  "CAES": "Caesar", 
  "AVG": "Augustus",
  "AVGVSTVS": "Augustus",
  "P M": "Pontifex Maximus",
  "PM": "Pontifex Maximus",
  "TR P": "Tribunicia Potestate",
  "TRP": "Tribunicia Potestate",
  "COS": "Consul",
  "P P": "Pater Patriae",
  "PP": "Pater Patriae",
  "S C": "Senatus Consulto",
  "SC": "Senatus Consulto",
  ...
}
```

**Use LLM for context and unusual cases:**

The dictionary handles 80% of expansions. Use Claude for:
- Unusual abbreviations not in dictionary
- Context-dependent expansions (FIDES could expand differently based on reverse type)
- Translating the full expanded legend into English
- Explaining historical significance of titles

**Cache expansions aggressively:**

Store expanded legends in `obverse_legend_expanded` and `reverse_legend_expanded`. Only call LLM once per unique legend string.

### 2.3 Natural Language Search

**Map natural language to structured filters:**

The spec shows the right approach. Refine the prompt to handle numismatic terminology:

User: "denarii from the Flavian dynasty"
→ Filter: category=imperial, denomination=Denarius, issuing_authority IN (Vespasian, Titus, Domitian)

User: "coins with SC on reverse"
→ Filter: reverse_legend LIKE '%S C%' OR reverse_legend LIKE '%SC%'

User: "my most expensive Republican coins"
→ Filter: category=republic, ORDER BY acquisition_price DESC, LIMIT 10

**Build a numismatic synonym dictionary:**

- "aurei" → aureus (plural handling)
- "sestertii" → sestertius
- "Flavians" → Vespasian, Titus, Domitian
- "Julio-Claudian" → Augustus, Tiberius, Caligula, Claudius, Nero
- "adoptive emperors" → Nerva, Trajan, Hadrian, Antoninus Pius, Marcus Aurelius
- "silver" → metal=silver
- "gold" → metal=gold
- "brass" → metal=orichalcum (for Roman Imperial context)

### 2.4 Vision-Based Features (Future)

When you implement image analysis:

**Coin identification from photo:**

Pass coin images to Claude with a prompt requesting:
- Likely denomination and metal
- Portrait identification (if recognizable ruler type)
- Reverse type classification
- Suggested catalog search terms

**Do not use for grading:**

LLM grading suggestions are unreliable. Surface conditions, wear patterns, and die state require trained human judgment. At most, offer "apparent grade range" with heavy caveats.

**Image quality assessment:**

More useful: have Claude assess whether an image is suitable for documentation (adequate lighting, focus, scale reference visible).

---

## 3. Search & Query Optimization

### 3.1 Full-Text Search Implementation

SQLite's FTS5 is sufficient for ~100-1000 coins. Configure it to index:
- obverse_legend
- reverse_legend
- obverse_description
- reverse_description
- personal_notes
- historical_significance

**Tokenization matters:**

Roman legends have no spaces: "CAESARAVGVSTVS". Consider:
- Character n-gram tokenizer (trigrams work well)
- Or: pre-process legends to add spaces between words before indexing

### 3.2 Faceted Search Performance

For 110 coins, performance isn't a concern. But design for growth:

**Denormalize common filter values:**

Store materialized columns for frequent filters:
- ruler_normalized (lowercase, no diacritics)
- mint_name (from joined Mint table)
- primary_reference (formatted string like "RIC I 207")

**Pre-compute statistics:**

Run nightly (or on-change) jobs to update:
- Total collection value
- Count by category/metal/ruler
- Recent acquisitions

Store in a single stats JSON blob or dedicated stats table.

### 3.3 API Query Design

**Use cursor-based pagination for large result sets:**

Current: page/per_page (offset pagination).

For consistency and performance with filtering, consider cursor-based:
```
GET /api/coins?limit=20&after_id=45
```

This avoids "page drift" when items are added/removed.

**Support combined sort:**

Allow multi-field sorting for meaningful orderings:
```
?sort=issuing_authority,mint_year_start
?sort=-acquisition_price,issuing_authority
```

---

## 4. Frontend Architecture Notes

### 4.1 Form Design for Numismatic Data

**Tab organization makes sense, but consider this grouping:**

1. **Identity** (what is it): category, denomination, metal, series
2. **Attribution** (who/when/where): ruler, dates, mint, references
3. **Design** (what it shows): obverse, reverse, legends, descriptions
4. **Physical** (measurements): weight, diameter, die axis
5. **Grading** (condition): service, grade, surface notes
6. **Collection** (your data): acquisition, storage, valuation, notes

**Inline legend expansion:**

When user enters `obverse_legend`, show a small button to expand. Display expansion inline below the field, not in a modal. Let user edit the expansion before saving.

**Reference autocomplete:**

For the reference number field, if the user has selected system=RIC and volume=I, query a local RIC I database (if available) to suggest numbers as they type. This catches typos.

### 4.2 Image Gallery Considerations

**Support combined obverse+reverse images:**

Many auction photos show both sides in a single image. Your ImageType enum has COMBINED—make sure the gallery handles this gracefully.

**Image comparison mode:**

For die studies, allow side-by-side comparison of two coins' obverses (or reverses). Overlay mode with transparency slider helps spot die matches.

**Zoom capability:**

Small details matter. Implement a loupe/zoom on hover or a full-screen viewer with zoom (consider OpenSeadragon for deep zoom if you move to high-res IIIF images later).

### 4.3 Stats Dashboard Enhancements

**Visualizations that matter for collectors:**

1. **Value over time**: Line chart of cumulative acquisition cost
2. **Distribution by ruler**: Bar chart, top 10-15 rulers
3. **Metal composition**: Pie/donut chart
4. **Acquisition sources**: Where you buy (auction houses, dealers, etc.)
5. **Price per category**: Box plot showing price ranges by category
6. **Timeline coverage**: Which emperors/periods you have vs. gaps

**Interactive filtering from charts:**

Click a bar in "Distribution by ruler" → filter collection view to that ruler.

---

## 5. Development Workflow with AI Assistants

### 5.1 Effective Prompting Patterns

When working with Claude on this codebase:

**Always provide context:**

```
I'm working on CoinStack, a FastAPI/React app for managing an ancient Roman coin collection.
Current task: [specific feature]
Relevant models: [paste model code if needed]
Constraints: [any technical constraints]
```

**Use the spec as reference:**

```
Referring to the CoinStack spec section 3.2 (SQLAlchemy models), 
I need to add a Countermark model that...
```

**Request scaffolds, not complete code:**

For complex features, ask for:
1. Data model changes
2. API endpoint signatures
3. React component structure
4. Test case outlines

Then fill in implementation details yourself or in follow-up requests.

### 5.2 Incremental Development Pattern

**For each feature, follow this sequence:**

1. **Schema first**: Define or update Pydantic schemas
2. **Model changes**: SQLAlchemy model updates, migration
3. **CRUD layer**: Database operations
4. **API endpoint**: Router implementation
5. **Tests**: Unit and API tests
6. **Frontend hook**: TanStack Query hook
7. **Component**: React component
8. **Integration**: Wire up in pages

Ask the AI to help with one step at a time, validating each before proceeding.

### 5.3 Code Review Prompts

When asking for review:

```
Review this [component/endpoint/model] for:
1. Numismatic domain accuracy (are the field names/types appropriate?)
2. Edge cases (nulls, empty strings, boundary values)
3. Performance concerns
4. Type safety
```

### 5.4 Debugging Prompts

```
This endpoint returns [unexpected result] when given [input].
Expected: [what should happen]
Actual: [what happens]
Relevant code: [paste code]
Error message: [if any]
```

---

## 6. Testing Strategy Notes

### 6.1 Domain-Specific Test Cases

**Date handling edge cases:**

- BC/AD boundary: coin from "5 BC - AD 5" (crosses year 0)
- Single year: "44 BC" (assassination of Caesar)
- Unknown end: "193 AD - ?" (Pertinax, brief reign)
- Circa dates: "c. 46-45 BC"

**Reference parsing edge cases:**

- "RIC I² 207" (superscript edition number)
- "Crawford 335/1c" (sub-variants)
- "BMC 123, pl. 5.14" (plate reference)
- "RSC 89 = RIC I 207" (cross-references)

**Weight/measurement edge cases:**

- Very light coins: 0.05g (tiny bronze fractions)
- Heavy coins: 50g+ (large medallions)
- Missing measurements: null vs 0
- Irregular flans: diameter_min different from diameter

### 6.2 LLM Testing Approach

**Mock for unit tests:**

Never call real Claude API in automated tests. Mock responses for:
- Successful extraction with all fields
- Partial extraction (some fields missing)
- Failed extraction (gibberish input)
- Rate limiting / API errors

**Integration test suite (manual/optional):**

Maintain a separate test file with real auction listings from various houses. Run manually to validate extraction quality when prompts change.

---

## 7. Future Architecture Considerations

### 7.1 If Collection Grows Significantly

At 1000+ coins, consider:

**PostgreSQL migration:**

SQLite handles thousands of rows fine, but PostgreSQL offers:
- Better full-text search (tsvector)
- JSONB for flexible metadata
- Vector extensions (pgvector) for semantic search
- Concurrent access if you ever add multi-user

**Image storage:**

Move from filesystem to:
- S3-compatible storage (MinIO for self-hosted)
- Cloudflare R2 (cheap, fast)
- Properly serve thumbnails via image CDN

### 7.2 If Adding Multiple Users

**Authentication layer:**

Current spec is single-user. For multi-user:
- Add User model with collection ownership
- Implement auth (consider Clerk, Auth.js, or simple JWT)
- Add visibility controls (private/public/shared)
- Consider organization/family sharing

**Database multi-tenancy:**

Options:
1. Single database, filter by user_id (simplest)
2. Schema-per-user (PostgreSQL)
3. Database-per-user (complex)

Start with option 1; it's sufficient for family/small-group use.

### 7.3 Potential External Integrations

**Price data sources:**

- acsearch.info (historical auction results)
- CoinArchives (auction records)
- OCRE (Online Coins of the Roman Empire) - free reference data

**Reference catalogs:**

- OCRE API for RIC lookups
- Nomisma.org for linked data
- Build local RIC/RPC extracts for autocomplete

**Image recognition:**

- Custom model trained on coin types (ambitious but possible)
- Integration with existing coin identification services

---

## 8. Quick Reference: AI Assistant Instructions

When starting a development session with an AI assistant, paste this context block:

```
PROJECT: CoinStack - Ancient Roman coin collection manager
STACK: Python 3.12, FastAPI, SQLAlchemy 2.0, SQLite | React 18, TypeScript, TanStack Query, Zustand, shadcn/ui
DATABASE: SQLite file at backend/data/coinstack.db
KEY MODELS: Coin, Mint, CoinReference, ProvenanceEvent, CoinImage, CoinTag

CURRENT STATE: [describe what's implemented]
TODAY'S GOAL: [specific feature or fix]

CONVENTIONS:
- Enums for category, metal, grade_service, rarity, reference_system, provenance_type
- Dates as integers (negative for BC, positive for AD)
- Prices in USD unless acquisition_currency specified
- References follow catalog conventions (RIC, Crawford, RPC, RSC, BMCRE, Sear)

IMPORTANT DOMAIN NOTES:
- "ruler" = issuing_authority field (who issued the coin)
- "portrait" = portrait_subject field (whose face is depicted)
- Die axis recorded as clock hours 1-12
- Weight to 0.01g precision (some references use 0.001g)
```

---

## Appendix: Numismatic Terminology Quick Reference

For AI assistants unfamiliar with numismatics:

| Term | Meaning |
|------|---------|
| Obverse | Front of coin (usually portrait side) |
| Reverse | Back of coin |
| Legend | Text inscription around the edge |
| Exergue | Section below main design (often mint mark) |
| Die axis | Orientation between obverse and reverse dies |
| Flan | Blank metal disc before striking |
| Denarius | Standard Roman silver coin |
| Aureus | Standard Roman gold coin |
| Sestertius | Large Roman bronze coin |
| As | Small Roman bronze coin |
| RIC | Roman Imperial Coinage (standard reference) |
| Crawford | Reference for Roman Republican coins |
| RPC | Roman Provincial Coinage |
| NGC/PCGS | Major grading services |
| Fouree | Ancient counterfeit with base metal core |
| Die study | Research linking coins from same dies |
| Countermark | Official stamp added after minting |

---

*Document version: 1.0*  
*Generated: January 2025*  
*For use with CoinStack development*
