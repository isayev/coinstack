"""Comprehensive parser tests against real Excel data."""
import re
import sys
sys.path.insert(0, '.')

from app.services.excel_import import (
    parse_reign_years, parse_references, normalize_category, 
    normalize_metal, parse_obverse_reverse, parse_ngc_grade
)

print("=" * 80)
print("TESTING DATE PARSER (parse_reign_years)")
print("=" * 80)

date_tests = [
    # From Excel - BC dates
    ("2 BC-AD 4", (-2, 4)),
    ("54 BC", (-54, -54)),
    ("96 BC", (-96, -96)),
    ("27 BC-AD 14", (-27, 14)),
    
    # From Excel - AD dates  
    ("AD 130-133", (130, 133)),
    ("AD 14-15", (14, 15)),
    ("AD 140/141", (140, 141)),  # SLASH format!
    ("AD 150-151", (150, 151)),
    ("AD 159-60", (159, 160)),   # ABBREVIATED end year - should expand
    ("AD 33-34", (33, 34)),
    ("AD 75", (75, 75)),
    ("AD 97", (97, 97)),
    
    # From Ruled column
    ("AD 014-37", (14, 37)),     # Leading zeros
    ("AD 014–37", (14, 37)),     # En-dash!
    ("AD 054-68", (54, 68)),
    ("AD 069-79", (69, 79)),
    ("AD 081-96", (81, 96)),
    ("AD 193-217", (193, 217)),
    ("AD 268-270", (268, 270)),
    ("AD 379-395", (379, 395)),
    
    # Edge cases
    ("None", (None, None)),
    ("", (None, None)),
    (None, (None, None)),
]

errors = []
for input_val, expected in date_tests:
    result = parse_reign_years(input_val)
    status = "✓" if result == expected else "✗"
    if result != expected:
        errors.append(f"  {input_val}: got {result}, expected {expected}")
        print(f"  {status} '{input_val}' -> {result} (EXPECTED: {expected})")
    else:
        print(f"  {status} '{input_val}' -> {result}")

if errors:
    print(f"\n  ERRORS ({len(errors)}):")
    for e in errors:
        print(e)

print("\n" + "=" * 80)
print("TESTING METAL NORMALIZATION")
print("=" * 80)

metal_tests = [
    ("Silver", "silver"),
    ("Gold", "gold"),
    ("Bronze", "bronze"),
    ("Billon", "billon"),
    ("Bronze/Copper", "bronze"),  # Should handle slash
]

for input_val, expected in metal_tests:
    result = normalize_metal(input_val)
    status = "✓" if result == expected else "✗"
    print(f"  {status} '{input_val}' -> '{result}'" + (f" (EXPECTED: {expected})" if result != expected else ""))

print("\n" + "=" * 80)
print("TESTING CATEGORY NORMALIZATION")
print("=" * 80)

category_tests = [
    ("Roman Imperial", "imperial"),
    ("Roman Provincial", "provincial"),
    ("Roman Republic", "republic"),
    ("Roman Provincial ", "provincial"),  # Trailing space
]

for input_val, expected in category_tests:
    result = normalize_category(input_val)
    status = "✓" if result == expected else "✗"
    print(f"  {status} '{input_val}' -> '{result}'" + (f" (EXPECTED: {expected})" if result != expected else ""))

print("\n" + "=" * 80)
print("TESTING REFERENCE PARSING")
print("=" * 80)

ref_tests = [
    "RIC I 207",
    " RPC I 1701a",  # Leading space
    "Crawford 335/1c. Sydenham 611. Caecilia 46a.",  # Multiple with period separator
    "RIC 127",
    "RIC 129, Sear 8677",  # Comma separator
    "RIC 161 Rome p. 236, \"285\"; Sear 12665",  # Complex
    "RIC 177a; RIC IViii, 177a (s) Scarce, page 34 - Cohen 17",
    "BMCRE 227. RIC 160. RSC 966. SEAR II 5722.",
    "IC 704, V",  # Non-standard
    "Prieur 1165. RPC V.3, Online unassigned 87419.",
]

for ref_str in ref_tests:
    result = parse_references(ref_str)
    print(f"\n  Input: '{ref_str}'")
    print(f"  Parsed: {result}")

print("\n" + "=" * 80)
print("TESTING NGC GRADE PARSING")
print("=" * 80)

ngc_tests = [
    "Choice AU  Strike: 5/5 Surface: 4/5",
    "XF  Strike: 4/5 Surface: 3/5",
    "Choice F",
    "VF",
    "FV  Strike: 4/5 Surface: 3/5",  # Typo "FV" instead of "VF"
]

for ngc_str in ngc_tests:
    result = parse_ngc_grade(ngc_str)
    print(f"  '{ngc_str}' -> {result}")

print("\n" + "=" * 80)
print("TESTING OBVERSE/REVERSE PARSING")
print("=" * 80)

obv_rev_tests = [
    "CAESAR AVGVSTVS-DIVI F PATER PATRIAE, laureate head of Augustus right ",
    "C•MAL, Roma seated left on pile of shields",
    "Eagle standing left on scepter, with spread wings",  # No legend
]

for text in obv_rev_tests:
    legend, desc = parse_obverse_reverse(text)
    print(f"\n  Input: '{text[:60]}...'")
    print(f"  Legend: '{legend}'")
    print(f"  Description: '{desc[:60]}...' " if desc and len(desc) > 60 else f"  Description: '{desc}'")
