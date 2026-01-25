
from app.services.excel_import import parse_reign_years

def test_parse_reign_years():
    test_cases = [
        ("BC 27-14", (-27, -14)),
        ("BC 27", (-27, -27)),
        ("27 BC", (-27, -27)),
        ("27 BC-AD 14", (-27, 14)),
        ("AD 69-79", (69, 79)),
        ("159-158 BC", (-159, -158)),
    ]
    
    for input_str, expected in test_cases:
        result = parse_reign_years(input_str)
        print(f"Input: '{input_str}' -> Result: {result} | Expected: {expected}")
        if result != expected:
            print(f"FAIL: '{input_str}'")
        else:
            print(f"PASS: '{input_str}'")

if __name__ == "__main__":
    test_parse_reign_years()
