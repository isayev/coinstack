"""Test text normalization."""
import sys
sys.path.insert(0, '.')

from app.services.excel_import import normalize_text

test_cases = [
    # (input, expected_description)
    ("Roman Provincial\xa0", "NBSP at end -> stripped"),
    ("\xa0RPC I 1701a", "NBSP at start -> stripped"),
    ("AD 014–37", "En-dash -> hyphen"),
    ("Choice AU  Strike: 5/5", "Multiple spaces -> single"),
    ("KOΣΩN, Roman consul", "Greek letters preserved"),
    ("A•ALB•S•F-L•METEL", "Bullets preserved"),
    ("Æ25", "AE ligature preserved"),
    ("RIC V.1#\u202f13c", "Narrow NBSP -> space"),
    ('"Roman Coins"', "Special quotes -> ASCII"),
    ("  leading and trailing  ", "Strip both ends"),
    ("Normal text", "No change needed"),
    (None, "None input"),
    ("", "Empty string"),
]

print("Testing normalize_text():")
print("=" * 70)

for input_val, description in test_cases:
    result = normalize_text(input_val)
    print(f"\n{description}:")
    print(f"  Input:  {repr(input_val)}")
    print(f"  Output: {repr(result)}")

# Test with actual Excel data
print("\n" + "=" * 70)
print("Testing with actual Excel values:")
print("=" * 70)

import openpyxl
wb = openpyxl.load_workbook(r'c:\vibecode\coinstack\original-data\collection-v1.xlsx')
ws = wb.active

# Test specific cells with known issues
test_cells = [
    (3, 3),   # Category with NBSP
    (3, 14),  # Greek obverse text
    (4, 14),  # Obverse with bullets
    (6, 8),   # Ruled with en-dash
]

for row, col in test_cells:
    raw = ws.cell(row, col).value
    normalized = normalize_text(raw)
    print(f"\nRow {row}, Col {col}:")
    print(f"  Raw:        {repr(raw)[:70]}")
    print(f"  Normalized: {repr(normalized)[:70]}")
