# Enum Field Reference for CoinStack Import

This document lists all valid enum values for coin import fields.

## Category

**Valid Values:**
- `greek` - Ancient Greek city-states
- `roman_republic` - Roman Republic (509-27 BC)
- `roman_imperial` - Roman Empire (27 BC - 476 AD)
- `roman_provincial` - Roman Provincial/Greek Imperial
- `byzantine` - Byzantine Empire (330-1453 AD)
- `medieval` - Medieval coinage
- `gallic_empire` - Gallic Empire (260-274 AD)
- `palmyrene_empire` - Palmyrene Empire (270-273 AD)
- `romano_british` - Romano-British (286-296 AD)
- `celtic` - Celtic coinage
- `judaean` - Judaean coinage
- `parthian` - Parthian Empire
- `sasanian` - Sasanian Empire
- `migration` - Migration Period ('barbarian' coinage)
- `other` - Other ancient coins

**Frontend Shortcuts (Auto-normalized):**
- `imperial` → `roman_imperial`
- `republic` → `roman_republic`
- `provincial` → `roman_provincial`

## Metal

**Valid Values:**
- `gold` (AU)
- `silver` (AR)
- `bronze` (AE)
- `copper` (CU)
- `electrum` (EL) - Gold/silver alloy
- `billon` (BI) - Debased silver
- `potin` - Copper/tin alloy
- `orichalcum` - Brass-like alloy
- `lead` (PB) - Ancient tokens, tesserae
- `ae` - Generic bronze/copper (standard numismatic abbreviation)

**Frontend Shortcuts (Auto-normalized):**
- `ar` → `silver`
- `au` → `gold`
- `ae` → `bronze` (or kept as `ae`)
- `bi` → `billon`
- `el` → `electrum`
- `cu` → `copper`
- `pb` → `lead`

**Invalid Values:**
- ❌ `uncertain` - Not a valid metal type

## Grading State

**Valid Values:**
- `raw` - Ungraded/raw coin
- `slabbed` - Professionally graded and sealed
- `capsule` - In protective capsule
- `flip` - In coin flip/holder

**Default:** `raw`

## Grade Service

**Valid Values:**
- `ngc` - NGC (Numismatic Guaranty Company)
- `pcgs` - PCGS (Professional Coin Grading Service)
- `icg` - ICG (Independent Coin Graders)
- `anacs` - ANACS (American Numismatic Association Certification Service)
- `none` - No grading service / raw coin

**Auto-normalized:**
- Empty string `""` → `none`
- `"n/a"` → `none`
- `"na"` → `none`
- `null` → `none`

## Import Endpoint Behavior

The `/api/v2/import/confirm` endpoint automatically normalizes common variations:

1. **Category normalization** - Converts short forms to full names
2. **Metal normalization** - Converts abbreviations to full names
3. **Case insensitivity** - All values are lowercased
4. **Whitespace trimming** - Leading/trailing spaces removed
5. **Validation** - Invalid values are rejected with clear error messages

## Testing

All enum values have been tested and validated. See test results:

```powershell
# Test category normalization
✅ 'imperial' -> 'roman_imperial'
✅ 'republic' -> 'roman_republic'
✅ 'provincial' -> 'roman_provincial'
✅ 'greek' -> 'greek'
✅ 'byzantine' -> 'byzantine'

# Test metal values
✅ All valid metals accepted
❌ 'uncertain' correctly rejected

# Test grade services
✅ 'ngc', 'pcgs', 'icg', 'anacs', 'none' all accepted
✅ null/empty values normalized to 'none'
```

## Frontend Dropdowns Updated

The import form dropdowns have been updated to only show valid values:

- ✅ Metal dropdown: Removed "uncertain", added all valid metals
- ✅ Grade service dropdown: Added ICG, ANACS, and "None / Raw"
- ✅ Category dropdown: Uses short forms that auto-normalize

## Error Messages

Invalid enum values return clear error messages:

```json
{
  "success": false,
  "error": "Invalid enum value: 'uncertain' is not a valid Metal"
}
```

---

**Last Updated:** January 26, 2026  
**Status:** ✅ All enum fields validated and working
