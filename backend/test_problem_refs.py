"""Test problematic reference patterns."""
import sys
sys.path.insert(0, '.')

from app.services.excel_import import parse_references, normalize_text

problem_refs = [
    "RIC IV, Part III, 27b",
    "RIC 7a",
    "RIC V.1# 13c",
    "RIC V.I 160.",
    "RIC V.II 118 (Cologne)",
    "RIC V.II 325.",
]

print("Testing problematic references:")
print("=" * 80)

for ref in problem_refs:
    normalized = normalize_text(ref)
    parsed = parse_references(normalized)
    print(f"\nOriginal: '{ref}'")
    print(f"Normalized: '{normalized}'")
    print(f"Parsed: {parsed}")
