# CoinStack Data Parsing & Conversion

## Overview

The `parse_collection.py` script provides robust data parsing and conversion for coin collection files (Excel/CSV).

## Features

- **Robust Parsing**: Handles various date formats, reference formats, and data types
- **Data Validation**: Validates required fields and data types
- **Error Reporting**: Detailed error and warning reporting
- **Data Normalization**: Normalizes categories, metals, and other fields
- **Reference Parsing**: Parses RIC, Crawford, RPC, Sydenham references
- **Date Parsing**: Handles BC/AD dates, reign years, mint years
- **NGC Grade Parsing**: Extracts strike and surface quality from NGC grades

## Usage

### Validate Only
```bash
python parse_collection.py collection-v1.xlsx --validate-only
```

### Convert and Save
```bash
python parse_collection.py collection-v1.xlsx -o output.json --pretty
```

### Quick Test
```bash
python test_parse.py
```

## Integration

The parsing script is integrated with the import service (`excel_import.py`). The import service uses `DataConverter` for robust data processing.

## Data Conversion Examples

### Date Parsing
- `"27 BC-AD 14"` → `reign_start: -27, reign_end: 14`
- `"AD 14-37"` → `reign_start: 14, reign_end: 37`
- `"54 BC"` → `reign_start: -54, reign_end: -54`

### Reference Parsing
- `"RIC I 207"` → `{system: "ric", volume: "I", number: "207"}`
- `"Crawford 335/1c"` → `{system: "crawford", number: "335/1c"}`
- `"RPC I 1701a"` → `{system: "rpc", volume: "I", number: "1701a"}`

### NGC Grade Parsing
- `"Choice AU  Strike: 5/5 Surface: 4/5"` → 
  - `grade: "Choice AU"`
  - `strike_quality: 5`
  - `surface_quality: 4`

### Obverse/Reverse Parsing
- `"CAESAR AVGVSTVS, laureate head right"` →
  - `obverse_legend: "CAESAR AVGVSTVS"`
  - `obverse_description: "laureate head right"`

## Statistics

From your collection:
- **Total rows**: 117
- **Successfully converted**: 110
- **Skipped**: 7 (empty rows)
- **Errors**: 0
- **Field coverage**: 23 fields per coin on average
