"""Excel/CSV import service."""
from pathlib import Path
from typing import List, Dict, Any, Optional
import openpyxl
import csv
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Coin, Mint, CoinReference
from app.models.coin import Category, Metal
from app.models.reference import ReferenceSystem
import re
import logging

# Import parsing functions directly (avoid circular imports)
# The parse_collection.py script can be used standalone
# For import service, we use the existing functions below

logger = logging.getLogger(__name__)


class ImportError(Exception):
    """Import error."""
    pass


def detect_file_type(file_path: Path) -> str:
    """Detect if file is CSV or Excel."""
    suffix = file_path.suffix.lower()
    if suffix in [".xlsx", ".xls"]:
        return "excel"
    elif suffix == ".csv":
        return "csv"
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def read_excel_file(file_path: Path) -> List[Dict[str, Any]]:
    """Read Excel file and return list of dictionaries."""
    workbook = openpyxl.load_workbook(file_path, data_only=True)
    sheet = workbook.active
    
    # Read headers from first row
    headers = []
    for cell in sheet[1]:
        headers.append(str(cell.value).strip() if cell.value else "")
    
    # Read data rows
    rows = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if any(cell is not None for cell in row):  # Skip empty rows
            row_dict = {}
            for i, value in enumerate(row):
                if i < len(headers) and headers[i]:
                    row_dict[headers[i]] = value
            rows.append(row_dict)
    
    return rows


def read_csv_file(file_path: Path) -> List[Dict[str, Any]]:
    """Read CSV file and return list of dictionaries."""
    rows = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def parse_date(date_value: Any) -> Optional[datetime]:
    """Parse date from various formats."""
    if not date_value:
        return None
    
    if isinstance(date_value, datetime):
        return date_value.date()
    
    if isinstance(date_value, str):
        # Try common date formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(date_value.strip(), fmt).date()
            except ValueError:
                continue
    
    return None


