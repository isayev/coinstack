# LLM Review Center Enhancement - Implementation Plan

## Overview

Enhanced the LLM review queue to display comprehensive coin information and validate catalog references against coin attributes. This enables users to make informed decisions when reviewing AI-suggested catalog references.

## Changes Made

### 1. Enhanced Backend Response Model

**File**: `backend/src/infrastructure/web/routers/llm.py`

#### New Models

- **`CatalogReferenceValidation`**: Validates suggested catalog references
  - Parsed components (catalog, number, volume)
  - Validation status: `matches`, `partial_match`, `mismatch`, `unknown`
  - Confidence score (0.0 to 1.0)
  - Match reason and existing reference comparison

- **Enhanced `LLMSuggestionItem`**: Now includes:
  - **Coin Details**: `mint`, `year_start`, `year_end`, `category`
  - **Legends**: `obverse_legend`, `reverse_legend`
  - **Existing References**: `existing_references` (for comparison)
  - **Validated References**: `validated_references` (with validation status)

### 2. Catalog Reference Parser

**Function**: `_parse_catalog_reference(ref_text: str)`

Parses catalog reference strings into structured components:
- Extracts catalog system (RIC, RSC, Cohen, Sear, etc.)
- Extracts volume (e.g., "IV.1", "III")
- Extracts number (e.g., "289c", "382")

**Supported Formats**:
- `RIC IV.1 289c` → `{catalog: "RIC", volume: "IV.1", number: "289c"}`
- `Cohen 382` → `{catalog: "Cohen", volume: None, number: "382"}`
- `RSC 382` → `{catalog: "RSC", volume: None, number: "382"}`
- `BMC III 234` → `{catalog: "BMC", volume: "III", number: "234"}`

### 3. Reference Validation Logic

**Function**: `_validate_catalog_reference(...)`

Validates suggested references by:
1. **Parsing** the reference into structured components
2. **Checking** if reference already exists in database
3. **Comparing** against coin attributes (issuer, mint, dates)
4. **Assigning** validation status and confidence score

**Validation Statuses**:
- `matches`: Reference already exists in DB (confidence: 1.0)
- `partial_match`: Successfully parsed, format valid (confidence: 0.6)
- `mismatch`: Format invalid or doesn't match coin (confidence: 0.0-0.4)
- `unknown`: Unable to parse (confidence: 0.5)

### 4. Enhanced Database Query

**Endpoint**: `GET /api/v2/llm/review`

Now fetches complete coin data:
```sql
SELECT 
    id, issuer, denomination, mint, category,
    year_start, year_end,
    obverse_legend, reverse_legend,
    llm_suggested_references, llm_suggested_rarity,
    llm_enriched_at
FROM coins_v2 
WHERE llm_suggested_references IS NOT NULL 
   OR llm_suggested_rarity IS NOT NULL
```

### 5. Frontend Type Updates

**File**: `frontend/src/types/audit.ts`

Updated `LLMSuggestionItem` interface to match backend:
- Added `CatalogReferenceValidation` type
- Added all new coin detail fields
- Added `validated_references` array

## Usage

### Backend API Response

```json
{
  "items": [
    {
      "coin_id": 32,
      "issuer": "Caracalla",
      "denomination": "Denarius",
      "mint": "Rome",
      "year_start": 217,
      "year_end": 217,
      "category": "roman_imperial",
      "obverse_legend": "ANTONINVS PIVS AVG GERM",
      "reverse_legend": "PM TR P XX COS IIII PP",
      "existing_references": ["RIC IVi 289c", "Cohen 382"],
      "suggested_references": ["RIC IV.1, 289c", "Sear 6846"],
      "validated_references": [
        {
          "reference_text": "RIC IV.1, 289c",
          "parsed_catalog": "RIC",
          "parsed_number": "289c",
          "parsed_volume": "IV.1",
          "validation_status": "matches",
          "confidence": 1.0,
          "match_reason": "Already exists in database: RIC IVI 289C",
          "existing_reference": "RIC IVI 289C"
        }
      ],
      "rarity_info": {
        "rarity_code": "S",
        "rarity_description": "Scarce",
        "source": "RIC IV.1 rates as S"
      }
    }
  ]
}
```

## Future Enhancements

### 1. Advanced Catalog Matching

Currently, validation is based on:
- Reference format parsing
- Database existence check
- Basic string matching

**Future improvements**:
- Cross-reference with external catalog databases (RIC online, etc.)
- Date range validation (check if reference matches coin's date range)
- Issuer/mint validation (verify reference corresponds to coin's issuer/mint)
- Confidence scoring based on multiple factors

### 2. Reference Resolution Service

Create a dedicated service that:
- Queries external catalog APIs
- Validates references against known catalog entries
- Provides detailed match information (page numbers, descriptions)

### 3. Bulk Validation

Add endpoint to validate multiple references at once:
```
POST /api/v2/llm/review/validate-batch
{
  "coin_id": 32,
  "references": ["RIC IV.1 289c", "Cohen 382"]
}
```

### 4. Reference Confidence Scoring

Enhance confidence calculation:
- **Format validity** (0.3): Can we parse it?
- **Database match** (0.4): Does it exist in our DB?
- **Attribute match** (0.3): Does it match coin's issuer/mint/dates?

## Testing

### Manual Testing

1. Generate context for a coin with missing references
2. Check `/api/v2/llm/review` endpoint
3. Verify:
   - All coin details are present
   - References are parsed correctly
   - Validation status is accurate
   - Existing references are shown

### Test Cases

1. **New Reference**: Coin without existing references
   - Should show `partial_match` or `unknown`
   - Confidence based on parse success

2. **Duplicate Reference**: Reference already in DB
   - Should show `matches`
   - Confidence: 1.0
   - `existing_reference` populated

3. **Invalid Format**: Malformed reference string
   - Should show `unknown` or `mismatch`
   - Low confidence

4. **Multiple References**: Coin with multiple suggestions
   - Each reference validated independently
   - Different validation statuses possible

## Implementation Notes

### Reference Parsing

The parser uses regex patterns to extract catalog information. Patterns are prioritized:
1. RIC (most common for Roman Imperial)
2. RSC, Cohen, Sear (common secondary references)
3. RRC, BMC, RPC (specialized catalogs)

### Validation Logic

Current validation is conservative:
- High confidence only for exact database matches
- Medium confidence for successfully parsed references
- Low confidence for unparseable or mismatched references

This can be enhanced with:
- External catalog lookups
- Date range validation
- Issuer/mint cross-referencing

## Related Files

- `backend/src/infrastructure/web/routers/llm.py` - Main implementation
- `backend/src/infrastructure/services/llm_service.py` - Citation parsing patterns
- `frontend/src/types/audit.ts` - TypeScript types
- `frontend/src/components/audit/LLMReviewTab.tsx` - UI component (needs update)

## Next Steps

1. **Update Frontend UI** (`LLMReviewTab.tsx`):
   - Display coin details (mint, dates, legends)
   - Show validation status for each reference
   - Color-code references by validation status
   - Display confidence scores

2. **Enhance Validation**:
   - Add date range checking
   - Add issuer/mint validation
   - Integrate external catalog APIs

3. **User Actions**:
   - Add "Accept Reference" button per reference
   - Add "Accept All Validated" bulk action
   - Show comparison view (existing vs. suggested)
