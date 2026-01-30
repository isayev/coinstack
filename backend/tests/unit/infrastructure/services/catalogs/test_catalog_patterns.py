import pytest
from src.infrastructure.services.catalogs.parser import parser, ParseResult

# Test Cases: (Raw Input, Expected System, Expected Volume, Expected Number, Expected Subtype/Variant)
# Use None if field expectation is irrelevant or None
TEST_CASES = [
    # RIC Standard
    ("RIC I 207", "ric", "I", "207", None),
    ("RIC 1 207", "ric", "I", "207", None),
    ("RIC I, 207", "ric", "I", "207", None), # Comma handling
    ("RIC I 207a", "ric", "I", "207", "a"),
    ("RIC 1 207 a", "ric", "I", "207", "a"), # Spacing variant
    
    # RIC Editions (The tricky part)
    ("RIC I (2nd ed) 1", "ric", "I.2", "1", None), 
    ("RIC I (2) 1", "ric", "I.2", "1", None),
    ("RIC I 2nd ed 1", "ric", "I.2", "1", None), # Bare edition
    ("RIC I² 207", "ric", "I.2", "207", None), # Superscript
    
    # RIC Volumes with parts
    ("RIC IV-1 123", "ric", "IV.1", "123", None),
    ("RIC IV.1 123", "ric", "IV.1", "123", None),
    ("RIC IV pt 1 123", "ric", "IV.1", "123", None),
    ("RIC IV 1 123", "ric", "IV.1", "123", None), # Bare part
    
    # Internet / Dealer Patterns
    ("RIC 2.3 430", "ric", "II.3", "430", None),
    ("RIC vol I 123", "ric", "I", "123", None), # Explicit "vol" handled by pre-normalization
    
    # RPC
    ("RPC I 1234", "rpc", "I", "1234", None),
    ("RPC IV.1 1234", "rpc", "IV.1", "1234", None), # Complex volume
    ("RPC 4.1 1234", "rpc", "IV.1", "1234", None),
    ("RPC I 3622C", "rpc", "I", "3622", "C"), # Case sensitivity / attached variant
    ("RPC I 3622 C", "rpc", "I", "3622", "C"),
    ("RPC online 1234", "rpc", None, "1234", None), # "online" stripped, becomes no-volume
    
    # Crawford (RRC)
    ("Crawford 44/5", "crawford", None, "44/5", None),
    ("RRC 44/5", "crawford", None, "44/5", None),
    
    # Edge Cases
    ("RIC 123", "ric", None, "123", None), # No volume
    
    # Emperor Names & Extra Text (Should be ignored)
    ("RIC VI 123 (Constantine I)", "ric", "VI", "123", None),
    ("RIC VI 123 - Constantine", "ric", "VI", "123", None),
    ("RIC VI, 123 - Constantine", "ric", "VI", "123", None),
    
    # Separators
    ("RIC VI: 123", "ric", "VI", "123", None),
    ("RIC VI, 123a", "ric", "VI", "123", "a"),
]

@pytest.mark.parametrize("raw, expected_system, expected_volume, expected_number, expected_subtype", TEST_CASES)
def test_catalog_patterns(raw, expected_system, expected_volume, expected_number, expected_subtype):
    """
    Data-driven test for catalog reference parsing.
    Verifies that various input formats normalize to the correct structured data.
    """
    result = parser.parse(raw)
    
    assert result.system == expected_system, f"System mismatch for '{raw}'"
    
    if expected_volume:
        assert result.volume == expected_volume, f"Volume mismatch for '{raw}'"
    
    if expected_number:
        assert result.number == expected_number, f"Number mismatch for '{raw}'"
        
    if expected_subtype:
        assert result.subtype == expected_subtype, f"Subtype mismatch for '{raw}'"