def parse_reign_years(reign_str: str) -> tuple[Optional[int], Optional[int]]:
    """Parse reign years from string like '27 BC-AD 14' or 'AD 14-37'."""
    if not reign_str:
        return None, None
    
    reign_str = str(reign_str).strip()
    
    # Pattern: "27 BC-AD 14" or "AD 14-37" or "14-37"
    patterns = [
        r"(-?\d+)\s*BC\s*-\s*AD\s*(\d+)",  # "27 BC-AD 14"
        r"AD\s*(\d+)\s*-\s*(\d+)",  # "AD 14-37"
        r"(-?\d+)\s*-\s*(\d+)",  # "14-37" or "-27-14"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, reign_str)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            # Convert BC years to negative
            if "BC" in reign_str and start > 0:
                start = -start
            return start, end
    
    # Try single year
    year_match = re.search(r"(-?\d+)", reign_str)
    if year_match:
        year = int(year_match.group(1))
        return year, year
    
    return None, None


def parse_references(ref_str: str) -> List[Dict[str, str]]:
    """Parse reference string like 'RIC I 207' or 'Crawford 335/1c'."""
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
        
        # Try to match RIC pattern: "RIC I 207" or "RIC I, 207"
        ric_match = re.match(r"RIC\s+([IVX]+(?:\.[IVX]+)?)?\s*,?\s*(\d+(?:/\d+[a-z])?)", part, re.IGNORECASE)
        if ric_match:
            volume = ric_match.group(1) or ""
            number = ric_match.group(2)
            references.append({
                "system": "ric",
                "volume": volume,
                "number": number,
                "is_primary": len(references) == 0,
            })
            continue
        
        # Try Crawford pattern: "Crawford 335/1c"
        crawford_match = re.match(r"Crawford\s+(\d+(?:/\d+[a-z])?)", part, re.IGNORECASE)
        if crawford_match:
            references.append({
                "system": "crawford",
                "number": crawford_match.group(1),
                "is_primary": len(references) == 0,
            })
            continue
        
        # Try RPC pattern: "RPC 1234"
        rpc_match = re.match(r"RPC\s+(\d+)", part, re.IGNORECASE)
        if rpc_match:
            references.append({
                "system": "rpc",
                "number": rpc_match.group(1),
                "is_primary": len(references) == 0,
            })
            continue
        
        # Default: treat as other
        references.append({
            "system": "other",
            "number": part,
            "is_primary": len(references) == 0,
        })
    
    return references


# Column mapping from Excel to Coin model
COLUMN_MAPPING = {
    "Ruler Issuer": "issuing_authority",
    "Coin type": "denomination",
    "Category": "category",
    "Composition": "metal",  # Will parse "Silver", "Gold", etc.
    "Temp loc": "storage_location",
    "Reference": "references",
    "Amount Paid": "acquisition_price",
    "Weight": "weight_g",
    "Diameter": "diameter_mm",
    "Condition": "grade",  # Primary grade
    "NGC Grade": "ngc_grade",  # More detailed grade
    "Mint": "mint_name",
    "Ruled": "reign",  # Parse reign years
    "Minted": "minted",  # Parse mint years
    "Obverse": "obverse_full",  # Will split into legend/description
    "Reverse": "reverse_full",  # Will split into legend/description
    "Source": "acquisition_source",
    "Link": "acquisition_url",
    "Comment": "personal_notes",
    "NGC comment": "surface_issues",
    "Pedigree": "provenance_notes",
    "Fine style": "style_notes",
    "Script": "script",
    "Laureate": "portrait_subject",
}


def normalize_category(category: str) -> Optional[str]:
    """Normalize category string to enum value."""
    if not category:
        return None
    
    category_lower = str(category).lower()
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
    return "other"


def normalize_metal(metal: str) -> Optional[str]:
    """Normalize metal string to enum value."""
    if not metal:
        return None
    
    metal_lower = str(metal).lower()
    if "gold" in metal_lower:
        return "gold"
    elif "silver" in metal_lower:
        return "silver"
    elif "bronze" in metal_lower:
        return "bronze"
    elif "billon" in metal_lower:
        return "billon"
    elif "orichalcum" in metal_lower:
        return "orichalcum"
    elif "copper" in metal_lower:
        return "copper"
    return None


def parse_obverse_reverse(full_text: str) -> tuple[Optional[str], Optional[str]]:
    """Parse obverse/reverse text into legend and description.
    
    Looks for pattern: "LEGEND, description" or just "description"
    """
    if not full_text:
        return None, None
    
    full_text = str(full_text).strip()
    
    # Try to split on comma - first part might be legend
    if "," in full_text:
        parts = full_text.split(",", 1)
        legend = parts[0].strip()
        description = parts[1].strip()
        
        # If legend looks like a legend (all caps, abbreviations), use it
        if len(legend) < 50 and legend.isupper():
            return legend, description
        else:
            # Otherwise, it's all description
            return None, full_text
    
    return None, full_text


def parse_mint_years(minted_str: str) -> tuple[Optional[int], Optional[int]]:
    """Parse mint years from string like '2 BC-AD 4' or '96 BC'."""
    if not minted_str:
        return None, None
    
    return parse_reign_years(minted_str)  # Same logic


def parse_ngc_grade(ngc_grade: str) -> dict:
    """Parse NGC grade string like 'Choice AU  Strike: 5/5 Surface: 4/5'."""
    if not ngc_grade:
        return {}
    
    result = {}
    ngc_str = str(ngc_grade).strip()
    
    # Extract grade (first part before "Strike:")
    if "Strike:" in ngc_str:
        grade_part = ngc_str.split("Strike:")[0].strip()
        result["grade"] = grade_part
    else:
        result["grade"] = ngc_str
    
    # Extract strike quality
    strike_match = re.search(r"Strike:\s*(\d)/5", ngc_str)
    if strike_match:
        result["strike_quality"] = int(strike_match.group(1))
    
    # Extract surface quality
    surface_match = re.search(r"Surface:\s*(\d)/5", ngc_str)
    if surface_match:
        result["surface_quality"] = int(surface_match.group(1))
    
    return result


def map_row_to_coin_data(row: Dict[str, Any]) -> Dict[str, Any]:
    """Map Excel/CSV row to CoinCreate schema."""
    coin_data = {}
    
    for excel_col, model_field in COLUMN_MAPPING.items():
        if excel_col in row and row[excel_col] is not None:
            value = row[excel_col]
            
            # Skip empty values
            if value == "" or value is None:
                continue
            
            # Handle type conversions
            if model_field == "acquisition_price":
                try:
                    coin_data[model_field] = float(value) if value else None
                except (ValueError, TypeError):
                    pass
            elif model_field == "weight_g":
                try:
                    coin_data[model_field] = float(value) if value else None
                except (ValueError, TypeError):
                    pass
            elif model_field == "diameter_mm":
                try:
                    coin_data[model_field] = float(value) if value else None
                except (ValueError, TypeError):
                    pass
            elif model_field == "acquisition_date":
                coin_data[model_field] = parse_date(value)
            elif model_field == "references":
                coin_data[model_field] = parse_references(value)
            elif model_field == "category":
                coin_data[model_field] = normalize_category(value)
            elif model_field == "metal":
                coin_data[model_field] = normalize_metal(value)
            elif model_field == "reign":
                start, end = parse_reign_years(value)
                if start is not None:
                    coin_data["reign_start"] = start
                if end is not None:
                    coin_data["reign_end"] = end
            elif model_field == "minted":
                start, end = parse_mint_years(value)
                if start is not None:
                    coin_data["mint_year_start"] = start
                if end is not None:
                    coin_data["mint_year_end"] = end
            elif model_field == "obverse_full":
                legend, description = parse_obverse_reverse(value)
                if legend:
                    coin_data["obverse_legend"] = legend
                if description:
                    coin_data["obverse_description"] = description
            elif model_field == "reverse_full":
                legend, description = parse_obverse_reverse(value)
                if legend:
                    coin_data["reverse_legend"] = legend
                if description:
                    coin_data["reverse_description"] = description
            elif model_field == "ngc_grade":
                ngc_data = parse_ngc_grade(value)
                coin_data.update(ngc_data)
            elif model_field == "surface_issues":
                # Store as list or JSON string
                if value:
                    coin_data[model_field] = [str(value).strip()]
            else:
                coin_data[model_field] = str(value).strip() if value else None
    
    return coin_data


def get_or_create_mint(db: Session, mint_name: str) -> Optional[Mint]:
    """Get or create mint."""
    if not mint_name:
        return None
    
    mint = db.query(Mint).filter(Mint.name == mint_name).first()
    if not mint:
        mint = Mint(name=mint_name)
        db.add(mint)
        db.flush()
    
    return mint


class ImportResult:
    """Import result."""
    
    def __init__(self):
        self.imported = 0
        self.updated = 0
        self.skipped = 0
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[str] = []
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "imported": self.imported,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
            "warnings": self.warnings,
        }


