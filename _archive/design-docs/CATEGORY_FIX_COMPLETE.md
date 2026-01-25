# Category Mapping Fix - COMPLETE ✅

**Date**: 2026-01-25
**Issue**: Provincial coins incorrectly categorized as Imperial
**Status**: RESOLVED ✅

---

## 🐛 Root Cause

**Problem**: During V1 → V2 migration, category mapping was incomplete.

**V1 Categories** (uppercase, in `coins` table):
- `IMPERIAL` (102 coins)
- `PROVINCIAL` (7 coins)
- `REPUBLIC` (1 coin)

**V2 Categories** (should be lowercase with prefix, in `coins_v2` table):
- `roman_imperial`
- `roman_provincial`
- `roman_republic`

**What Went Wrong**:
- `IMPERIAL` → `roman_imperial` ✓ Correct
- `PROVINCIAL` → `roman_imperial` ✗ **WRONG** (should be `roman_provincial`)
- `REPUBLIC` → `roman_republic` ✓ Correct

All 7 provincial coins were incorrectly mapped to `roman_imperial`.

---

## ✅ Solution

Created and ran migration script: `fix_category_mapping.py`

### Script Actions:
1. **Identified** the 7 provincial coins from V1 table: IDs [2, 4, 5, 28, 33, 41, 56]
2. **Updated** their category in V2 from `roman_imperial` → `roman_provincial`
3. **Verified** all mappings are now correct

### Corrected Coins:
- Coin #2 (Tiberius)
- Coin #4 (Tiberius)
- Coin #5 (Tiberius)
- Coin #28 (Caracalla)
- Coin #33 (Elagabalus)
- Coin #41 (Maximinus I)
- Coin #56 (Decius)

---

## 📊 Verification

**Before Fix**:
```
V2 table:
  roman_imperial: 109 coins  ← 7 provincial coins mixed in
  roman_republic: 1 coin
  roman_provincial: 0 coins  ← MISSING!
```

**After Fix**:
```
V2 table:
  roman_imperial: 102 coins  ✓
  roman_provincial: 7 coins  ✓
  roman_republic: 1 coin     ✓
```

**API Verification**:
```bash
$ curl http://localhost:8000/api/v2/coins?category=roman_provincial
# Returns 7 coins with correct category
```

---

## 🎯 Category Schema

The complete category enum (as defined in domain schemas):

```python
CategorySchema = z.enum([
  'greek',              # Ancient Greek coins
  'roman_imperial',     # Roman Imperial coinage (27 BC - 476 AD)
  'roman_republic',     # Roman Republic (509 BC - 27 BC)
  'roman_provincial',   # Roman Provincial issues (local mints under Roman rule)
  'byzantine',          # Byzantine Empire (330-1453 AD)
  'medieval',           # Medieval European coinage
  'other'               # Other ancient/medieval coinage
])
```

---

## 🔍 How to Identify Categories

**Roman Imperial**:
- Minted in official Roman mints (Rome, Antioch, etc.)
- Imperial titulature on legends
- Standard Roman denominations (Denarius, Aureus, etc.)

**Roman Provincial**:
- Minted in provincial cities under Roman control
- Greek legends often present
- Local designs mixing Roman and local elements
- Irregular denominations
- Examples: Coins from Alexandria, Antioch, Ephesus, etc.

**Roman Republic**:
- Pre-27 BC coinage
- Republican magistrate names
- Before establishment of Empire

---

## 📁 Files Modified

1. ✅ `backend/src/infrastructure/scripts/fix_category_mapping.py` (NEW)
   - Migration script to correct categories
   - Includes verification logic

2. ✅ `backend/coinstack_v2.db` (UPDATED)
   - 7 coins updated from `roman_imperial` → `roman_provincial`

---

## 🚀 Result

All coins now have correct category classifications! The provincial coins (with Greek legends and local designs) are properly distinguished from imperial coinage.

**Frontend Impact**:
- Category filters now work correctly
- Provincial coins show correct category badge
- Collection statistics are accurate

---

## 💡 Prevention

For future migrations, ensure complete category mapping:

```python
CATEGORY_MAPPING = {
    'IMPERIAL': 'roman_imperial',
    'PROVINCIAL': 'roman_provincial',
    'REPUBLIC': 'roman_republic',
    # Add any other V1 categories here
}
```

Always verify category distribution after migration.

---

## ✅ Summary

**Root Cause**: Incomplete V1→V2 category mapping
**Fix**: Migration script to correct 7 provincial coins
**Verification**: All 110 coins now correctly categorized
**Result**: Categories now accurate for all coins! 🎉
