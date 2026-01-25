"""Comprehensive data parsing and conversion script for CoinStack.

This script processes Excel/CSV files and converts them to the CoinStack format
with validation, normalization, and detailed reporting.
"""
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import openpyxl
import csv
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class DataConverter:
    """Converts raw Excel/CSV data to CoinStack format."""
    
    def __init__(self):
        self.stats = {
            "total_rows": 0,
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "warnings": 0,
        }
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[str] = []
    
    def parse_reign_years(self, reign_str: str) -> Tuple[Optional[int], Optional[int]]:
        """Parse reign years from various formats."""
        if not reign_str:
            return None, None
        
        reign_str = str(reign_str).strip()
        
        # Patterns: "27 BC-AD 14", "AD 14-37", "54 BC", "14-37"
        patterns = [
            (r"(-?\d+)\s*BC\s*-\s*AD\s*(\d+)", True),  # "27 BC-AD 14"
            (r"AD\s*(\d+)\s*-\s*(\d+)", False),  # "AD 14-37"
            (r"(-?\d+)\s*-\s*(\d+)", True),  # "14-37" or "-27-14"
            (r"(-?\d+)\s*BC", True),  # "54 BC"
            (r"AD\s*(\d+)", False),  # "AD 14"
            (r"(\d+)", False),  # "14"
        ]
        
        for pattern, check_bc in patterns:
            match = re.search(pattern, reign_str)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    start = int(groups[0])
                    end = int(groups[1])
                    if check_bc and "BC" in reign_str and start > 0:
                        start = -start
                    return start, end
                elif len(groups) == 1:
                    year = int(groups[0])
                    if check_bc and "BC" in reign_str and year > 0:
                        year = -year
                    return year, year
        
        return None, None
    
    def parse_mint_years(self, minted_str: str) -> Tuple[Optional[int], Optional[int]]:
        """Parse mint years (same logic as reign years)."""
        return self.parse_reign_years(minted_str)
    
    def normalize_category(self, category: str) -> Optional[str]:
        """Normalize category to enum value."""
        if not category:
            return None
        
        category_lower = str(category).lower().strip()
        
        if "imperial" in category_lower:
            return "imperial"
        elif "republic" in category_lower:
            return "republic"
        elif "provincial" in category_lower:
            return "provincial"
        elif "byzantine" in category_lower:
            return "byzantine"
        elif "greek" in category_lower:
            return "greek"
        elif category_lower:
            return "other"
        
        return None
    
    def normalize_metal(self, metal: str) -> Optional[str]:
        """Normalize metal to enum value."""
        if not metal:
            return None
        
        metal_lower = str(metal).lower().strip()
        
        if "gold" in metal_lower or metal_lower == "au":
            return "gold"
        elif "silver" in metal_lower or metal_lower == "ar":
            return "silver"
        elif "bronze" in metal_lower or metal_lower == "ae":
            return "bronze"
        elif "billon" in metal_lower:
            return "billon"
        elif "orichalcum" in metal_lower:
            return "orichalcum"
        elif "copper" in metal_lower:
            return "copper"
        
        return None
    
    def parse_obverse_reverse(self, full_text: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse obverse/reverse text into legend and description."""
        if not full_text:
            return None, None
        
        full_text = str(full_text).strip()
        
        # Look for pattern: "LEGEND, description" where legend is short and uppercase
        if "," in full_text:
            parts = full_text.split(",", 1)
            potential_legend = parts[0].strip()
            description = parts[1].strip()
            
            # Check if first part looks like a legend (short, mostly uppercase, abbreviations)
            if (len(potential_legend) < 80 and 
                potential_legend.isupper() and 
                any(char in potential_legend for char in ["•", " ", "-", "."])):
                return potential_legend, description
        
        # No clear legend, treat as description only
        return None, full_text
    
    def parse_references(self, ref_str: str) -> List[Dict[str, str]]:
        """Parse reference string into structured references."""
        if not ref_str:
            return []
        
        ref_str = str(ref_str).strip()
        references = []
        
        # Split by common separators
        parts = re.split(r"[;,\n]", ref_str)
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            # RIC pattern: "RIC I 207" or "RIC I, 207" or "RPC I 1701a"
            ric_match = re.match(r"(RIC|RPC)\s+([IVX]+(?:\.[IVX]+)?)?\s*,?\s*(\d+(?:/\d+[a-z])?)", part, re.IGNORECASE)
            if ric_match:
                system = ric_match.group(1).lower()
                volume = ric_match.group(2) or ""
                number = ric_match.group(3)
                references.append({
                    "system": system,
                    "volume": volume,
                    "number": number,
                    "is_primary": len(references) == 0,
                })
                continue
            
            # Crawford pattern: "Crawford 335/1c"
            crawford_match = re.match(r"Crawford\s+(\d+(?:/\d+[a-z])?)", part, re.IGNORECASE)
            if crawford_match:
                references.append({
                    "system": "crawford",
                    "number": crawford_match.group(1),
                    "is_primary": len(references) == 0,
                })
                continue
            
            # Sydenham pattern: "Sydenham 611"
            sydenham_match = re.match(r"Sydenham\s+(\d+)", part, re.IGNORECASE)
            if sydenham_match:
                references.append({
                    "system": "sydenham",
                    "number": sydenham_match.group(1),
                    "is_primary": False,
                })
                continue
            
            # Default: treat as other
            references.append({
                "system": "other",
                "number": part,
                "is_primary": len(references) == 0,
            })
        
        return references
    
    def parse_ngc_grade(self, ngc_grade: str) -> Dict[str, Any]:
        """Parse NGC grade string."""
        if not ngc_grade:
            return {}
        
        result = {}
        ngc_str = str(ngc_grade).strip()
        
        # Extract grade (everything before "Strike:")
        if "Strike:" in ngc_str:
            grade_part = ngc_str.split("Strike:")[0].strip()
            result["grade"] = grade_part
        else:
            result["grade"] = ngc_str
        
        # Extract strike quality: "Strike: 5/5"
        strike_match = re.search(r"Strike:\s*(\d)/5", ngc_str)
        if strike_match:
            result["strike_quality"] = int(strike_match.group(1))
        
        # Extract surface quality: "Surface: 4/5"
        surface_match = re.search(r"Surface:\s*(\d)/5", ngc_str)
        if surface_match:
            result["surface_quality"] = int(surface_match.group(1))
        
        return result
    
    def parse_numeric(self, value: Any, field_name: str) -> Optional[float]:
        """Parse numeric value with error handling."""
        if value is None or value == "":
            return None
        
        try:
            if isinstance(value, (int, float)):
                return float(value)
            
            value_str = str(value).strip()
            # Remove common non-numeric characters
            value_str = re.sub(r"[^\d.]", "", value_str)
            
            if not value_str:
                return None
            
            return float(value_str)
        except (ValueError, TypeError) as e:
            self.warnings.append(f"{field_name}: Could not parse '{value}' as number")
            return None
    
    def convert_row(self, row: Dict[str, Any], row_num: int) -> Optional[Dict[str, Any]]:
        """Convert a single row to CoinStack format."""
        coin_data = {}
        
        # Required fields validation
        issuing_authority = str(row.get("Ruler Issuer", "")).strip()
        denomination = str(row.get("Coin type", "")).strip()
        
        if not issuing_authority or not denomination:
            self.stats["skipped"] += 1
            self.warnings.append(f"Row {row_num}: Missing required fields (Ruler Issuer or Coin type)")
            return None
        
        coin_data["issuing_authority"] = issuing_authority
        coin_data["denomination"] = denomination
        
        # Category
        category = self.normalize_category(row.get("Category", ""))
        if category:
            coin_data["category"] = category
        else:
            coin_data["category"] = "imperial"  # Default
        
        # Metal (required)
        metal = self.normalize_metal(row.get("Composition", ""))
        if metal:
            coin_data["metal"] = metal
        else:
            self.stats["skipped"] += 1
            self.warnings.append(f"Row {row_num}: Missing or invalid metal")
            return None
        
        # Storage location
        if row.get("Temp loc"):
            coin_data["storage_location"] = str(row.get("Temp loc")).strip()
        
        # Mint
        mint_name = row.get("Mint")
        if mint_name:
            coin_data["mint_name"] = str(mint_name).strip()
        
        # Script
        if row.get("Script"):
            coin_data["script"] = str(row.get("Script")).strip()
        
        # Portrait subject
        if row.get("Laureate"):
            coin_data["portrait_subject"] = str(row.get("Laureate")).strip()
        
        # Reign years
        if row.get("Ruled"):
            start, end = self.parse_reign_years(str(row.get("Ruled")))
            if start is not None:
                coin_data["reign_start"] = start
            if end is not None:
                coin_data["reign_end"] = end
        
        # Mint years
        if row.get("Minted"):
            start, end = self.parse_mint_years(str(row.get("Minted")))
            if start is not None:
                coin_data["mint_year_start"] = start
            if end is not None:
                coin_data["mint_year_end"] = end
        
        # Physical attributes
        weight = self.parse_numeric(row.get("Weight"), "Weight")
        if weight is not None:
            coin_data["weight_g"] = weight
        
        diameter = self.parse_numeric(row.get("Diameter"), "Diameter")
        if diameter is not None:
            coin_data["diameter_mm"] = diameter
        
        # Obverse
        if row.get("Obverse"):
            legend, description = self.parse_obverse_reverse(str(row.get("Obverse")))
            if legend:
                coin_data["obverse_legend"] = legend
            if description:
                coin_data["obverse_description"] = description
        
        # Reverse
        if row.get("Reverse"):
            legend, description = self.parse_obverse_reverse(str(row.get("Reverse")))
            if legend:
                coin_data["reverse_legend"] = legend
            if description:
                coin_data["reverse_description"] = description
        
        # References
        if row.get("Reference"):
            references = self.parse_references(str(row.get("Reference")))
            if references:
                coin_data["references"] = references
        
        # Grading
        if row.get("Condition"):
            coin_data["grade"] = str(row.get("Condition")).strip()
        
        # NGC Grade (more detailed)
        if row.get("NGC Grade"):
            ngc_data = self.parse_ngc_grade(str(row.get("NGC Grade")))
            if ngc_data.get("grade"):
                coin_data["grade"] = ngc_data["grade"]  # Override Condition with NGC Grade
            if "strike_quality" in ngc_data:
                coin_data["strike_quality"] = ngc_data["strike_quality"]
            if "surface_quality" in ngc_data:
                coin_data["surface_quality"] = ngc_data["surface_quality"]
        
        # Surface issues
        if row.get("NGC comment"):
            issues = str(row.get("NGC comment")).strip()
            if issues:
                coin_data["surface_issues"] = [issues]
        
        # Acquisition
        amount_paid = self.parse_numeric(row.get("Amount Paid"), "Amount Paid")
        if amount_paid is not None:
            coin_data["acquisition_price"] = amount_paid
        
        if row.get("Source"):
            coin_data["acquisition_source"] = str(row.get("Source")).strip()
        
        if row.get("Link"):
            coin_data["acquisition_url"] = str(row.get("Link")).strip()
        
        # Notes
        if row.get("Comment"):
            coin_data["personal_notes"] = str(row.get("Comment")).strip()
        
        if row.get("Pedigree"):
            coin_data["provenance_notes"] = str(row.get("Pedigree")).strip()
        
        if row.get("Fine style"):
            coin_data["style_notes"] = str(row.get("Fine style")).strip()
        
        self.stats["processed"] += 1
        return coin_data
    
    def process_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process Excel/CSV file and return converted data."""
        self.stats["total_rows"] = 0
        self.stats["processed"] = 0
        self.stats["skipped"] = 0
        self.errors = []
        self.warnings = []
        
        # Read file
        suffix = file_path.suffix.lower()
        if suffix in [".xlsx", ".xls"]:
            rows = self._read_excel(file_path)
        elif suffix == ".csv":
            rows = self._read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
        
        self.stats["total_rows"] = len(rows)
        
        # Convert rows
        converted_data = []
        for idx, row in enumerate(rows, start=2):  # Start at 2 (row 1 is header)
            try:
                coin_data = self.convert_row(row, idx)
                if coin_data:
                    converted_data.append(coin_data)
            except Exception as e:
                self.stats["errors"] += 1
                self.errors.append({
                    "row": idx,
                    "error": str(e),
                    "data": str(row),
                })
                logger.error(f"Error processing row {idx}: {e}")
        
        return converted_data
    
    def _read_excel(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read Excel file."""
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.active
        
        # Read headers
        headers = []
        for cell in sheet[1]:
            headers.append(str(cell.value).strip() if cell.value else "")
        
        # Read data rows
        rows = []
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if any(cell is not None for cell in row):
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers) and headers[i]:
                        row_dict[headers[i]] = value
                rows.append(row_dict)
        
        workbook.close()
        return rows
    
    def _read_csv(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read CSV file."""
        rows = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        return rows
    
    def get_report(self) -> Dict[str, Any]:
        """Get processing report."""
        return {
            "stats": self.stats.copy(),
            "errors": self.errors[:20],  # Limit to first 20
            "warnings": self.warnings[:50],  # Limit to first 50
        }


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Parse and convert coin collection data")
    parser.add_argument("input_file", type=Path, help="Input Excel or CSV file")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON file")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, don't convert")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON output")
    
    args = parser.parse_args()
    
    if not args.input_file.exists():
        print(f"Error: File not found: {args.input_file}")
        sys.exit(1)
    
    print(f"Processing: {args.input_file}")
    print("=" * 60)
    
    converter = DataConverter()
    
    try:
        converted_data = converter.process_file(args.input_file)
        
        # Print report
        report = converter.get_report()
        print(f"\nProcessing complete:")
        print(f"  Total rows: {report['stats']['total_rows']}")
        print(f"  Processed: {report['stats']['processed']}")
        print(f"  Skipped: {report['stats']['skipped']}")
        print(f"  Errors: {report['stats']['errors']}")
        print(f"  Warnings: {len(report['warnings'])}")
        
        if report['errors']:
            print(f"\nErrors (showing first {len(report['errors'])}):")
            for error in report['errors']:
                print(f"  Row {error['row']}: {error['error']}")
        
        if report['warnings']:
            print(f"\nWarnings (showing first {min(10, len(report['warnings']))}):")
            for warning in report['warnings'][:10]:
                print(f"  {warning}")
        
        if not args.validate_only:
            # Save output
            if args.output:
                output_data = {
                    "converted": converted_data,
                    "report": report,
                }
                with open(args.output, "w", encoding="utf-8") as f:
                    if args.pretty:
                        json.dump(output_data, f, indent=2, ensure_ascii=False)
                    else:
                        json.dump(output_data, f, ensure_ascii=False)
                print(f"\n✅ Converted data saved to: {args.output}")
            else:
                # Print sample
                print(f"\n✅ Converted {len(converted_data)} coins")
                if converted_data:
                    print("\nSample converted coin (first one):")
                    print(json.dumps(converted_data[0], indent=2, ensure_ascii=False, default=str))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