async def import_collection_file(
    db: Session,
    file_path: Path,
    dry_run: bool = False,
) -> ImportResult:
    """Import collection from CSV or Excel file with robust parsing."""
    result = ImportResult()
    
    try:
        file_type = detect_file_type(file_path)
        
        if file_type == "excel":
            rows = read_excel_file(file_path)
        else:
            rows = read_csv_file(file_path)
        
        logger.info(f"Found {len(rows)} rows in {file_path.name}")
        
        for idx, row in enumerate(rows, start=2):  # Start at 2 (row 1 is header)
            try:
                coin_data = map_row_to_coin_data(row)
                
                # Validate required fields
                if not coin_data.get("issuing_authority") or not coin_data.get("denomination"):
                    result.skipped += 1
                    result.warnings.append(f"Row {idx}: Missing required fields")
                    continue
                
                if not coin_data.get("category"):
                    coin_data["category"] = "imperial"  # Default
                
                if not coin_data.get("metal"):
                    result.skipped += 1
                    result.warnings.append(f"Row {idx}: Missing metal")
                    continue
                
                # Convert to enums
                try:
                    coin_data["category"] = Category(coin_data["category"])
                except ValueError:
                    coin_data["category"] = Category.IMPERIAL
                
                try:
                    coin_data["metal"] = Metal(coin_data["metal"])
                except ValueError:
                    result.skipped += 1
                    result.warnings.append(f"Row {idx}: Invalid metal '{coin_data.get('metal')}'")
                    continue
                
                # Handle mint
                mint = None
                if "mint_name" in coin_data:
                    mint = get_or_create_mint(db, coin_data.pop("mint_name"))
                
                # Handle references
                references_data = coin_data.pop("references", [])
                
                if not dry_run:
                    # Create coin
                    coin = Coin(**coin_data)
                    if mint:
                        coin.mint = mint
                    
                    db.add(coin)
                    db.flush()
                    
                    # Add references
                    for ref_data in references_data:
                        try:
                            ref = CoinReference(
                                coin_id=coin.id,
                                system=ReferenceSystem(ref_data["system"]),
                                volume=ref_data.get("volume"),
                                number=ref_data["number"],
                                is_primary=ref_data.get("is_primary", False),
                            )
                            db.add(ref)
                        except ValueError as e:
                            logger.warning(f"Invalid reference system '{ref_data.get('system')}': {e}")
                    
                    db.commit()
                    result.imported += 1
                else:
                    result.imported += 1
                    result.warnings.append(f"Row {idx}: Dry run - not imported")
            
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error importing row {idx}: {error_msg}", exc_info=True)
                result.errors.append({
                    "row": idx,
                    "error": error_msg,
                    "data": str(row.get("Ruler Issuer", "Unknown")),
                })
                result.skipped += 1
        
        if not dry_run:
            db.commit()
        
        logger.info(f"Import complete: {result.imported} imported, {result.skipped} skipped")
        
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        result.errors.append({
            "row": 0,
            "error": str(e),
        })
        if not dry_run:
            db.rollback()
    
    return result
