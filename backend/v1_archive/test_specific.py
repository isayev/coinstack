import re

# Test BMC pattern
bmc_pattern = r"(BMCRE?)\s+(\d+)"
test_cases = ["BMC 837", "BMCRE 227", "BMC 736."]

print("Testing BMC pattern:")
for test in test_cases:
    m = re.match(bmc_pattern, test, re.IGNORECASE)
    print(f"  '{test}' -> {m.groups() if m else 'NO MATCH'}")

# Test Cohen pattern
cohen_pattern = r"(?:Cohen|Coh\.?|C)\s+(\d+)"
test_cases = ["Cohen 161", "Coh. 84", "C 161", "Coh"]

print("\nTesting Cohen pattern:")
for test in test_cases:
    m = re.match(cohen_pattern, test, re.IGNORECASE)
    print(f"  '{test}' -> {m.groups() if m else 'NO MATCH'}")

# Test the splitting issue
print("\nTesting splitting on 'RIC 41; Coh. 84.':")
ref_str = 'RIC 41; Coh. 84.'
parts = re.split(r"[;\n]|\.\s+", ref_str)
print(f"  Parts after split: {parts}")
